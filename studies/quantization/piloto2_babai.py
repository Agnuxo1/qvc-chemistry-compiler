# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Pilot 2: real Babai quantization of the two-body words at a target width.

Reference points fixed before the run (brot 7): plain rounding 0.445 measured,
public quantization-aware local search plateau 0.11, gate 0.02.
"""
import json, sys, time
import numpy as np
import scipy.linalg as sl
from scipy.optimize import minimize
from quant_lib import *

BITS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
PASSES = int(sys.argv[2]) if len(sys.argv) > 2 else 2
REFIT = int(sys.argv[3]) if len(sys.argv) > 3 else 150
ALPHA = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
TAG = f"b{BITS}"

st, tei = load()
G = target(tei, st["S"])
del tei
words, tree, w, brot = st["words"], st["tree"], st["w"].copy(), st["brot"]
R, B, C = w.shape
step = np.pi / 2 ** (BITS - 1)
z = words[N:].astype(np.float64) * (2.0 ** (BITS - brot))   # 8-bit words in target units
log = []


def state(z):
    u = decode(z * step, tree).reshape(R, B, N)
    return u


def refit(z, w, iters):
    """Weights-only L-BFGS on error_2^2, words fixed."""
    u = state(z)
    s = np.einsum("rbp,rbq->rbpq", u, u).reshape(R, B, N * N)

    def fg(v):
        ww = v.reshape(R, B, C)
        X = np.einsum("rbm,rbc->mrc", s, ww, optimize=True).reshape(N * N, R * C)
        E = X @ X.T
        E -= G
        f = float((E * E).sum())
        EX = (E @ X).reshape(N * N, R, C)
        g = 4.0 * np.einsum("rbm,mrc->rbc", s, EX, optimize=True)
        return f, g.ravel()

    r = minimize(fg, w.ravel(), jac=True, method="L-BFGS-B", options=dict(maxiter=iters, maxcor=30))
    return r.x.reshape(R, B, C), float(np.sqrt(r.fun))


t0 = time.time()
u = state(z)
e, E, Xm = error2(u, w, G)
print("inicio", e, flush=True)
zc = np.round(z)
print("redondeo", error2(state(zc), w, G)[0], flush=True)

for p in range(PASSES):
    for r in np.argsort([-np.linalg.norm(Xm[:, i * C:(i + 1) * C]) for i in range(R)]):
        rows = slice(r * B, (r + 1) * B)
        uu, D = decode_jac(z[rows] * step, tree)
        X_g = Xm[:, r * C:(r + 1) * C]
        H = group_hessian(uu, D, w[r], X_g, step)
        b = group_gradient(uu, D, w[r], X_g, E, step)
        d = np.diag(H).copy()
        H[np.diag_indices_from(H)] += ALPHA * d.mean() + 1e-14
        o = np.argsort(d)
        bo = b[o]
        L = sl.cholesky(H[np.ix_(o, o)], lower=True, check_finite=False, overwrite_a=True)
        del H
        delta = -sl.cho_solve((L, True), bo, check_finite=False)
        y = z[rows].ravel()[o] + delta
        n = y.size
        err = np.zeros(n)
        zq = np.empty(n)
        Ld = np.diag(L).copy()
        for k in range(n - 1, -1, -1):
            c = y[k] - (L[k + 1:, k] @ err[k + 1:]) / Ld[k]
            zq[k] = np.round(c)
            err[k] = zq[k] - y[k]
        del L
        znew = z.copy()
        flat = znew[rows].ravel()
        flat[o] = zq
        znew[rows] = flat.reshape(B, N - 1)
        en, En, Xn = error2(state(znew), w, G)
        ok = en < e or p == 0  # first pass must quantize every group
        print(f"pase {p} grupo {r} t={time.time()-t0:.0f}s error_2 {en:.5f} {'ok' if ok else 'rechazado'} |delta|max {np.abs(delta).max():.2f}", flush=True)
        if ok:
            z, e, E, Xm = znew, en, En, Xn
        del En, Xn
    frac = float(np.mean(z == np.round(z)))
    print(f"pase {p}: enteras {frac:.4f} error_2 {e:.5f}", flush=True)
    log.append(dict(p=p, e=e))
    w2, e2 = refit(np.round(z), w, REFIT)
    print(f"pase {p}: tras reajustar pesos, error_2 {e2:.5f}, t={time.time()-t0:.0f}s", flush=True)
    log[-1]["refit"] = e2
    w = w2
    z = np.round(z)
    e, E, Xm = error2(state(z), w, G)

np.savez(ROOT + f"piloto2_{TAG}.npz", z=z, w=w)
json.dump(log, open(ROOT + f"piloto2_{TAG}.json", "w"), indent=1)
print("fin", e, "t", time.time() - t0)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
