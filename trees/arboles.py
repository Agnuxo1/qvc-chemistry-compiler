# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Givens trees for the angle words: the verifier takes any tree rooted at 0 with parents before children.

Rounding an angle by delta moves a row by |du|^2 = delta^2 m_e, with m_e the row's mass at that split, so the rounding noise of
a row follows the sum of m_e over edges: the expected number of splits its mass goes through. A tree is a full binary decision
tree over the orbitals, so Huffman on the weighted marginal minimises that sum.
"""
import heapq

import numpy as np

N = 76


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


def check(edges):
    seen = {0}
    assert len(edges) == N - 1
    for p, q in edges:
        assert int(p) in seen and int(q) not in seen, (p, q)
        seen.add(int(q))
    assert len(seen) == N


def split_mass(a, edges):
    """Mass at each split, for rows of squared amplitudes a (rows, N)."""
    a = a.copy()
    m = np.zeros((a.shape[0], len(edges)))
    for t in range(len(edges) - 1, -1, -1):
        p, q = edges[t]
        m[:, t] = a[:, p] + a[:, q]
        a[:, p] += a[:, q]
    return m


def huffman(p, n=N):
    """Edges of the Huffman tree of the marginal p. Orbital 0 keeps the root; each subtree is held by its heaviest orbital."""
    heap = [(float(p[i]), i, ("hoja", i)) for i in range(n)]
    heapq.heapify(heap)
    c = n
    while len(heap) > 1:
        a, _, x = heapq.heappop(heap)
        b, _, y = heapq.heappop(heap)
        heapq.heappush(heap, (a + b, c, ("nodo", x, y)))
        c += 1
    root = heap[0][2]

    def leaves(t):
        return [t[1]] if t[0] == "hoja" else leaves(t[1]) + leaves(t[2])

    def holder(t):
        ls = leaves(t)
        return 0 if 0 in ls else max(ls, key=lambda i: p[i])

    edges, level = [], [root]
    while level:
        nxt = []
        for t in level:
            if t[0] == "hoja":
                continue
            l, r = t[1], t[2]
            if holder(r) == holder(t):
                l, r = r, l
            edges.append((holder(l), holder(r)))
            nxt += [l, r]
        level = nxt
    e = np.asarray(edges, dtype=np.int64)
    check(e)
    return e

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
