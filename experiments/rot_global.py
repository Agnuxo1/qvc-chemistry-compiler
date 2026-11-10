# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Channel rotations of one group from random orthogonal starts: is the chain's Jacobi optimum global? Usage: rot_global.py <table.npz> <group> <restarts> <sweeps>"""
import sys
import time

import numpy as np

d = np.load(sys.argv[1])
w = d["W"].astype(float)
H = d["H2_I"].astype(float)
r, n, sweeps = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
A0 = np.concatenate([w[r], H[r][None]], axis=0)         # (B+1, C): the rows are the b's and w_B
C = A0.shape[1]


def f(A):
    return float((np.abs(A).sum(0) ** 2).sum())


def jacobi(A, rng, sweeps):
    prev = f(A)
    for s in range(sweeps):
        for i, j in rng.permutation([(i, j) for i in range(C) for j in range(i + 1, C)]):
            x, y = A[:, i].copy(), A[:, j].copy()
            cand = np.concatenate([np.arctan2(-x, y), np.arctan2(y, x)]) % (np.pi / 2)
            cand = np.concatenate([[0.0], cand])
            co, si = np.cos(cand)[:, None], np.sin(cand)[:, None]
            val = np.abs(co * x[None] + si * y[None]).sum(1) ** 2 + np.abs(co * y[None] - si * x[None]).sum(1) ** 2
            t = cand[int(np.argmin(val))]
            c, sn = np.cos(t), np.sin(t)
            A[:, i], A[:, j] = c * x + sn * y, c * y - sn * x
        cur = f(A)
        if prev - cur < 1e-6:
            break
        prev = cur
    return A


rng = np.random.default_rng(100 + r)
base = f(A0)
polished = f(jacobi(A0.copy(), rng, sweeps))
print("grupo", r, "actual", round(base, 4), "actual tras Jacobi", round(polished, 4), flush=True)
t0, vals = time.time(), []
for k in range(n):
    Q, _ = np.linalg.qr(rng.standard_normal((C, C)))
    vals.append(f(jacobi(A0 @ Q, rng, sweeps)))
    print(k, round(vals[-1], 4), round(time.time() - t0), flush=True)
print("mejor reinicio", round(min(vals), 4), "mediana", round(float(np.median(vals)), 4), "frente a", round(polished, 4), flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
