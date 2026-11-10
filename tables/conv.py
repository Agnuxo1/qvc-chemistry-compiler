# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Check their continuous tables against our packed target and convert them to (th, w).

Usage: conv.py <table.npz> [<out.npz>]. Vectors go to unit norm with the scale moved into w;
angles come from our tree, which the verifier uses too. Their fit is on error_2, so the
number printed must match the last line of the table's log.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import sys

import numpy as np

P = (_HOME + "/")
N = 76
i, j = np.triu_indices(N)
wgt = np.where(i == j, 1.0, np.sqrt(2.0))
G = np.load(P + "work/Gp.npy")


def log_depth_tree(n=N):
    edges, level, depth = [], [0], 0
    while len(edges) < n - 1:
        nxt = []
        for label in level:
            nxt.append(label)
            right = label + (1 << depth)
            if right < n:
                edges.append((label, right))
                nxt.append(right)
        level, depth = nxt, depth + 1
    return np.asarray(edges, dtype=np.int64)


tree = np.load(os.environ["QVC_TREE"]).astype(np.int64) if os.environ.get("QVC_TREE") else log_depth_tree()   # any tree rooted at 0, parents first


def err(U, W):
    """error_2 for vectors (R, B, N) and weights (R, B, C)."""
    R, B, C = W.shape
    s = (U[:, :, i] * U[:, :, j] * wgt).reshape(R, B, -1)
    X = np.einsum("rbp,rbc->prc", s, W, optimize=True).reshape(len(i), R * C)
    E = X @ X.T
    E -= G
    return float(np.linalg.norm(E))


def angles(v):
    """Angles of unit rows on the tree, parent amplitude kept with its sign (cos >= 0)."""
    a = v.copy()
    th = np.zeros((len(a), len(tree)))
    for t in range(len(tree) - 1, -1, -1):
        p, q = tree[t]
        s = np.where(a[:, p] > 0, 1.0, np.where(a[:, p] < 0, -1.0, np.where(a[:, q] > 0, -1.0, 1.0)))
        th[:, t] = np.arctan2(s * a[:, q], s * a[:, p])
        a[:, p] = s * np.hypot(a[:, p], a[:, q])
        a[:, q] = 0.0
    return th


def decode(th):
    v = np.zeros((th.shape[0], N))
    v[:, 0] = 1.0
    for t, (p, c) in enumerate(tree):
        a, b = v[:, p].copy(), v[:, c].copy()
        co, si = np.cos(th[:, t]), np.sin(th[:, t])
        v[:, p] = co * a - si * b
        v[:, c] = si * a + co * b
    return v


with np.load(sys.argv[1]) as z:
    U, W = (z["U"].astype(float), z["W"].astype(float)) if "U" in z.files else (z["u"].astype(float), z["w"].astype(float))
    if "tree_edges" in z.files:
        print("mismo arbol", np.array_equal(z["tree_edges"], tree))
R, B, C = W.shape
if os.environ.get("QVC_DEAL"):                       # deal rows over the 16-address blocks by strength, as deal_rows.py
    for r in range(R):
        nb = -(-B // 16)
        sizes = [min(16, B - j * 16) for j in range(nb)]
        perm, slots, jb = np.empty(B, int), [0] * nb, 0
        for row in np.argsort(-np.sum(W[r] ** 2, axis=1)):
            while slots[jb] >= sizes[jb]:
                jb = (jb + 1) % nb
            perm[jb * 16 + slots[jb]] = row
            slots[jb] += 1
            jb = (jb + 1) % nb
        U[r], W[r] = U[r][perm], W[r][perm]
n = np.linalg.norm(U, axis=2)
u = U / n[:, :, None]
w = W.copy()
print(os.path.basename(sys.argv[1]), W.shape, "error_2 con nuestro objetivo", err(u, w))
th = angles(u.reshape(-1, N))
v = decode(th)
print("deriva", np.abs(np.abs((v * u.reshape(-1, N)).sum(1)) - 1).max(), "fuera de [-pi/2,pi/2]", (np.abs(th) > np.pi / 2 + 1e-12).mean())
print("error_2 tras angulos", err(v.reshape(R, B, N), w))
if len(sys.argv) > 2:
    np.savez(sys.argv[2], th=th, w=w)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
