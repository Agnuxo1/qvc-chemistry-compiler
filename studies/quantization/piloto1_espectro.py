# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Pilot 1: can a Hessian-weighted quantizer beat plain rounding at brot 7?

Pre-registered reading, written before the run:
  * Sanity: the Hessian must predict the measured cost of plain rounding.
  * Predicted Babai error = sqrt(sum r_kk^2 / 12) against sqrt(sum H_kk / 12).
  * A ratio below 0.3 justifies building the full quantizer. A ratio near 1
    means rows are nearly orthogonal and the idea does not pay.
"""
import json, sys, time
import numpy as np
import scipy.linalg as sl
from quant_lib import *

st, tei = load()
G = target(tei, st["S"])
del tei
words, tree, w, brot = st["words"], st["tree"], st["w"], st["brot"]
R, B, C = w.shape
two = words[N:]
theta8 = two * (np.pi / 2 ** (brot - 1))
u, D = decode_jac(theta8, tree)
print("recheck", np.abs(u - decode(theta8, tree)).max())
u3 = u.reshape(R, B, N)
e0, E0, Xm = error2(u3, w, G)
print("error_2 base", e0)
del E0

# Measured plain rounding to 7 bits, fixed weights
for name, f in (("7 bits, redondeo al par inferior", lambda x: (x // 2) * 2),
                ("7 bits, redondeo al par mas cercano", lambda x: 2 * np.round(x / 2 + 1e-9).astype(int) % 2 ** brot)):
    q = f(two)
    uq = decode(q * (np.pi / 2 ** (brot - 1)), tree).reshape(R, B, N)
    print(name, "error_2", error2(uq, w, G)[0], "fraccion cambiada", (q != two).mean())

del G
step = np.pi / 2 ** 6          # one 7-bit word
out = []
t0 = time.time()
for r in range(R):
    sl_rows = slice(r * B, (r + 1) * B)
    X_g = Xm[:, r * C:(r + 1) * C]
    H = group_hessian(u[sl_rows], D[sl_rows], w[r], X_g, step)
    d = np.diag(H).copy()
    tr = d.sum()
    eps = 1e-10 * tr / d.size
    H[np.diag_indices_from(H)] += eps
    orders = {"natural": np.arange(d.size), "diag_desc": np.argsort(-d)}
    res = dict(group=r, n=int(d.size), tr=float(tr), diag_q=[float(x) for x in np.quantile(d, [.01, .5, .99])])
    for k, o in orders.items():
        L = sl.cholesky(H[np.ix_(o, o)], lower=True, check_finite=False, overwrite_a=True)
        res[k] = float((np.diag(L) ** 2).sum())
        del L
    out.append(res)
    print(r, f"{time.time()-t0:.0f}s", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in res.items()}, flush=True)

tot = sum(o["tr"] for o in out)
print("rounding predicted, uniform step noise 1/12:", np.sqrt(tot / 12))
print("rounding predicted, words halved noise 1/8 on half of words:", np.sqrt(tot / 8))
for k in ("natural", "diag_desc"):
    s = sum(o[k] for o in out)
    print(k, "babai predicted", np.sqrt(s / 12), "ratio vs rounding", np.sqrt(s / tot))
json.dump(out, open(ROOT + "piloto1.json", "w"), indent=1)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
