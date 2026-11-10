# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Pilot 4: continuous floor of the published shape (8, 143, 44).

Angles and weights free, no word grid. Tells how much of the 20 mHa budget is
rank error and how much is left for quantization.
"""
import sys, time
import numpy as np
from scipy.optimize import minimize
from quant_lib import *

ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
st, tei = load()
G = target(tei, st["S"])
del tei
words, tree, w0, brot = st["words"], st["tree"], st["w"], st["brot"]
R, B, C = w0.shape
th0 = words[N:] * (np.pi / 2 ** (brot - 1))
nth = th0.size
t0 = time.time()
hist = []


def fg(p):
    th = p[:nth].reshape(R * B, N - 1)
    w = p[nth:].reshape(R, B, C)
    u, D = decode_jac(th, tree)
    u3 = u.reshape(R, B, N)
    Xm = channels(u3, w)
    E = Xm @ Xm.T
    E -= G
    f = float((E * E).sum())
    EX = (E @ Xm).reshape(N, N, R, C)              # E x_c as matrices
    EXs = EX + EX.transpose(1, 0, 2, 3)
    # dX^c/dw_bc = u_b u_b^T ; dX^c/du_b = w_bc (du u^T + u du^T)
    gw = 2.0 * np.einsum("rbp,rbq,pqrc->rbc", u3, u3, EXs, optimize=True)
    Y = np.einsum("pqrc,rbc,rbq->rbp", EXs, w, u3, optimize=True)
    gth = 4.0 * np.einsum("ikp,ip->ik", D, Y.reshape(R * B, N), optimize=True)
    hist.append(np.sqrt(f))
    if len(hist) % 20 == 1:
        print(f"eval {len(hist)} t={time.time()-t0:.0f}s error_2 {hist[-1]:.6f}", flush=True)
    return f, np.concatenate([gth.ravel(), gw.ravel()])


p0 = np.concatenate([th0.ravel(), w0.ravel()])
# gradient check on a few random coordinates
f0, g0 = fg(p0)
rng = np.random.default_rng(0)
for k in rng.integers(0, p0.size, 4):
    h = 1e-5
    q = p0.copy(); q[k] += h
    r = p0.copy(); r[k] -= h
    print("check", k, g0[k], (fg(q)[0] - fg(r)[0]) / (2 * h), flush=True)
res = minimize(fg, p0, jac=True, method="L-BFGS-B", options=dict(maxiter=ITERS, maxcor=30))
print("suelo continuo", np.sqrt(res.fun), "t", time.time() - t0)
np.save(ROOT + "piloto4_p.npy", res.x)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
