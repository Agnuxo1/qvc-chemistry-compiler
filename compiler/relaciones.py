# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Relation search for the loader decomposition.

tensorqrom.group_features draws all its relations at random at once and keeps only about seven
before the rank-one features stop spanning. Here relations enter one at a time: a candidate
stays only if the surviving features still span the smaller space, and among candidates the
one with the fewest paired products wins. The idea is described publicly by qwertykeypadapple
and Gluzdov; this implementation is ours, on top of tensorqrom (marculera, Apache-2.0).
"""
import os

import tensorqrom as tq


def _choices(rel, Y, m, rng):
    """Rank-one features (y, s, flat, 0) of every output direction s that satisfy `rel`."""
    flat = lambda y, s: sum(s << (i * m) for i in tq._bits(y))  # noqa: E731
    out = {}
    for s in range(1, 1 << m):
        cons = [sum((bin((r >> (i * m)) & s).count("1") & 1) << i for i in range(Y)) for r in rel]
        ys = tq.nullspace(cons, Y)
        rng.shuffle(ys)
        out[(s, 0)] = [(y, s, flat(y, s), 0) for y in ys]
    return out


def _dims(ch):
    return sum(len(v) for v in ch.values())


MUESTRA, FINOS, REINTENTOS, PACIENCIA = (int(os.environ.get(k, v)) for k, v in
                                         (("QVC_MUESTRA", 40), ("QVC_FINOS", 6), ("QVC_REINTENTOS", 3), ("QVC_PACIENCIA", 3)))


def buscar(rows, Y, m, rng, muestra=MUESTRA, finos=FINOS, reintentos=REINTENTOS):
    """Features spanning a space that holds `rows`, or None; greedy admission of relations."""
    n = Y * m
    todas = tq.nullspace(rows, n)
    kept, ind = [], {}
    ch = _choices(kept, Y, m, rng)
    best = tq._pair_first(ch, n, rng)
    if best is None:
        return None
    nbest = tq._products(best)
    sin_mejora = 0
    while len(kept) < len(todas):
        cands = []
        seen = set()
        for _ in range(muestra):
            v = 0
            for r in todas:
                if rng.random() < 0.5:
                    v ^= r
            red = tq._reduce(v, ind)
            if red and red not in seen:
                seen.add(red)
                cands.append(v)
        if not cands:
            break
        # screen by how many feature dimensions a relation leaves
        scored = sorted(cands, key=lambda v: -_dims(_choices(kept + [v], Y, m, rng)))[:finos]
        top = None
        for v in scored:
            rel = kept + [v]
            span = n - len(rel)
            c = _choices(rel, Y, m, rng)
            for _ in range(reintentos):
                f = tq._pair_first(c, span, rng)
                if f is not None and (top is None or tq._products(f) < top[0]):
                    top = (tq._products(f), f, v)
        if top is None:
            break
        kept.append(top[2])
        red = tq._reduce(top[2], ind)
        ind[red.bit_length() - 1] = red
        if top[0] < nbest:
            nbest, best, sin_mejora = top[0], top[1], 0
        else:
            sin_mejora += 1
            if sin_mejora > PACIENCIA:
                break
    return best


_memo = {}


def group_features(rows, Y, m, codim, rng, restarts=8, allowed=None):
    """Drop-in for tensorqrom.group_features: `shared` calls it for many codimensions, one search serves them."""
    key = (tuple(rows), Y, m)
    if key not in _memo:
        _memo[key] = buscar(rows, Y, m, rng) if m <= 7 else tq._orig_group_features(rows, Y, m, codim, rng, restarts, allowed)
    return _memo[key]


def activar():
    if not hasattr(tq, "_orig_group_features"):
        tq._orig_group_features = tq.group_features
        tq.group_features = group_features

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
