"""Refit w and W at fixed words with an augmented Lagrangian, to spend the whole error budget on lambda_eff.

    python notebooks/dfthc-refit/experiments/refit_al.py REFINED.npz OUT.npz [--target 19.98] [--margin 0.0005]
                                                          [--outer 12] [--inner 300]

refit_weights.py minimizes log lambda_eff with one-sided quadratic penalties. L-BFGS stops at the kink of the
E_gap penalty after a couple of iterations (its own comment says so), so error_2 stays far below the target:
on the (9, 143, 46) own-weights tables it ended at 19.49 and 18.41 mHa against a 19.98 target. Here both
constraints enter a smooth augmented Lagrangian in mHa units, so the solve keeps moving along the E_gap floor
and trades error_2 for Lambda. The same exact moves and official metrics as refit_weights.refit follow.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import refit_weights as rw  # noqa: E402


def solve(data: dict, target_mha: float, margin: float, outer: int, inner: int, rounds: int, log=print):
    brot = int(data.get('brot', 10))
    edges = np.asarray(data['tree_edges'], np.int64)
    w0 = np.asarray(data['W'], np.float64)
    W0 = np.asarray(data['H2_I'], np.float64) - w0.sum(axis=1)
    R, B, C = w0.shape
    N = edges.shape[0] + 1
    words2 = np.asarray(data['angle_words'], np.int64)[N:]
    coded = [int(c) for c in data['coded']] if 'coded' in data else []
    coded2 = [int(c) for c in data['coded2']] if 'coded2' in data else []
    u = rw.encode.decode(words2, edges, brot).reshape(R, B, N)
    u /= np.linalg.norm(u, axis=2, keepdims=True)
    ref = rw.load_reference(rw.check_fcidump())
    with np.load(rw.SHIFTS) as z:
        _, _, S, beta = rw.native_inputs({'U': u, 'W': w0, 'H2_I': data['H2_I'], 'H1_I': z['H1_I'],
                                          'Hsym_lower': z['Hsym_lower']})
    K, Q, T2 = rw.error_terms(u, np.asarray(ref['tei'], np.float64), S)
    start = rw.official(data, brot)
    eta = int(ref['electrons'])
    wp = rw.WeightProblem(u, K, Q, T2, ref['h1_thc'] - 0.5 * eta * S + beta * np.eye(N),
                          float(rw.UPPER_ENERGY - ref['ecore'] + eta * beta))
    target, floor = 1e-3 * target_mha, rw.GAP_FLOOR + margin
    log(f"start: error_2 {1e3 * start['error_2']:.4f} mHa, E_gap {start['E_gap']:.4f}, lambda_eff {start['lambda_eff']:.4f}")
    scale = np.concatenate([np.full(w0.size, np.std(w0)), np.full(W0.size, np.std(W0))])
    y_e, y_g, rho = 0.0, 0.0, 1.0

    def lagrangian(z):
        x = z * scale
        w, W = x[:w0.size].reshape(w0.shape), x[w0.size:].reshape(W0.shape)
        (e2, gap, Lam), (de2, dgap, dLam) = wp.evaluate(w, W)
        rad = gap * (2 * Lam - gap)
        if rad <= 0:
            return 1e12, np.zeros_like(z)
        f = 500.0 * np.log(rad)                         # 1e3 log lambda_eff: per mille
        gw, gW = [1e3 * ((Lam - gap) * g + gap * l) / rad for g, l in zip(dgap, dLam)]
        ce, cg = 1e3 * (e2 - target), 1e3 * (floor - gap)   # constraints in mHa: <= 0 when satisfied
        pe, pg = max(0.0, y_e + rho * ce), max(0.0, y_g + rho * cg)
        f += (pe ** 2 - y_e ** 2 + pg ** 2 - y_g ** 2) / (2 * rho)
        gw = gw + 1e3 * pe * de2 - 1e3 * pg * dgap[0]
        gW = gW - 1e3 * pg * dgap[1]
        return f, np.concatenate([gw.ravel(), gW.ravel()]) * scale

    z = np.concatenate([w0.ravel(), W0.ravel()]) / scale
    t0 = time.time()
    for k in range(outer):
        res = minimize(lagrangian, z, jac=True, method='L-BFGS-B',
                       options={'maxiter': inner, 'maxcor': 30, 'ftol': 1e-13, 'gtol': 1e-7, 'maxls': 40})
        z = res.x
        x = z * scale
        w, W = x[:w0.size].reshape(w0.shape), x[w0.size:].reshape(W0.shape)
        (e2, gap, Lam), _ = wp.evaluate(w, W)
        ce, cg = 1e3 * (e2 - target), 1e3 * (floor - gap)
        lam = float(np.sqrt(gap * (2 * Lam - gap)))
        log(f'outer {k}: {res.nit} its, error_2 {1e3 * e2:.4f} mHa, E_gap {gap:.5f}, Lambda {Lam:.3f}, lambda_eff {lam:.4f}, '
            f'y {y_e:.3f} {y_g:.3f} rho {rho:.1f} ({time.time() - t0:.0f} s)')
        y_e, y_g = max(0.0, y_e + rho * ce), max(0.0, y_g + rho * cg)
        if max(ce, cg) > 0.02:
            rho = min(rho * 2.0, 200.0)
    best, best_m = None, None
    for k in range(rounds):                              # the exact moves of refine.py: they keep error_2
        w, W = rw.rotate_columns(w, W, sweeps=2, seed=k)
        p = rw.Problem(u, w, ref, S, beta)
        W = rw.optimize_offsets(p, W, margin)
        cand = rw.assemble(words2, w, W, p, edges, brot, one_start=np.asarray(data['angle_words'])[:N], coded=coded,
                           **({'coded2': coded2} if coded2 else {}))      # coded2 only where the pipeline has it
        m = rw.official(cand, brot)
        log(f'moves {k}', json.dumps(m))
        ok = m['error_2'] <= 0.01999 and m['error_1'] <= 0.0199 and m['E_gap'] > rw.GAP_FLOOR
        if ok and (best_m is None or m['lambda_eff'] < best_m['lambda_eff']):
            best, best_m = cand, m
    return best, best_m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('refined', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--target', type=float, default=19.98)
    ap.add_argument('--margin', type=float, default=0.0005)
    ap.add_argument('--outer', type=int, default=12)
    ap.add_argument('--inner', type=int, default=300)
    ap.add_argument('--rounds', type=int, default=3)
    a = ap.parse_args()
    with np.load(a.refined) as z:
        data = {k: np.array(z[k]) for k in z.files}
    best, best_m = solve(data, a.target, a.margin, a.outer, a.inner, a.rounds, log=lambda *x: print(*x, flush=True))
    if best is None:
        print('no feasible candidate: nothing saved')
        return
    np.savez(a.out, **best, brot=int(data.get('brot', 10)))
    print('RESULT', json.dumps(best_m))
    print('saved', a.out)


if __name__ == '__main__':
    main()
