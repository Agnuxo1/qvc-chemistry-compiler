"""Merge groups k at a time (exact), then shrink bases and copies gradually with float64 L-BFGS refits.

    python notebooks/dfthc-refit/experiments/shrink.py SEED.npz OUTDIR --merge 3 \
        170x84,160x78,150x70,143x62,143x56,143x50,143x46 [--pre 2500] [--fade 300] [--fit 1200] [--save 143x46]

The (26, 60, 30) groups merged in threes give (9, 180, 90) with no loss, and no group is ever
dropped: dropping a whole merged group costs ~1 Ha before the refit and 2,500 L-BFGS iterations
only bring 13.9 back to 19.3 mHa. Each step here fades each group's weakest bases (sum_c w_bc^2)
and weakest copies (||sum_b w_bc u_b u_b^T||_F) at x0.5, then x0.2 while the rest refit, removes
them and refits. Steps named in --save get a longer refit (--final) and write OUTDIR/{R}x{B}x{C}.npz.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import FCIDUMP, SHIFTS, UPPER_ENERGY  # noqa: E402
import fastfit  # noqa: E402
import structure  # noqa: E402

import jax  # noqa: E402

jax.config.update('jax_enable_x64', True)
jax.config.update('jax_default_matmul_precision', 'highest')
import jax.numpy as jnp  # noqa: E402
from dfthc import df_thc_sga  # noqa: E402

df_thc_sga.dtype = jnp.float64
from dfthc.train_df_thc_sga import Initialize  # noqa: E402
from scipy.optimize import minimize  # noqa: E402


def impacts(U: np.ndarray, w: np.ndarray, prob) -> tuple[np.ndarray, np.ndarray]:
    """Exact error_2^2 increase from removing each copy (R, C) and each basis vector (R, B) alone.

    In packed pair space (fastfit) the residual is H = A^T A - T with A's rows a_rc, and the norm
    weights M = m m^T. Removing copy (r, c): H - a a^T, so the change is (sum m a^2)^2 - 2 a~^T H a~
    (a~ = m a). Removing basis vector (r, b) shifts group r's rows by w_rbc pi_rb (pi = its pair
    vector): H + D, D = -(u pi^T + pi u^T) + beta pi pi^T with u = sum_c w_rbc a_rc, beta = |w_rb|^2.
    """
    T, M, i, j = (np.asarray(x) for x in prob)
    m = np.sqrt(np.diag(M))
    u = U / np.linalg.norm(U, axis=2, keepdims=True)
    pi = u[:, :, i] * u[:, :, j]                                  # (R, B, P)
    A = np.einsum('rbc,rbp->rcp', w, pi)                          # (R, C, P)
    H = np.einsum('rcp,rcq->pq', A, A) - T
    At = A * m
    copies = np.einsum('rcp,rcp->rc', At, At @ H) * -2 + np.einsum('rcp->rc', A * A * m) ** 2
    ut = np.einsum('rbc,rcp->rbp', w, A) * m                      # u~ per basis vector
    pt = pi * m
    Hp = pt @ H
    beta = np.sum(w ** 2, axis=2)
    inner = -2 * np.sum(ut * Hp, axis=2) + beta * np.sum(pt * Hp, axis=2)
    us, ps = ut / np.sqrt(m), pt / np.sqrt(m)                     # |D|_M^2 weighs entries by sqrt(m_p m_q)
    up, pp, uu = np.sum(us * ps, axis=2), np.sum(ps * ps, axis=2), np.sum(us * us, axis=2)
    bases = 2 * inner + 2 * uu * pp + 2 * up ** 2 + beta ** 2 * pp ** 2 - 4 * beta * up * pp
    return copies, bases


def split(U: np.ndarray, w: np.ndarray, B: int, C: int, prob=None):
    """Kept (U, w) and the faded parts: bases beyond B (Ub, wb over kept copies) and copies beyond C.

    With `prob` (fastfit.problem), copies and bases are ranked by the exact error increase of
    removing each alone (`impacts`); otherwise by their norms."""
    u = U / np.linalg.norm(U, axis=2, keepdims=True)
    gram = np.einsum('rbp,rdp->rbd', u, u) ** 2
    if prob is not None and C < w.shape[2]:
        cop = np.argsort(impacts(U, w, prob)[0], axis=1)[:, ::-1]
    else:
        cop = np.argsort(-np.einsum('rbc,rbd,rdc->rc', w, gram, w), axis=1)
    w = np.take_along_axis(w, cop[:, None, :], axis=2)
    wc = w[:, :, C:]                       # copies to fade, over all current bases
    w = w[:, :, :C]
    if prob is not None and B < w.shape[1]:
        bas = np.argsort(impacts(U, w, prob)[1], axis=1)[:, ::-1]
    else:
        bas = np.argsort(-np.sum(w ** 2, axis=2), axis=1)
    U = np.take_along_axis(U, bas[:, :, None], axis=1)
    w = np.take_along_axis(w, bas[:, :, None], axis=1)
    wc = np.take_along_axis(wc, bas[:, :, None], axis=1)
    return U[:, :B], w[:, :B], U[:, B:], w[:, B:], wc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('seed', type=Path)
    ap.add_argument('outdir', type=Path)
    ap.add_argument('schedule', help='comma-separated BxC steps after the merge')
    ap.add_argument('--merge', type=int, default=3)
    ap.add_argument('--pre', type=int, default=2500)
    ap.add_argument('--fade', type=int, default=300)
    ap.add_argument('--fit', type=int, default=1200)
    ap.add_argument('--final', type=int, default=4000)
    ap.add_argument('--save', default='')
    ap.add_argument('--kappa', type=float, default=5e-5)
    ap.add_argument('--merged', action='store_true', help='SEED is already merged (e.g. an earlier OUTDIR file)')
    ap.add_argument('--seed-fit', type=int, default=0,
                    help='fit SEED this many iterations before merging (a random seed: our own small groups), '
                         'saved as OUTDIR/seed_fit.npz')
    ap.add_argument('--f32', action='store_true', help='float32 objective (T4 GPUs are slow in float64)')
    ap.add_argument('--select', choices=('norm', 'impact'), default='norm',
                    help='which bases and copies to cut: smallest norm, or smallest exact error increase')
    ap.add_argument('--device', action='store_true',
                    help='packed-pair objective and on-device optax L-BFGS (fastfit.py); for GPUs')
    a = ap.parse_args()
    DT = jnp.float32 if a.f32 else jnp.float64
    df_thc_sga.dtype = DT
    a.outdir.mkdir(parents=True, exist_ok=True)
    save = set(a.save.split(',')) if a.save else set()

    ref = Initialize(str(FCIDUMP), UPPER_ENERGY)
    ref = {k: (jnp.asarray(v, DT) if hasattr(v, 'dtype') and jnp.issubdtype(v.dtype, jnp.floating) else v)
           for k, v in ref.items()}
    with np.load(SHIFTS) as z:
        frozen = {k: jnp.asarray(z[k], DT) for k in ('Hsym_lower', 'H1_I')}

    prob = fastfit.problem(ref, frozen, DT) if a.device else None
    sel = fastfit.problem(ref, frozen, jnp.float64) if a.select == 'impact' else None

    def objective(U, w):
        if a.device:
            eps = fastfit.error2(U, w, prob)
        else:
            resid = df_thc_sga.Compute_H2_residual_after_symmetry_shift(frozen, ref, df_thc_sga.Compute_H2_sqrt(U, w))
            eps = df_thc_sga.Compute_H2_norm(resid, ref['tril_diag'])
        D = 0.5 * jnp.sum(jnp.sum(jnp.abs(w), axis=1) ** 2 - jnp.sum(w, axis=1) ** 2)
        return eps + a.kappa * D, (eps, D)

    def assemble(U, w, Ub, wb, wc, s):
        """Full (U, w): kept bases then faded bases; kept copies then faded copies (faded parts scaled by s)."""
        Uf = jnp.concatenate([U, Ub], axis=1)
        top = jnp.concatenate([w, s * wb], axis=1)                 # (R, B + nb, C)
        wf = jnp.concatenate([top, s * wc], axis=2)                # wc spans all B + nb bases
        return Uf, wf

    vg = jax.jit(jax.value_and_grad(lambda U, w, Ub, wb, wc, s: objective(*assemble(U, w, Ub, wb, wc, s)),
                                    argnums=(0, 1), has_aux=True))
    t0 = time.time()

    def fit(U, w, iters: int, label: str, Ub, wb, wc, s: float):
        n = U.size
        Ub, wb, wc, s = jnp.asarray(Ub, DT), jnp.asarray(wb, DT), jnp.asarray(wc, DT), DT(s)

        def fun(x):
            (v, _), (gU, gw) = vg(jnp.asarray(x[:n].reshape(U.shape), DT), jnp.asarray(x[n:].reshape(w.shape), DT),
                                  Ub, wb, wc, s)
            return float(v), np.concatenate([np.asarray(gU, np.float64).ravel(), np.asarray(gw, np.float64).ravel()])

        (_, (e0, _)), _ = vg(jnp.asarray(U, DT), jnp.asarray(w, DT), Ub, wb, wc, s)
        if iters > 0 and a.device:
            f = lambda p: objective(*assemble(p[0], p[1], Ub, wb, wc, s))[0]  # noqa: E731
            U, w = (np.asarray(x, np.float64) for x in
                    fastfit.lbfgs(f, (jnp.asarray(U, DT), jnp.asarray(w, DT)), iters, chunk=min(200, iters)))
        elif iters > 0:
            res = minimize(fun, np.concatenate([U.ravel(), w.ravel()]), jac=True, method='L-BFGS-B',
                           options={'maxiter': iters, 'maxfun': 2 * iters, 'maxcor': 30, 'ftol': 1e-15, 'gtol': 1e-12})
            U, w = res.x[:n].reshape(U.shape), res.x[n:].reshape(w.shape)
        (_, (eps, D)), _ = vg(jnp.asarray(U, DT), jnp.asarray(w, DT), Ub, wb, wc, s)
        print(f'{label:>16}: error_2 {1e3 * float(e0):8.3f} -> {1e3 * float(eps):8.3f} mHa  D {float(D):7.2f}  '
              f'({time.time() - t0:.0f} s)', flush=True)
        return U, w

    with np.load(a.seed) as z:
        p = {k: np.asarray(z[k], np.float64) for k in z.files}
    if not a.merged:
        if a.seed_fit > 0:
            U, w = p['U'], p['W']
            print(f'seed {w.shape}', flush=True)
            U, w = fit(U, w, a.seed_fit, f'seed {U.shape[0]}x{w.shape[1]}x{w.shape[2]}',
                       *split(U, w, w.shape[1], w.shape[2])[2:], 0.0)
            p = {**p, 'U': U, 'W': w, 'H2_I': w.sum(axis=1)}
            np.savez(a.outdir / 'seed_fit.npz', **p)
        p = structure.merge(p, a.merge, a.merge * p['W'].shape[2])
    U, w = p['U'], p['W']
    R = U.shape[0]
    print(f'start {w.shape}', flush=True)
    U, w = fit(U, w, a.pre, f'{R}x{w.shape[1]}x{w.shape[2]}', *split(U, w, w.shape[1], w.shape[2])[2:], 0.0)
    np.savez(a.outdir / f'{R}x{w.shape[1]}x{w.shape[2]}.npz', U=U, W=w, H2_I=w.sum(axis=1))
    for step in filter(None, a.schedule.split(',')):   # an empty schedule: the pre-fit only
        B, C = (int(v) for v in step.split('x'))
        U, w, Ub, wb, wc = split(U, w, B, C, sel)
        for s in (0.5, 0.2):
            U, w = fit(U, w, a.fade, f'{step} x{s}', Ub, wb, wc, s)
        none = split(U, w, B, C)[2:]
        U, w = fit(U, w, a.final if step in save else a.fit, f'{R}x{step}', *none, 0.0)
        np.savez(a.outdir / (f'{R}x{step}.npz' if step in save else 'last.npz'),
                 U=U, W=w, H2_I=w.sum(axis=1))


if __name__ == '__main__':
    main()
