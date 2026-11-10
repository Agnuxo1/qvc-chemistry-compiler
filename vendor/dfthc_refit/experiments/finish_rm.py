"""Refine, refit, build and verify a table rounded by quantize_rm.py, with its Reed-Muller codes kept throughout.

    python notebooks/dfthc-refit/experiments/finish_rm.py ROUNDED.npz OUTDIR [--rounds 6] [--outer 200] [--inner 3000]

refine.py and refit_al.py run unchanged: both reach the one-body rows through onebody.refresh, which is replaced
here by rmcode.refresh, and neither moves a two-body word. The build is rmcode.build_family.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from functools import partial
from pathlib import Path

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
import rmcode  # noqa: E402
import build  # noqa: E402,F401  (puts the verifier on sys.path)
import onebody  # noqa: E402
import refine  # noqa: E402
import refit_al  # noqa: E402
from build import BASELINE_SCORE, KEYS, verify, write_kmx_family  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('rounded', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--brot', type=int, default=8)
    ap.add_argument('--margin', type=float, default=0.0005)
    ap.add_argument('--rounds', type=int, default=6)
    ap.add_argument('--target', type=float, default=19.98)
    ap.add_argument('--outer', type=int, default=200)
    ap.add_argument('--inner', type=int, default=3000)
    ap.add_argument('--shots', type=int, default=64)
    ap.add_argument('--trials', type=int, default=6)
    ap.add_argument('--no-refit', action='store_true', help='build the refined table as it is (a test of the pipeline)')
    a = ap.parse_args()
    log = lambda *x: print(*x, flush=True)  # noqa: E731
    a.out.mkdir(parents=True, exist_ok=True)
    with np.load(a.rounded) as z:
        words2, w, deg = np.asarray(z['words'], np.int64), np.asarray(z['w'], np.float64), np.asarray(z['codes'], np.int64)
        coded, coded2 = [int(c) for c in z['coded']], []
    onebody.refresh = partial(rmcode.refresh, deg=deg)   # `refine.assemble` and so `refit_al.solve` go through this
    t0 = time.time()
    best, m = refine.refine(words2, w, a.brot, a.rounds, a.margin, 3000, log=log, coded=coded, coded2=coded2)
    log('refined', json.dumps(m), f'({time.time() - t0:.0f} s)')
    np.savez(a.out / 'refined.npz', **best, brot=a.brot, codes=deg)
    data = {k: np.array(v) for k, v in best.items()} | {'brot': np.array(a.brot)}
    if not a.no_refit:
        best, m = refit_al.solve(data, a.target, a.margin, a.outer, a.inner, 3, log=log)
        if best is None:
            log('no feasible refit: nothing built')
            return
        log('refit', json.dumps(m), f'({time.time() - t0:.0f} s)')
        np.savez(a.out / 'refit_al.npz', **best, brot=a.brot, codes=deg)
    words = np.asarray(best['angle_words'], np.int64)
    rmcode.check(words, np.arange(len(words)), deg)
    sub = a.out / 'submission'
    sub.mkdir(exist_ok=True)
    np.savez(sub / 'submission.npz', **{k: np.array(best[k]) for k in KEYS}, tree_edges=best['tree_edges'], angle_words=words)
    family = rmcode.build_family(words, deg, a.brot, trials=a.trials, log=log)
    log('angle circuits: qubits', max(c.num_qubits for c in family), 'Toffolis per pass', sum(c.operation_statistics().num_toffoli_like for c in family))
    write_kmx_family(family, sub, format='kmb')
    try:
        r = verify(sub, shots_per_address=a.shots)
    except AssertionError as e:
        log('rejected:', e)
        return
    res = {'score': r['score'], 'improvement': BASELINE_SCORE / r['score'], 'lambda_eff': r['lambda_eff'], 'toffoli': r['toffoli_count'],
           'qubits': r['num_qubits'], 'error_1_mHa': 1e3 * r['metrics']['error_1'], 'error_2_mHa': 1e3 * r['metrics']['error_2'],
           'angles_toffoli': r['resources']['angles_toffoli']}
    (a.out / 'result.json').write_text(json.dumps(res, indent=1))
    log('RESULT', json.dumps(res))


if __name__ == '__main__':
    main()
