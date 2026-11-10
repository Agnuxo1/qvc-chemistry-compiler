# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Prune a continuous table to one channel fewer per group: rotate the channels of each group, drop the weakest.

Channels of a group can be mixed by any rotation without changing the model, so the eigenvector of the smallest
eigenvalue of the channel Gram is the best channel to drop. Usage: poda.py <table.npz> <C>
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys

import numpy as np

P = (_HOME + "/")
N = 76
i, j = np.triu_indices(N)
wgt = np.where(i == j, 1.0, np.sqrt(2.0))
G = np.load(P + "work/Gp.npy")
with np.load(sys.argv[1]) as d:
    U = d["U"] if "U" in d.files else d["u"]
    W = d["W"] if "W" in d.files else d["w"]
C = int(sys.argv[2])
U = U / np.linalg.norm(U, axis=2, keepdims=True)
R, B, C0 = W.shape


def err(W):
    X = np.concatenate([((U[r][:, i] * U[r][:, j] * wgt).T @ W[r]) for r in range(R)], axis=1)
    return float(np.linalg.norm(X @ X.T - G))


print("inicio", err(W), flush=True)
out = np.zeros((R, B, C))
for r in range(R):
    S = U[r][:, i] * U[r][:, j] * wgt                  # (B, packed)
    X = S.T @ W[r]
    lam, Q = np.linalg.eigh(X.T @ X)
    out[r] = W[r] @ Q[:, C0 - C:]
    print(r, "energia que se quita", lam[:C0 - C], flush=True)
print("podada", err(out), flush=True)
np.savez(f"seed_{R}x{B}x{C}.npz", u=U, w=out)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
