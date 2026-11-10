# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Weight refit that keeps trying: the augmented Lagrangian ends a few hundredths of a mHa either side of its target.

refit_al.solve (marculera, Apache-2.0) returns nothing when its last iterate lands above 19.99 mHa, even if every
other step was feasible, so one bad last step throws the whole refit away. Lowering the target slightly costs about
0.5 lambda_eff per mHa, far less than losing the refit. Usage: reajuste.py REFINED.npz OUT.npz [outer] [inner]
"""
import json
import sys
import time
from functools import partial

import numpy as np

import quantize  # noqa: F401  (our decoder, cached before the public modules look for theirs)
import build  # noqa: F401  (puts the verifier on the path)
import arbol_env  # noqa: F401  (a tree other than the public one, if QVC_TREE is set)
import onebody
import refit_al
import rmcode

TARGETS = (19.98, 19.965, 19.95, 19.92, 19.88)
MARGIN = 0.0005
_minimize = refit_al.minimize
_rng = np.random.default_rng(0)


def _kick(fun, x0, **kw):
    """L-BFGS-B can stop dead on the kink of E_gap and repeat 0 iterations for every outer step: a tiny jitter gets it moving."""
    res = _minimize(fun, x0, **kw)
    tries = 0
    while res.nit == 0 and tries < 12:
        tries += 1
        res = _minimize(fun, res.x + 1e-4 * _rng.standard_normal(res.x.shape), **kw)
    return res


refit_al.minimize = _kick


def reajustar(data, outer=200, inner=3000, log=print):
    """Best feasible refit over TARGETS, in order; (None, None) when none of them is feasible."""
    for target in TARGETS:
        t0 = time.time()
        best, m = refit_al.solve(data, target, MARGIN, outer, inner, 3, log=log)
        log("objetivo", target, "resultado", json.dumps(m), f"({time.time()-t0:.0f} s)")
        if best is not None:
            return best, m
    return None, None


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    outer = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    inner = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
    say = lambda *x: print(*x, flush=True)  # noqa: E731
    with np.load(src) as z:
        data = {k: np.array(z[k]) for k in z.files}
    deg = np.asarray(data.pop("codes"), np.int64)
    onebody.refresh = partial(rmcode.refresh, deg=deg)
    best, m = reajustar(data, outer, inner, say)
    if best is None:
        sys.exit("sin reajuste factible")
    np.savez(out, **best, brot=int(data["brot"]), codes=deg)
    say("final", json.dumps(m))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
