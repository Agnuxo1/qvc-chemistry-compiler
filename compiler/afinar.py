# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Refine and refit a rounded table: offsets, gauge, one-body rows and weights, with its codes kept.

Calls the public refine.py and refit_al.py (marculera, Apache-2.0) as their finish_rm.py does;
the circuits come from compila.py. Usage: afinar.py ROUNDED.npz OUT.npz [rounds] [outer] [inner]
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
import refine
import rmcode
from reajuste import reajustar

src, out = sys.argv[1], sys.argv[2]
ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 6
OUTER = int(sys.argv[4]) if len(sys.argv) > 4 else 200
INNER = int(sys.argv[5]) if len(sys.argv) > 5 else 3000
BROT, MARGIN = 8, 0.0005
log = lambda *x: print(*x, flush=True)  # noqa: E731
with np.load(src) as z:
    words2, w, deg = np.asarray(z["words"], np.int64), np.asarray(z["w"], np.float64), np.asarray(z["codes"], np.int64)
    coded = [int(c) for c in z["coded"]]
onebody.refresh = partial(rmcode.refresh, deg=deg)
t0 = time.time()
best, m = refine.refine(words2, w, BROT, ROUNDS, MARGIN, 3000, log=log, coded=coded, coded2=[])
log("refinada", json.dumps(m), f"({time.time()-t0:.0f} s)")
data = {k: np.array(v) for k, v in best.items()} | {"brot": np.array(BROT)}
best2, m2 = reajustar(data, OUTER, INNER, log)
if best2 is None:
    log("sin reajuste factible: se conserva la refinada")
    best2, m2 = best, m
log("final", json.dumps(m2), f"({time.time()-t0:.0f} s)")
np.savez(out, **best2, brot=BROT, codes=deg)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
