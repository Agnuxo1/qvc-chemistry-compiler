# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Second tree search: relabelling plus subtree moves, then the edges in the order that frees the costliest words.

A tree is a parent and an ordered child list per node, and a relabelling perm of the orbitals (root stays orbital 0). Moves: swap two
labels, or detach a subtree and hang it elsewhere. Cost as in busca.py but on the 7-bit grid of the coded batches for every edge.
Usage: busca2.py <table.npz> <seconds> <out.npy> <seed> [start_edges.npy]
"""
import sys
import time

import numpy as np

import arboles as A

N = A.N
step = np.pi / 128
d = np.load(sys.argv[1])
U, W = (d["U"], d["W"]) if "U" in d.files else (d["u"], d["w"])
U = U / np.linalg.norm(U, axis=2, keepdims=True)
R, B, C = W.shape
V = U.reshape(R * B, N)
rho = (W ** 2).sum(axis=2).reshape(R * B)
rho = rho / rho.sum()
wall, out = float(sys.argv[2]), sys.argv[3]
rng = np.random.default_rng(int(sys.argv[4]))
start = np.load(sys.argv[5]).astype(np.int64) if len(sys.argv) > 5 else A.log_depth_tree()


def per_edge(edges, h):
    a = V.copy()
    c = np.zeros(len(edges))
    for t in range(len(edges) - 1, -1, -1):
        p, q = edges[t]
        ap, aq = a[:, p], a[:, q]
        s = np.where(ap > 0, 1.0, np.where(ap < 0, -1.0, np.where(aq > 0, -1.0, 1.0)))
        th = np.arctan2(s * aq, s * ap)
        r = np.hypot(ap, aq)
        c[t] = float((rho * r ** 2 * (th - h * np.round(th / h)) ** 2).sum())
        a[:, p] = s * r
        a[:, q] = 0.0
    return c


def children_of(edges):
    ch = {i: [] for i in range(N)}
    for p, q in edges:
        ch[int(p)].append(int(q))
    return ch


def to_edges(ch):
    edges, level = [], [0]
    while level:
        nxt = []
        for p in level:
            for c in ch[p]:
                edges.append((p, c))
                nxt.append(c)
        level = nxt
    return np.asarray(edges, dtype=np.int64)


def subtree(ch, r):
    out, stack = set(), [r]
    while stack:
        x = stack.pop()
        out.add(x)
        stack += ch[x]
    return out


def cost(ch):
    return float(per_edge(to_edges(ch), step * 2).sum())


def ordena(edges, c):
    """Edges with the costliest first where parents and the order of siblings allow: the first batch stays uncoded."""
    ch = children_of(edges)
    cost_of = {(int(p), int(q)): float(x) for (p, q), x in zip(edges, c)}
    reached, order, nxt = {0}, [], {i: 0 for i in range(N)}
    while len(order) < N - 1:
        cand = [(cost_of[(p, ch[p][nxt[p]])], p, ch[p][nxt[p]]) for p in reached if nxt[p] < len(ch[p])]
        x, p, q = max(cand)
        order.append((p, q))
        nxt[p] += 1
        reached.add(q)
    return np.asarray(order, dtype=np.int64)


ch = children_of(start)
base_cost = float(per_edge(A.log_depth_tree(), step * 2).sum())
cur = best = cost(ch)
bch = {k: list(v) for k, v in ch.items()}
print("coste inicio / log_depth", cur / base_cost, flush=True)
T0, T1 = 0.002 * cur, 0.00002 * cur
t0, n, acc = time.time(), 0, 0
while time.time() - t0 < wall:
    frac = (time.time() - t0) / wall
    temp = T0 * (T1 / T0) ** frac
    undo = None
    if rng.random() < 0.5:                                  # swap two labels (structure stays)
        i, j = (int(x) for x in rng.integers(1, N, 2))
        if i == j:
            continue
        m = {i: j, j: i}
        new = {m.get(k, k): [m.get(c, c) for c in v] for k, v in ch.items()}
    else:                                                   # hang a subtree somewhere else
        q = int(rng.integers(1, N))
        sub = subtree(ch, q)
        targets = [x for x in range(N) if x not in sub]
        p2 = int(rng.choice(targets))
        new = {k: [c for c in v if c != q] for k, v in ch.items()}
        pos = int(rng.integers(0, len(new[p2]) + 1))
        new[p2] = new[p2][:pos] + [q] + new[p2][pos:]
    c = cost(new)
    n += 1
    if c < cur or rng.random() < np.exp((cur - c) / temp):
        ch, cur = new, c
        acc += 1
        if c < best:
            best, bch = c, {k: list(v) for k, v in new.items()}
    if n % 5000 == 0:
        print(n, f"t={time.time()-t0:.0f}s actual {cur/base_cost:.4f} mejor {best/base_cost:.4f} aceptados {acc}", flush=True)
e = to_edges(bch)
c1 = per_edge(e, step * 2)
e2 = ordena(e, c1)
A.check(e2)
np.save(out, e2)
c2 = per_edge(e2, step)[:5].sum() + per_edge(e2, step * 2)[5:].sum()
print("fin", n, "mejor/log_depth", best / base_cost, "con primer lote libre", c2 / base_cost, flush=True)
print("primer lote", e2[:5].tolist(), flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
