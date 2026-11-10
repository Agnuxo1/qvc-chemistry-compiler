# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Assign rows to the 16-address blocks so that bit 0 of each coded word fits its Reed-Muller word better.

Inside a group the rows can be permuted freely: T and Q do not change. Bit 0 of a coded word must be RM(1,4) over each block, so the
rows that share a block are forced to agree on a word of that code. Cost of a block and edge: the best codeword of the rounding
harm a * (z - q(b))^2 over the rows of the block, with a the row's weight times its mass at that split. Simulated annealing over swaps
inside a group, from the public round-robin deal. Usage: reparto.py <marc.npz> <tree.npy> <seconds> <out.npz> [seed]
"""
import sys
import time

import numpy as np

import arboles as A

N = A.N
d = np.load(sys.argv[1])
th, w = d["th"].astype(float), d["w"].astype(float)
tree = np.load(sys.argv[2]).astype(np.int64)
wall, out = float(sys.argv[3]), sys.argv[4]
rng = np.random.default_rng(int(sys.argv[5]) if len(sys.argv) > 5 else 0)
R, B, C = w.shape
assert th.shape == (R * B, N - 1)
step = np.pi / 128
BIT = 2.0  # two steps apart: q(b) are the nearest integers of each parity


def decode(th):
    v = np.zeros((th.shape[0], N))
    v[:, 0] = 1.0
    for t, (p, q) in enumerate(tree):
        a = v[:, p].copy()
        v[:, p] = np.cos(th[:, t]) * a
        v[:, q] = np.sin(th[:, t]) * a
    return v


u = decode(th)
m = A.split_mass(u ** 2, tree)
rho = (w ** 2).sum(axis=2).reshape(R * B)
a = rho[:, None] * m                                 # harm weight of each (row, edge)
z = th / step
nearest_even = 2.0 * np.round(z / 2.0)
near_odd = 2.0 * np.round((z - 1.0) / 2.0) + 1.0
delta = a * ((z - near_odd) ** 2 - (z - nearest_even) ** 2)   # (rows, edges): harm of bit 1 minus harm of bit 0

# RM(1,4): 32 words of 16 bits
pts = np.array([[(x >> i) & 1 for i in range(4)] for x in range(16)])
gens = np.vstack([np.ones(16, int), pts.T])
CW = np.array([[(c >> i) & 1 for i in range(5)] for c in range(32)]) @ gens % 2  # (32, 16)
CW = CW.astype(float)
addr = N + np.arange(R * B)
block = addr // 16
slot = addr % 16
nb = int(block.max()) + 1
pos2row = np.arange(R * B)                           # position -> row
members = [np.flatnonzero(block == b) for b in range(nb)]
group = np.arange(R * B) // B


def block_cost(b):
    D = np.zeros((16, N - 1))
    pp = members[b]
    D[slot[pp]] = delta[pos2row[pp]]
    return float(np.min(CW @ D, axis=0).sum())


cost_b = np.array([block_cost(b) for b in range(nb)])
c0 = cur = best = cost_b.sum()
bp = pos2row.copy()
T0, T1 = 0.01 * abs(c0) / nb, 0.0005 * abs(c0) / nb
t0, n, acc = time.time(), 0, 0
print("inicio", c0, "bloques", nb, flush=True)
while time.time() - t0 < wall:
    g = int(rng.integers(R))
    i, j = rng.integers(0, B, 2) + g * B
    if i == j or block[i] == block[j]:
        continue
    bi, bj = int(block[i]), int(block[j])
    temp = T0 * (T1 / T0) ** ((time.time() - t0) / wall) if n % 200 == 0 else temp
    pos2row[[i, j]] = pos2row[[j, i]]
    ci, cj = block_cost(bi), block_cost(bj)
    dc = ci + cj - cost_b[bi] - cost_b[bj]
    n += 1
    if dc < 0 or rng.random() < np.exp(-dc / temp):
        cost_b[bi], cost_b[bj] = ci, cj
        cur += dc
        acc += 1
        if cur < best:
            best = cur
            bp = pos2row.copy()
    else:
        pos2row[[i, j]] = pos2row[[j, i]]
    if n % 100000 == 0:
        print(n, f"t={time.time()-t0:.0f}s actual {cur:.6g} mejor {best:.6g} inicio {c0:.6g} aceptados {acc}", flush=True)
assert np.array_equal(np.sort(bp), np.arange(R * B)) and np.array_equal(group[bp], group)
np.savez(out, th=th[bp], w=w.reshape(R * B, C)[bp].reshape(R, B, C))
base = float(np.minimum(delta, 0).sum())    # the unreachable floor: every row keeps its own best bit
print("fin", n, "inicio", c0, "mejor", best, "suelo sin codigo", base, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
