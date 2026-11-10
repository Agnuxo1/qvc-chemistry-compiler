# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""More channel rotations on a finished table: the L1 term of Lambda drops and error_2 does not move.

refine.rotate_columns (marculera, Apache-2.0) keeps A A^T exactly. The chain runs it with 2 sweeps and 10 hops; this repeats it
with more of both and several seeds, then recomputes offsets and one-body rows as the chain does. Usage: rotar.py IN.npz OUT.npz [seconds]
"""
import json
import sys
import time
from functools import partial

import numpy as np

import quantize  # noqa: F401  (our decoder, cached before the public modules look for theirs)
import build  # noqa: F401  (puts the verifier on the path)
import arbol_env  # noqa: F401
import onebody
import refit_weights as rw
import rmcode
from dfthcsos.scoreinfra.dfthc_math import lambda_h2

src, out = sys.argv[1], sys.argv[2]
wall = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
with np.load(src) as z:
    data = {k: np.array(z[k]) for k in z.files}
deg = np.asarray(data.pop("codes"), np.int64)
onebody.refresh = partial(rmcode.refresh, deg=deg)
brot = int(data["brot"])
edges = np.asarray(data["tree_edges"], np.int64)
w0 = np.asarray(data["W"], np.float64)
W0 = np.asarray(data["H2_I"], np.float64) - w0.sum(axis=1)
R, B, C = w0.shape
N = edges.shape[0] + 1
words2 = np.asarray(data["angle_words"], np.int64)[N:]
coded = [int(c) for c in data["coded"]]
u = rw.encode.decode(words2, edges, brot).reshape(R, B, N)
u /= np.linalg.norm(u, axis=2, keepdims=True)
ref = rw.load_reference(rw.check_fcidump())
with np.load(rw.SHIFTS) as z:
    _, _, S, beta = rw.native_inputs({"U": u, "W": w0, "H2_I": data["H2_I"], "H1_I": z["H1_I"], "Hsym_lower": z["Hsym_lower"]})
start = rw.official({k: data[k] for k in ("U", "W", "H2_I", "H1_I", "Hsym_lower", "tree_edges", "angle_words")}, brot)
print("inicio", json.dumps(start), "lambda_h2", lambda_h2(w0, W0), flush=True)
best, t0, seed = (lambda_h2(w0, W0), w0, W0), time.time(), 0
while time.time() - t0 < wall:
    w, W = rw.rotate_columns(best[1], best[2], sweeps=8, seed=seed, hops=30)
    l = lambda_h2(w, W)
    print(f"semilla {seed}: lambda_h2 {l:.5f} ({time.time()-t0:.0f} s)", flush=True)
    if l < best[0]:
        best = (l, w, W)
    seed += 1
_, w, W = best
p = rw.Problem(u, w, ref, S, beta)
W = rw.optimize_offsets(p, W, 0.0005)
cand = rw.assemble(words2, w, W, p, edges, brot, one_start=np.asarray(data["angle_words"])[:N], coded=coded)
m = rw.official(cand, brot)
print("final", json.dumps(m), "lambda_h2", lambda_h2(w, W), flush=True)
ok = m["error_2"] <= 0.01999 and m["error_1"] <= 0.0199 and m["E_gap"] > rw.GAP_FLOOR
print("factible", ok, flush=True)
if ok:
    np.savez(out, **cand, brot=brot, codes=deg)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
