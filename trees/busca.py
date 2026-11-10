# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Search over Givens trees for less rounding noise: relabel orbitals of a fixed tree shape, cost = independent-rounding estimate.

cost(T) = sum_rows rho sum_edges m_e (theta - round(theta))^2: the mass at each split times its squared rounding residual, with rho
the row's squared weight. Angles close to 0 or pi/2 cost almost nothing, so a tree that keeps a row's main orbitals together can pay
less than the balanced label order. Usage: busca.py <table.npz> <seconds> <out.npy> [seed] [start_edges.npy]
"""
import sys
import time

import numpy as np

import arboles as A

N = A.N
step = np.pi / 128
FREE = int(__import__('os').environ.get('QVC_FREE', '5'))   # edges before this index are uncoded (batch 0 with code 1-14)
d = np.load(sys.argv[1])
U, W = (d["U"], d["W"]) if "U" in d.files else (d["u"], d["w"])
U = (U / np.linalg.norm(U, axis=2, keepdims=True))
R, B, C = W.shape
V = U.reshape(R * B, N)
rho = (W ** 2).sum(axis=2).reshape(R * B)
rho = rho / rho.sum()
wall, out = float(sys.argv[2]), sys.argv[3]
rng = np.random.default_rng(int(sys.argv[4]) if len(sys.argv) > 4 else 0)
base = np.load(sys.argv[5]) if len(sys.argv) > 5 else A.log_depth_tree()


def cost(edges):
    a = V.copy()
    tot = 0.0
    for t in range(len(edges) - 1, -1, -1):
        p, q = edges[t]
        ap, aq = a[:, p], a[:, q]
        s = np.where(ap > 0, 1.0, np.where(ap < 0, -1.0, np.where(aq > 0, -1.0, 1.0)))
        th = np.arctan2(s * aq, s * ap)
        r = np.hypot(ap, aq)
        h = step if t < FREE else step * 2.0               # bit 0 of the coded batches is near-fixed: their words act as 7-bit
        tot += float((rho * (r ** 2) * (th - h * np.round(th / h)) ** 2).sum())
        a[:, p] = s * r
        a[:, q] = 0.0
    return tot


def relabel(edges, perm):
    return perm[edges]


perm = np.arange(N)
c0 = best = cur = cost(base)
bp = perm.copy()
T0, T1 = 0.003 * c0, 0.00005 * c0
t0, n, acc = time.time(), 0, 0
print("inicio coste", c0, flush=True)
while time.time() - t0 < wall:
    frac = (time.time() - t0) / wall
    temp = T0 * (T1 / T0) ** frac
    i, j = rng.integers(1, N, 2)
    if i == j:
        continue
    perm[[i, j]] = perm[[j, i]]
    c = cost(relabel(base, perm))
    n += 1
    if c < cur or rng.random() < np.exp((cur - c) / temp):
        cur = c
        acc += 1
        if c < best:
            best = c
            bp = perm.copy()
    else:
        perm[[i, j]] = perm[[j, i]]
    if n % 2000 == 0:
        print(n, f"t={time.time()-t0:.0f}s actual {cur/c0:.4f} mejor {best/c0:.4f} aceptados {acc}", flush=True)
e = relabel(base, bp)
A.check(e)
np.save(out, e)
print("fin evaluaciones", n, "mejor/inicio", best / c0, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
