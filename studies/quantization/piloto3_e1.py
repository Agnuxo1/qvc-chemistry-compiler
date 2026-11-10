# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Pilot 3: Babai quantization of the one-body rows at a target width.

Fixed references at brot 7: plain rounding about 2.19 (public), annealing 0.0191
(public, same tree), gate 0.02. Uses the published weights, so h1_prime is the
8-bit one; it tests the quantizer, not the final table.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import sys, time
import numpy as np
import scipy.linalg as sl
from quant_lib import *

sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
from dfthcsos.scoreinfra.dfthc_math import build_h1_prime, reconstruct_x, h1_thc_reconstruction_error
from dfthcsos.verify import load_fixed_shifts  # noqa: F401

BITS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
st, tei = load()
oei = np.load(ROOT + "oei.npy")
words, tree, w, W, S, brot = st["words"], st["tree"], st["w"], st["W"], st["S"], st["brot"]
beta1 = float(np.load(ROOT + "chem_state.npz")["beta_1"])
R, B, C = w.shape
eta = 113
u2 = decode(words[N:] * (np.pi / 2 ** (brot - 1)), tree).reshape(R, B, N)
X = reconstruct_x(u2, w)
X = np.tril(X) + np.swapaxes(np.tril(X, k=-1), -1, -2)
h1 = oei - 0.5 * np.einsum("prrq->pq", tei)
del tei
hp = build_h1_prime(h1, S, beta1, eta, W, X)
step = np.pi / 2 ** (BITS - 1)


def e1(z):
    v = decode(z * step, tree)
    return h1_thc_reconstruction_error(v, h1, S, beta1, eta, W, X)


z = words[:N].astype(float) * 2.0 ** (BITS - brot)
print("8 bits", e1(z), "redondeo", e1(np.round(z)), "espectro", np.linalg.eigvalsh(hp)[[0, 37, 75]], flush=True)
ev, Q = np.linalg.eigh(hp)
for ALPHA in (1e-4, 1e-3, 1e-2):
    zc = z.copy()
    for it in range(6):
        v, D = decode_jac(zc * step, tree)
        idx = np.abs(v @ Q).argmax(1)
        lam = ev[idx]
        E1 = (v.T * lam) @ v - hp
        Dm = (D * step).reshape(N * (N - 1), N)
        row = np.repeat(np.arange(N), N - 1)
        H = np.empty((Dm.shape[0],) * 2)
        Du = Dm @ v.T
        VV = v @ v.T
        for i in range(N):
            a = slice(i * (N - 1), (i + 1) * (N - 1))
            for j in range(N):
                c = slice(j * (N - 1), (j + 1) * (N - 1))
                H[a, c] = 2 * lam[i] * lam[j] * ((Dm[a] @ Dm[c].T) * VV[i, j] + np.outer(Du[a, j], Du[c, i]))
        b = 2 * lam[row] * np.einsum("kp,kp->k", Dm, (E1 @ v.T).T[row])
        d = np.diag(H).copy()
        H[np.diag_indices_from(H)] += ALPHA * d.mean() + 1e-16
        o = np.argsort(d)
        L = sl.cholesky(H[np.ix_(o, o)], lower=True, check_finite=False, overwrite_a=True)
        delta = -sl.cho_solve((L, True), b[o], check_finite=False)
        y = zc.ravel()[o] + delta
        n = y.size
        err = np.zeros(n)
        zq = np.empty(n)
        Ld = np.diag(L).copy()
        for k in range(n - 1, -1, -1):
            cc = y[k] - (L[k + 1:, k] @ err[k + 1:]) / Ld[k]
            zq[k] = np.round(cc)
            err[k] = zq[k] - y[k]
        f = zc.ravel().copy()
        f[o] = zq
        zc = f.reshape(N, N - 1)
        print(f"alpha {ALPHA} it {it} error_1 {e1(zc):.5f}", flush=True)
np.save(ROOT + f"piloto3_b{BITS}.npy", zc)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
