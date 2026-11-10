"""Round a DF-THC structure's two-body Givens angles to brot-bit words, progressively.

Plain rounding of the angles adds ~3.5 mHa to error_2 at 10 bits, more than the margin a
compressed factorization has. Instead the angles are rounded in stages (the idea of the
group-compression notebook, ahmedberatozer, reimplemented here in JAX):

1. Angles are taken in the **signed gauge** theta/pi in [-1/2, 1/2): at each Givens edge the
   parent amplitude keeps its sign, so cos(theta) >= 0. The tree then reproduces each vector up
   to a global sign, which `u u^T` does not see, and a 10-bit word's bit 9 equals bit 8.
2. Each stage freezes the not-yet-frozen angles whose rounding should hurt most: the diagonal
   Gauss-Newton curvature of the weighted two-body residual (estimated with random probe
   matrices, E[(d<e, v>/d theta)^2] = sum (de/d theta)^2) times the squared rounding offset.
3. The free angles and the weights w are then refit on epsilon_fro + kappa * D(w) (Adam), so
   they absorb the error of what was frozen. A last stage refits only w. With --lbfgs-until, the
   early stages refit by L-BFGS instead (michaelrustad's hybrid quantization; use --x64 on CPU).

    python notebooks/dfthc-refit/quantize.py STRUCTURE.npz OUT.npz [--brot 10]

OUT.npz holds the two-body `words` (R*B, N-1) and the refit weights `w` (R, B, C).

This copy of quantize.py takes `--codes`, Reed-Muller codes on any bit of any batch (rmcode.py), in place of
--coded and --coded2, and leaves a block's codeword open until its frozen angles pin it down, where quantize.py
locks a block's pattern at its first frozen angle. Bits above bit 0 wait for --lock-at: at that frozen fraction the
angles go through the exact gauge pass (rmcode.gauge_angles), the cheapest codewords are chosen, and they stay. Earlier
the entries are free to drift, which would break a relation at every stage; later nothing strong is left free to
absorb the flips (with 27% of the angles left, all weak, one run went from 18.1 to 26.8 mHa).

With --open the whole table goes through the gauge pass before the first stage, with the wrap half a step early, and no
codeword ever locks: each stage takes the cheapest words that agree with what is frozen, on every coded bit, as bit 0
does. Once a block's words lock, its free angles sit on a lattice of up to 16 steps that no longer follows them.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
import rmcode  # noqa: E402
from paths import FCIDUMP, SHIFTS, UPPER_ENERGY  # noqa: E402  (puts the starter kit on sys.path)
import encode  # noqa: E402
import fastfit  # noqa: E402
import onebody  # noqa: E402
from encode import signed_angles  # noqa: E402,F401  (re-exported for adaround.py)

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import optax  # noqa: E402
from dfthc import df_thc_sga  # noqa: E402
from dfthc.train_df_thc_sga import Initialize  # noqa: E402

jax.config.update('jax_default_matmul_precision', 'highest')

# Fraction of angles still free after each stage.
FREE = (0.7, 0.5, 0.35, 0.25, 0.17, 0.11, 0.07, 0.045, 0.03, 0.02, 0.012, 0.006, 0.0)




def levels(edges: np.ndarray) -> list[np.ndarray]:
    """Split the ordered edges into runs that touch disjoint orbitals (7 for the log-depth tree)."""
    runs, current, used = [], [], set()
    for t, (p, q) in enumerate(edges):
        if p in used or q in used:
            runs.append(np.array(current))
            current, used = [], set()
        current.append(t)
        used.update((int(p), int(q)))
    return runs + [np.array(current)]


def decode(theta, edges: np.ndarray, n: int):
    """The verifier's Givens tree (reconstruct_u_vectors) in JAX: rows of theta/pi -> vectors.

    Edges within a level act on disjoint orbitals, so each level is one vectorized update.
    """
    c, s = jnp.cos(jnp.pi * theta), jnp.sin(jnp.pi * theta)
    u = jnp.zeros((theta.shape[0], n), theta.dtype).at[:, 0].set(1.0)
    for ts in levels(edges):
        p, q = edges[ts, 0], edges[ts, 1]
        up, uq = u[:, p], u[:, q]
        u = u.at[:, p].set(c[:, ts] * up - s[:, ts] * uq).at[:, q].set(s[:, ts] * up + c[:, ts] * uq)
    return u


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('structure', type=Path, help='npz with U (R, B, N) and W (R, B, C)')
    ap.add_argument('out', type=Path)
    ap.add_argument('--brot', type=int, default=10)
    ap.add_argument('--stage-steps', type=int, default=1500)
    ap.add_argument('--final-steps', type=int, default=4000)
    ap.add_argument('--probes', type=int, default=8)
    ap.add_argument('--lr-theta', type=float, default=1e-3)
    ap.add_argument('--lr-w', type=float, default=3e-4)
    ap.add_argument('--kappa', type=float, default=2e-5)
    ap.add_argument('--free', type=str, help='comma-separated fractions of angles still free after each stage '
                    '(default: FREE); a leading 1.0 is a continuous refit before any rounding')
    ap.add_argument('--fit-steps', type=int, default=6000, help='Adam steps of a stage that freezes nothing')
    ap.add_argument('--smart', action='store_true',
                    help='round each frozen angle up or down by the second-order change, not to nearest')
    ap.add_argument('--lbfgs-until', type=float, default=0.0,
                    help='refit stages with L-BFGS instead of Adam while at most this fraction is frozen '
                         '(michaelrustad: long L-BFGS over the first 10%% recovers what short Adam refits never do)')
    ap.add_argument('--lbfgs-iters', type=int, default=1500)
    ap.add_argument('--lbfgs-host', action='store_true',
                    help="SciPy's L-BFGS-B on the host (the original; ~9 it/s on an A100) instead of optax's on the device")
    ap.add_argument('--x64', action='store_true', help='float64 throughout (with --lbfgs-until, on CPU)')
    ap.add_argument('--codes', type=str, help="per-block Reed-Muller codes, 'bit:degree:first-last,...' over five-word "
                    "batches, e.g. '0:1:3-14,1:2:3-14' (rmcode.py). Bits above bit 0 keep every angle in the signed gauge "
                    'during the rounding, since the gauge fix at the end would negate words, which flips higher bits')
    ap.add_argument('--lock-at', type=float, default=0.4, help='frozen fraction at which the codes above bit 0 are chosen')
    ap.add_argument('--open', action='store_true', help='signed gauge from the first stage, and no codeword ever locks')
    a = ap.parse_args()
    if a.x64:
        jax.config.update('jax_enable_x64', True)
        df_thc_sga.dtype = jnp.float64

    ref = Initialize(str(FCIDUMP), UPPER_ENERGY)
    if a.x64:
        ref = {k: (jnp.asarray(v, jnp.float64) if hasattr(v, 'dtype') and jnp.issubdtype(v.dtype, jnp.floating)
                   else v) for k, v in ref.items()}
    with np.load(SHIFTS) as z:
        frozen_shift = {k: jnp.asarray(z[k], dtype=df_thc_sga.dtype) for k in ('Hsym_lower', 'H1_I')}
    with np.load(a.structure) as z:
        U, w0 = np.asarray(z['U'], np.float64), np.asarray(z['W'], np.float64)
    R, B, N = U.shape
    edges = encode.log_depth_tree(N)
    scale = float(1 << (a.brot - 1))
    # Angles are not clipped to the signed range: theta and theta + 1 give the same projector, and
    # a few % sit in (1/2 - 1/scale, 1/2), where clipping costs up to twice a rounding step. Each
    # row's words are moved into the signed gauge exactly at the end (onebody.signed_gauge).
    f32 = lambda x: jnp.asarray(x, dtype=df_thc_sga.dtype)  # noqa: E731

    theta0 = signed_angles(U.reshape(-1, N), edges)
    back = np.asarray(decode(jnp.asarray(theta0), edges, N))
    unit = U.reshape(-1, N) / np.linalg.norm(U.reshape(-1, N), axis=1, keepdims=True)
    drift = np.max(np.abs(np.abs(np.sum(back * unit, axis=1)) - 1.0))
    assert drift < 1e-5, f'signed gauge does not reproduce the vectors (|overlap| - 1 = {drift})'

    m = np.where(np.asarray(ref['tril'][0]) == np.asarray(ref['tril'][1]), 1.0, 2.0)
    sqrt_mm = f32(np.sqrt(np.outer(m, m)))  # Compute_H2_norm's multiplicities, as a weight on entries

    def residual(theta, w):
        """Multiplicity-weighted packed residual: its Frobenius norm is epsilon_fro."""
        u = decode(theta, edges, N).reshape(R, B, N)
        H2_sqrt = df_thc_sga.Compute_H2_sqrt(u, w)
        return sqrt_mm * df_thc_sga.Compute_H2_residual_after_symmetry_shift(frozen_shift, ref, H2_sqrt)

    def d_penalty(w):
        return 0.5 * jnp.sum(jnp.sum(jnp.abs(w), axis=1) ** 2 - jnp.sum(w, axis=1) ** 2)

    def cost(theta, w):
        eps = jnp.sqrt(jnp.sum(residual(theta, w) ** 2))
        return eps + a.kappa * d_penalty(w), eps

    qround = lambda t: np.round(t * scale) / scale  # noqa: E731
    reserved = None                                      # entries kept for last (rmcode.slack), set at the first freeze

    # Coded bits: words are the rows N.. of the table, so row i has address N + i; block a // 16, position a % 16.
    deg = rmcode.parse(a.codes, N - 1, a.brot)
    ccols = np.flatnonzero(deg.any(axis=1))
    # With a coded bit above bit 0 the words must end in the signed gauge without the gauge fix below, which negates
    # words and so changes those bits. Angles stay free until --lock-at (rmcode.gauge_angles); the signed range
    # [-1/2, 1/2 - 1/scale] is clipped from then on, when the strong entries at its edge have frozen.
    # --open: the range is half a step wider at the bottom and narrower at the top, which still rounds into the signed range
    # and has no wall: 2.5% of the angles of a compact table sit within a step of +1/2, and clipping them is as bad as rounding
    # the whole table (12.4 -> 188 mHa), while the same angles wrapped half a step early are the same vectors.
    early = 0.5 / scale if a.open else 0.0
    g_lo, g_hi = -0.5 - early, 0.5 - early - (1e-9 if a.open else 1.0 / scale)
    gauged = bool(deg[:, 1:].any())
    clipping = gauged and a.open
    gauge = lambda t: jnp.clip(t, g_lo, g_hi) if clipping else t  # noqa: E731
    addr = N + np.arange(R * B)
    blk, pos = addr // 16, addr % 16

    low = deg.copy()
    low[:, 1:] = 0                                       # the codes that survive the gauge pass: bit 0 only
    locked = None                                        # (residues, moduli) of the coded columns, from --lock-at on

    def coded_round(theta_now, c):
        """Rounded words for every angle: nearest, except coded columns follow their block's codewords, chosen to
        minimize the curvature-weighted squared rounding offset among those that agree with the frozen angles."""
        nonlocal locked
        q = qround(theta_now)
        if len(ccols) == 0:
            return q
        t = theta_now[:, ccols] * scale
        if locked is None:
            r, m = rmcode.residues(t, c[:, ccols], blk, pos, (deg if clipping or not gauged else low)[ccols], frozen[:, ccols],
                                   np.round(qvals[:, ccols] * scale).astype(np.int64), scale if clipping else None)
            if clipping and not a.open:
                locked = r, m
        else:
            r, m = locked
        v = rmcode.residue_round(t, r, m)
        q[:, ccols] = (rmcode.into_gauge(v, m, scale) if clipping else v) / scale
        return q

    @jax.jit
    def curvature(theta, w, key):
        """Estimate diag(J^T J) of the weighted residual w.r.t. theta with random probes."""
        _, vjp = jax.vjp(lambda th: residual(th, w), theta)

        def one(k):
            v = jax.random.normal(k, sqrt_mm.shape, dtype=df_thc_sga.dtype)
            return vjp(v)[0] ** 2
        return jnp.mean(jax.vmap(one)(jax.random.split(key, a.probes)), axis=0)

    half_sq = jax.jit(jax.grad(lambda th, w: 0.5 * jnp.sum(residual(th, w) ** 2)))  # J^T e

    def choose(theta_now, w, key):
        """Per-angle rounding and its estimated harm. With --smart, pick floor or ceil to minimize
        the second-order change of |e|^2, 2 g d + c d^2 (g = J^T e, c ~ diag J^T J); else nearest."""
        nonlocal reserved
        c = np.asarray(curvature(f32(theta_now), w, key), np.float64)
        if reserved is None:
            reserved = np.zeros(theta_now.shape, bool)
            if len(ccols) and not a.open:
                reserved[:, ccols] = rmcode.slack(c[:, ccols], blk, pos, deg[ccols])
        if not a.smart or len(ccols):
            q = coded_round(theta_now, c)
            return q, c * (q - theta) ** 2
        g = np.asarray(half_sq(f32(theta_now), w), np.float64)
        lo_q, hi_q = np.floor(theta * scale) / scale, np.ceil(theta * scale) / scale
        harm = [2 * g * (q - theta) + c * (q - theta) ** 2 for q in (lo_q, hi_q)]
        q = np.where(harm[0] <= harm[1], lo_q, hi_q)
        return q, np.minimum(harm[0], harm[1])

    def lbfgs_stage(theta, w, fmask, fq):
        """Refit the free angles and w by L-BFGS (frozen angles get zero gradient through the mask): optax's
        L-BFGS on the device (fastfit.lbfgs, jitted chunks, no host round trips), or with --lbfgs-host SciPy's
        L-BFGS-B driving the device objective from the host (the original; ~9 it/s on an A100, 4 on this CPU)."""
        vg = jax.jit(jax.value_and_grad(
            lambda th, ww: cost(fmask * fq + (1.0 - fmask) * th, ww), argnums=(0, 1), has_aux=True))
        (_, start), _ = vg(f32(theta), f32(w))
        if a.lbfgs_host:
            from scipy.optimize import minimize
            n = theta.size
            shape_w = tuple(w.shape)

            def fun(x):
                (v, _), (gt, gw) = vg(f32(x[:n].reshape(theta.shape)), f32(x[n:].reshape(shape_w)))
                return float(v), np.concatenate([np.asarray(gt, np.float64).ravel(), np.asarray(gw, np.float64).ravel()])

            res = minimize(fun, np.concatenate([np.asarray(theta, np.float64).ravel(), np.asarray(w, np.float64).ravel()]),
                           jac=True, method='L-BFGS-B', options={'maxiter': a.lbfgs_iters, 'maxfun': 2 * a.lbfgs_iters,
                                                                 'maxcor': 30, 'ftol': 1e-15, 'gtol': 1e-12})
            theta, w = np.asarray(gauge(res.x[:n].reshape(theta.shape)), np.float64), f32(res.x[n:].reshape(shape_w))
        else:
            th, w = fastfit.lbfgs(lambda p: cost(fmask * fq + (1.0 - fmask) * gauge(p[0]), p[1])[0],
                                  (f32(theta), f32(w)), a.lbfgs_iters)
            theta = np.asarray(gauge(th), np.float64)
        (_, eps), _ = vg(f32(theta), w)
        return theta, w, float(start), float(eps)

    if clipping:
        theta0 = rmcode.gauge_angles(theta0, edges, early)
    theta, w = np.asarray(gauge(theta0.copy()), np.float64), f32(w0)
    frozen = np.zeros(theta.shape, dtype=bool)
    qvals = np.zeros_like(theta)
    key = jax.random.key(0)
    t0 = time.time()
    schedule = tuple(float(x) for x in a.free.split(',')) if a.free else FREE
    for stage, free in enumerate(schedule + (None,)):
        if free is not None:
            need = int(round((1.0 - free) * theta.size)) - int(frozen.sum())
            if need > 0:
                key, sub = jax.random.split(key)
                if gauged and not clipping and frozen.mean() >= a.lock_at:
                    fixed = rmcode.gauge_angles(np.where(frozen, qvals, theta), edges)
                    theta, qvals, clipping = np.clip(fixed, g_lo, g_hi), np.where(frozen, fixed, qvals), True
                    reserved[:] = False
                q, impact = choose(np.where(frozen, qvals, theta), w, sub)
                impact = rmcode.last(impact, reserved)
                impact[frozen] = -np.inf
                pick = np.argsort(-impact, axis=None)[:need]
                frozen.flat[pick] = True
                qvals.flat[pick] = q.flat[pick]
        steps = a.final_steps if free is None else a.fit_steps if free >= 1.0 else a.stage_steps
        fmask, fq = f32(frozen), f32(qvals)
        train_theta = not frozen.all()
        if free is not None and frozen.mean() <= a.lbfgs_until:
            theta, w, start, eps = lbfgs_stage(theta, w, fmask, fq)
            print(f'stage {stage:2d}: frozen {frozen.mean():.4f}  error_2 {1e3 * start:7.3f} -> {1e3 * eps:7.3f} mHa  '
                  f'D {float(d_penalty(w)):7.2f}  L-BFGS ({time.time() - t0:.0f} s)', flush=True)
            continue
        sched = lambda lr: optax.exponential_decay(lr, max(steps, 1), 0.2)  # noqa: E731
        opt = optax.multi_transform({'theta': optax.adam(sched(a.lr_theta)) if train_theta else optax.set_to_zero(),
                                     'w': optax.adam(sched(a.lr_w))}, {'theta': 'theta', 'w': 'w'})
        params = {'theta': f32(theta), 'w': w}
        state = opt.init(params)

        @jax.jit
        def step(params, state):
            def loss(pp):
                th = fmask * fq + (1.0 - fmask) * pp['theta']
                return cost(th, pp['w'])
            (value, eps), g = jax.value_and_grad(loss, has_aux=True)(params)
            upd, state = opt.update(g, state, params)
            params = optax.apply_updates(params, upd)
            params = {'theta': gauge(params['theta']), 'w': params['w']}
            return params, state, value, eps

        best = (np.inf, params, np.nan)
        for i in range(steps + 1):
            new, state_new, value, eps = step(params, state)
            if i == 0:
                start = float(eps)  # right after this stage's freeze, before any refit
            if float(value) < best[0]:
                best = (float(value), params, float(eps))  # value and eps are those of `params`
            if i == steps:
                break
            params, state = new, state_new
        theta, w = np.asarray(best[1]['theta'], np.float64), best[1]['w']
        print(f'stage {stage:2d}: frozen {frozen.mean():.4f}  error_2 {1e3 * start:7.3f} -> {1e3 * best[2]:7.3f} mHa  '
              f'D {float(d_penalty(w)):7.2f}  ({time.time() - t0:.0f} s)', flush=True)

    final = np.where(frozen, qvals, qround(theta))
    assert not len(ccols) or frozen.all(), 'coded rounding needs a schedule that ends at 0.0'
    raw = np.mod(np.round(final * scale).astype(np.int64), 1 << a.brot)
    words = onebody.signed_gauge(raw, edges, a.brot)
    if gauged:
        assert np.array_equal(words, raw), 'the gauge fix moved a word although every angle was kept in the gauge'
    rmcode.check(words, addr, deg)
    if len(ccols):
        print(f'codes kept on every block: {a.codes}')
    drift = np.abs(np.abs(np.sum(encode.decode(raw, edges, a.brot) * encode.decode(words, edges, a.brot), axis=1)) - 1)
    assert drift.max() < 1e-9, 'gauge conversion changed a vector'
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, words=words, w=np.asarray(w, np.float64), brot=a.brot, coded=ccols, coded2=ccols[:0], codes=deg)
    print('saved', a.out)


if __name__ == '__main__':
    main()
