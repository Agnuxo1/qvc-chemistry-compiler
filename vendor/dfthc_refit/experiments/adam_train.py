"""Train a structure with Adam the way the public seeds were trained: long, with a decaying learning rate.

    python notebooks/dfthc-refit/experiments/adam_train.py START.npz OUTDIR --steps N [--lr 1e-3] [--lr-final 1e-5]
                                                            [--kappa 5e-5] [--mu 0] [--report 2000] [--save 20000] [--step0 K]

The objective is the pipeline's: error_2 (fastfit, packed pair space) + kappa D(w). Adam runs in jitted
chunks on the device with lr(step) = lr * (lr_final / lr)^(step / steps). Every --save steps the current
structure goes to OUTDIR/last.npz (with the step count in OUTDIR/state.json) and the best error_2 seen to
OUTDIR/best.npz; `--step0` resumes the schedule at that step from a checkpoint. The L-BFGS seeds plateau
where they start (random 19, DF 6.8 at (9,180,90), 19 at a scoring shape); the public seeds came out of
tens of thousands of Adam epochs and prune far better, so this is the one lever not yet pulled.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import FCIDUMP, SHIFTS, UPPER_ENERGY  # noqa: E402
import fastfit  # noqa: E402

import jax  # noqa: E402

jax.config.update('jax_enable_x64', True)
jax.config.update('jax_default_matmul_precision', 'highest')
import jax.numpy as jnp  # noqa: E402
import optax  # noqa: E402
from dfthc import df_thc_sga  # noqa: E402

df_thc_sga.dtype = jnp.float64
from dfthc.train_df_thc_sga import Initialize  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('start', type=Path)
    ap.add_argument('outdir', type=Path)
    ap.add_argument('--steps', type=int, required=True, help='total schedule length (steps)')
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--lr-final', type=float, default=1e-5)
    ap.add_argument('--kappa', type=float, default=5e-5)
    ap.add_argument('--mu', type=float, default=0.0, help='rounding-sensitivity penalty, mu * predicted raw 8-bit rounding noise (Gram form, see objective); '
                    'at C = 40 mu 0.03 costs 0.05 mHa of fit for -2.5%% noise, 0.1 costs 0.35 for -5.6%%')
    ap.add_argument('--report', type=int, default=2000)
    ap.add_argument('--save', type=int, default=20000)
    ap.add_argument('--step0', type=int, default=0, help='resume the schedule at this step (START is a checkpoint)')
    ap.add_argument('--chunk', type=int, default=200)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    ref = Initialize(str(FCIDUMP), UPPER_ENERGY)
    ref = {k: (jnp.asarray(v, jnp.float64) if hasattr(v, 'dtype') and jnp.issubdtype(v.dtype, jnp.floating) else v)
           for k, v in ref.items()}
    with np.load(SHIFTS) as z:
        frozen = {k: jnp.asarray(z[k], jnp.float64) for k in ('Hsym_lower', 'H1_I')}
        shifts = {k: np.array(z[k]) for k in ('H1_I', 'Hsym_lower')}
    prob = fastfit.problem(ref, frozen, jnp.float64)

    def objective(p):
        eps = fastfit.error2(p[0], p[1], prob)
        D = 0.5 * jnp.sum(jnp.sum(jnp.abs(p[1]), axis=1) ** 2 - jnp.sum(p[1], axis=1) ** 2)
        if a.mu:
            # First-order 8-bit rounding sensitivity, sum_r sum_b w_rb^T G_r w_rb with G_r the Gram matrix of the copies
            # M_rc = sum_b w_rbc u_rb u_rb^T (= tr(A K A) per group, A = W W^T, K = (u_b . u_b')^2 on unit rows); it tracks the
            # measured per-row diag(J^T J) at rank correlation 0.998. kraw turns it into the predicted raw rounding noise (Ha)
            # of a C = 40 table, so mu is mHa of fit paid per mHa of raw noise (absorbed noise is ~7.5% of raw, 1:1 in ratio).
            u = p[0] / jnp.linalg.norm(p[0], axis=2, keepdims=True)
            K = jnp.einsum('rbn,rcn->rbc', u, u) ** 2
            A = jnp.einsum('rbc,rdc->rbd', p[1], p[1])
            P = jnp.einsum('rbc,rcd,rdb->', A, K, A)
            return eps + a.kappa * D + a.mu * 0.03518 * jnp.sqrt(P), (eps, D)
        return eps + a.kappa * D, (eps, D)

    opt = optax.inject_hyperparams(optax.adam)(learning_rate=a.lr)
    vg = jax.value_and_grad(objective, has_aux=True)

    @jax.jit
    def run(params, state, lr):
        state.hyperparams['learning_rate'] = lr

        def body(_, carry):
            p, s = carry
            (_, aux), g = vg(p)
            upd, s = opt.update(g, s, p)
            return optax.apply_updates(p, upd), s
        params, state = jax.lax.fori_loop(0, a.chunk, body, (params, state))
        (_, (eps, D)), _ = vg(params)
        return params, state, eps, D

    with np.load(a.start) as z:
        params = (jnp.asarray(z['U'], jnp.float64), jnp.asarray(z['W'], jnp.float64))
    state = opt.init(params)
    (_, (eps, D)), _ = vg(params)
    print(f'start {tuple(params[1].shape)} at step {a.step0}: error_2 {1e3 * float(eps):8.3f} mHa  D {float(D):7.2f}', flush=True)
    t0, step, best = time.time(), a.step0, float(eps)

    def save(name, p, eps):
        U, w = (np.asarray(x) for x in p)
        np.savez(a.outdir / name, U=U, W=w, H2_I=w.sum(axis=1), **shifts)

    while step < a.steps:
        n = min(a.chunk, a.steps - step)
        lr = a.lr * (a.lr_final / a.lr) ** (step / a.steps)
        params, state, eps, D = run(params, state, lr)
        step += a.chunk
        eps = float(eps)
        if eps < best:
            best = eps
            if step % a.save == 0:
                save('best.npz', params, eps)
        if step % a.report == 0:
            print(f'{step:9d}: error_2 {1e3 * eps:8.3f} mHa  D {float(D):7.2f}  lr {lr:.2e}  best {1e3 * best:8.3f}  '
                  f'({time.time() - t0:.0f} s, {(step - a.step0) / (time.time() - t0):.0f} steps/s)', flush=True)
        if step % a.save == 0:
            save('last.npz', params, eps)
            (a.outdir / 'state.json').write_text(json.dumps({'step': step, 'steps': a.steps, 'error_2_mHa': 1e3 * eps,
                                                             'best_mHa': 1e3 * best}))
    save('last.npz', params, float(eps))
    (a.outdir / 'state.json').write_text(json.dumps({'step': step, 'steps': a.steps, 'error_2_mHa': 1e3 * float(eps),
                                                     'best_mHa': 1e3 * best, 'done': True}))
    print('done', flush=True)


if __name__ == '__main__':
    main()
