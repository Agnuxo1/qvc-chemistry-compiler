# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Warm start for a smaller table: drop rows per group by backward elimination and, if asked, add channels from the residual.

Each channel of a group is L_rc = sum_b w_rbc u_b u_b^T, so removing a row b is a least-squares column deletion whose
cost per channel is w_bc^2 / (K^-1)_bb, with K the Gram of the packed products. The weakest row goes, the weights of the
rest absorb it exactly as in the normal equations. New channels are the top eigenvectors of G - X X^T, projected on
the group's remaining rows. Usage: podaB.py <table.npz> <B> <C> <name> [R]  ->  seed_<name>.npz with u (unit) and w.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import sys

import numpy as np

ROOT = os.environ.get("QVC_ROOT", (_HOME + "/work/"))
N = 76
i, j = np.triu_indices(N)
wgt = np.where(i == j, 1.0, np.sqrt(2.0))
G = np.load(ROOT + "Gp.npy")
with np.load(sys.argv[1]) as d:
    U = d["U"] if "U" in d.files else d["u"]
    W = d["W"] if "W" in d.files else d["w"]
Bn, Cn, name = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
U = U / np.linalg.norm(U, axis=2, keepdims=True)
Rn = int(sys.argv[5]) if len(sys.argv) > 5 else W.shape[0]
if Rn < W.shape[0]:                 # drop the groups with the least channel energy; the new channels below take over
    energy = np.array([np.sum(((U[r][:, i] * U[r][:, j] * wgt).T @ W[r]) ** 2) for r in range(W.shape[0])])
    keep_groups = np.sort(np.argsort(-energy)[:Rn])
    print("energia por grupo", np.round(energy, 3), "quedan", keep_groups, flush=True)
    U, W = U[keep_groups], W[keep_groups]
R, B0, C0 = W.shape
assert Bn <= B0 and Cn >= C0


def pack(u):
    return u[:, i] * u[:, j] * wgt


def channels(us, ws):
    return np.concatenate([pack(us[r]).T @ ws[r] for r in range(R)], axis=1)


def err(us, ws):
    X = channels(us, ws)
    E = X @ X.T
    E -= G
    return float(np.linalg.norm(E))


print("inicio", (R, B0, C0), err(U, W), flush=True)
newU, newW = np.zeros((R, Bn, N)), np.zeros((R, Bn, C0))
for r in range(R):
    S = pack(U[r])
    K = S @ S.T
    Ki = np.linalg.pinv(K, hermitian=True, rcond=1e-12)
    keep = list(range(B0))
    w = W[r].copy()
    lost = 0.0
    while len(keep) > Bn:
        cost = (w ** 2).sum(1) / np.diag(Ki)
        k = int(np.argmin(cost))
        lost += float(cost[k])
        ki = Ki[:, k].copy()
        w = w - np.outer(ki, w[k]) / Ki[k, k]
        Ki = Ki - np.outer(ki, ki) / Ki[k, k]
        ok = np.delete(np.arange(len(keep)), k)
        Ki, w = Ki[np.ix_(ok, ok)], w[ok]
        del keep[k]
    newU[r], newW[r] = U[r][keep], w
    print("grupo", r, "residuo cuadrado por canales", round(lost, 6), flush=True)
print("podada", err(newU, newW), flush=True)
if Cn > C0:
    extra = Cn - C0
    X = channels(newU, newW)
    E = G - X @ X.T
    lam, V = np.linalg.eigh(E)
    order = np.argsort(-lam)[:R * extra]
    print("autovalores positivos usados", lam[order[0]], lam[order[-1]], flush=True)
    sols, A = [], []
    for r in range(R):
        S = pack(newU[r])
        A.append((S, np.linalg.pinv(S @ S.T, hermitian=True, rcond=1e-12)))
    left = [extra] * R
    added = [[] for _ in range(R)]
    for o in order:
        v = V[:, o] * np.sqrt(max(lam[o], 0.0))
        best, bw, br = None, None, None
        for r in range(R):
            if left[r] == 0:
                continue
            S, Ki = A[r]
            c = Ki @ (S @ v)
            res = float(np.sum((S.T @ c - v) ** 2))
            if best is None or res < best:
                best, bw, br = res, c, r
        added[br].append(bw)
        left[br] -= 1
    newW = np.concatenate([np.concatenate([newW[r], np.stack(added[r], axis=1)], axis=1)[None] for r in range(R)])
    print("con canales nuevos", err(newU, newW), flush=True)
np.savez(ROOT + f"seed_{name}.npz", u=newU, w=newW)
print("guardada", name, newW.shape, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
