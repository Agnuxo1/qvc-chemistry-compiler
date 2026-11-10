# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente (this port and its modifications)
# SPDX-License-Identifier: Apache-2.0
# Derived-From: public DFTHC refit pipeline by marculera (Apache-2.0); see NOTICE and docs/ATTRIBUTION.md
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (Apache-2.0): keep this notice, the NOTICE file and the credit to both authors in any copy.
"""Orbital-clustered seed at any (R, B, C), on our packed target.

marculera's compact_seed.py (Apache-2.0) in numpy: pivoted-Cholesky leaves of the weighted
target, balanced k-means on the leaves' orbital profiles, simultaneous OMP over each group's
eigenvectors, least-squares weights. Our Gp already is d T d with d = sqrt(m).
Usage: semilla.py <R> <B> <C> [k-means seed] -> seed_<R>x<B>x<C>[_k].npz with u (unit) and w.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import sys
import time

import numpy as np

N = 76
ROOT = os.environ.get("QVC_ROOT", (_HOME + "/work/"))
R, B, C = (int(x) for x in sys.argv[1:4])
KS = int(sys.argv[4]) if len(sys.argv) > 4 else 0
i, j = np.triu_indices(N)
m = np.where(i == j, 1.0, 2.0)
d = np.sqrt(m)
Tw = np.load(ROOT + "Gp.npy")
t0 = time.time()


def unpack(a):
    L = np.zeros((N, N))
    L[i, j] = a
    L[j, i] = a
    return L


def balanced_kmeans(X, size, weight, iters=60):
    rng = np.random.default_rng(KS)
    n = len(X)
    lab = rng.permutation(np.repeat(np.arange(R), size))
    for _ in range(iters):
        cen = np.array([np.average(X[lab == r], axis=0, weights=weight[lab == r] + 1e-12) for r in range(R)])
        cen /= np.linalg.norm(cen, axis=1, keepdims=True)
        sim = X @ cen.T
        srt = np.sort(sim, axis=1)
        order = np.argsort(-(srt[:, -1] - srt[:, -2]))      # the most decided rows pick first
        left, new = np.full(R, size), np.zeros(n, int)
        for idx in order:
            for r in np.argsort(-sim[idx]):
                if left[r] > 0:
                    new[idx] = r
                    left[r] -= 1
                    break
        if np.all(new == lab):
            break
        lab = new
    return lab


def omp(cand, targets):
    """B unit vectors whose pair vectors best span the copies, each copy re-projected after a pick."""
    Pi = (cand[:, i] * cand[:, j]) * m
    Pn = Pi / np.linalg.norm(Pi, axis=1, keepdims=True)
    Y = targets * m
    res = Y.copy()
    chosen = []
    for _ in range(B):
        sc = np.sum((Pn @ res.T) ** 2, axis=1)
        sc[chosen] = -1.0
        chosen.append(int(np.argmax(sc)))
        A = Pi[chosen].T
        res = Y - (A @ np.linalg.lstsq(A, Y.T, rcond=None)[0]).T
    return cand[chosen]


K = R * C
diag, L = np.diag(Tw).copy(), np.zeros((len(Tw), K))
for k in range(K):
    q = int(np.argmax(diag))
    L[:, k] = (Tw[:, q] - L[:, :k] @ L[q, :k]) / np.sqrt(diag[q])
    diag = np.maximum(diag - L[:, k] ** 2, 0)
leaves = [unpack(L[:, k] / d) for k in range(K)]
prof = np.array([np.sqrt(np.sum(l ** 2, axis=1)) for l in leaves])
prof /= np.linalg.norm(prof, axis=1, keepdims=True)
wt = np.array([np.sum(l ** 2) for l in leaves])
lab = balanced_kmeans(prof, C, wt)
U, W = np.zeros((R, B, N)), np.zeros((R, B, C))
for r in range(R):
    ks = list(np.flatnonzero(lab == r))
    cand = np.concatenate([np.linalg.eigh(leaves[k])[1].T for k in ks])
    U[r] = omp(cand, np.stack([leaves[k][i, j] for k in ks]))
    pairs = (U[r][:, i] * U[r][:, j]) * m
    for c, k in enumerate(ks):
        W[r, :, c] = np.linalg.lstsq(pairs.T, leaves[k][i, j] * m, rcond=None)[0]
    print("grupo", r, f"{time.time()-t0:.0f}s", flush=True)
wgt = np.where(i == j, 1.0, np.sqrt(2.0))
X = np.einsum("rbp,rbc->prc", (U[:, :, i] * U[:, :, j] * wgt), W, optimize=True).reshape(len(i), K)
E = X @ X.T
E -= Tw
share = np.bincount(lab, weights=wt, minlength=R) / wt.sum()
print(f"semilla {W.shape}: error_2 {np.linalg.norm(E):.5f}; grupos {share.min():.3f}-{share.max():.3f} del peso; {time.time()-t0:.0f}s", flush=True)
name = f"seed_{R}x{B}x{C}" + (f"_{KS}" if KS else "") + ".npz"
np.savez(os.environ.get("QVC_OUT", "./") + name, u=U, w=W)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: Apache-2.0 :: cite the author when reusing
