# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Loader decomposition grouped on the low side: all outputs at once, five triples of low monomials.

tensorqrom.shared groups six outputs against the 15 low monomials, and rank-one features stop being plentiful at 76 per
group. Grouping the other way, 3 low coordinates against all outputs, a Toffoli carries a feature (y, s) from two
triples with the same output direction s. The structure is read from the public 24.94 circuits, where low operands only
take 35 values, the nonzero elements of five 3-dimensional spaces; the search below is ours.

For each triple the features must span a space W holding its rows. W is the annihilator of relations K: a feature
(y, s) lies in W when s solves the relations contracted with y. A product needs s in the solutions of both triples,
so every relation costs candidates and saves one feature. Relations enter one at a time while the pairs still span.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import random
import sys
import time

import numpy as np
import tensorqrom as tq

GRUPOS = [(4, 6, 10), (8, 7, 9), (2, 3, 5), (1, 11, 13), (14, 12, 15)]   # low monomial masks: x2, x1x2, x1x3 ...
T3 = range(1, 8)
MUESTRA, FINOS, PACIENCIA, REINTENTOS = (int(os.environ.get(k, v)) for k, v in
                                         (("QVC_BM", 12), ("QVC_BF", 3), ("QVC_BP", 24), ("QVC_BR", 1)))
RECOCIDO = float(os.environ.get("QVC_BA", "0"))      # seconds of relation swaps each time the greedy search stalls


def _paridad(x):
    return bin(x).count("1") & 1


class Problema:
    def __init__(self, C):
        X = C[1:, 1:]                                # (15 low, 76 high, O)
        self.L, self.H, self.O = X.shape
        O = self.O
        self.mask = (1 << O) - 1
        self.rows = []
        for g in GRUPOS:
            rows = []
            for h in range(self.H):
                v = 0
                for pos, m in enumerate(g):
                    v |= sum(1 << o for o in range(O) if X[m - 1, h, o]) << (pos * O)
                rows.append(v)
            self.rows.append(rows)
        self.N = [tq.nullspace(r, 3 * O) for r in self.rows]
        self.triv = []
        for i, g in enumerate(GRUPOS):              # coordinates no row uses: outputs that do not reach this monomial
            used = 0
            for r in self.rows[i]:
                used |= r
            self.triv.append([1 << b for b in range(3 * O) if not used >> b & 1])

    def flat(self, y, s):
        return sum(s << (p * self.O) for p in range(3) if y >> p & 1)

    def contrae(self, rho, y):
        v = 0
        for p in range(3):
            if y >> p & 1:
                v ^= (rho >> (p * self.O)) & self.mask
        return v


def soluciones(P, K, rng, limite=6):
    """Candidates (i, y, j, y2, s) and, per (i, y), the single-feature solutions."""
    E = [{y: [P.contrae(r, y) for r in K[i]] for y in T3} for i in range(len(GRUPOS))]
    cand, n = [], 0
    for i in range(len(GRUPOS)):
        for j in range(i, len(GRUPOS)):
            for y in T3:
                for y2 in T3:
                    if i == j and y2 <= y:
                        continue
                    S = tq.nullspace(E[i][y] + E[j][y2], P.O)
                    n += len(S)
                    if not S:
                        continue
                    vs = list(S) if len(S) <= limite else []
                    if len(S) == 2:
                        vs.append(S[0] ^ S[1])
                    for _ in range(limite if len(S) > limite else 0):
                        v = 0
                        for b in S:
                            if rng.random() < 0.5:
                                v ^= b
                        if v:
                            vs.append(v)
                    cand += [(i, y, j, y2, s) for s in vs]
    return cand, E, n


def elegir(P, K, rng):
    """Best of a few greedy passes; past the generic limit only some pairs have a solution, and the order matters."""
    cand, E, _ = soluciones(P, K, rng)
    best = None
    for _ in range(REINTENTOS):
        r = _pasada(P, K, rng, cand, E)
        if r is not None and (best is None or r[0] < best[0]):
            best = r
    return best


def _pasada(P, K, rng, cand, E):
    """One greedy pass; None if some triple cannot reach its whole span."""
    rng.shuffle(cand)
    piv = [dict() for _ in GRUPOS]
    need = [3 * P.O - len(K[i]) for i in range(len(GRUPOS))]
    buckets = {}
    for c in cand:
        buckets.setdefault((c[0], c[2]), []).append(c)
    picked = []
    while True:                                      # the two triples that still miss most, so none is left without a partner
        rem = [need[i] - len(piv[i]) for i in range(len(GRUPOS))]
        live = [(rem[i] + rem[j] + rng.random(), i, j) for (i, j), v in buckets.items()
                if v and rem[i] > 0 and rem[j] > 0 and (i != j or rem[i] > 1)]
        if not live:
            break
        _, i, j = max(live)
        _, y, _, y2, s = buckets[(i, j)].pop()
        fi, fj = P.flat(y, s), P.flat(y2, s)
        ri = tq._reduce(fi, piv[i])
        if not ri:
            continue
        if i == j:
            trial = dict(piv[i])
            trial[ri.bit_length() - 1] = ri
            rj = tq._reduce(fj, trial)
        else:
            rj = tq._reduce(fj, piv[j])
        if not rj:
            continue
        piv[i][ri.bit_length() - 1] = ri
        piv[j][rj.bit_length() - 1] = rj
        picked.append((i, y, j, y2, s))
    singles = []
    for i in range(len(GRUPOS)):
        if len(piv[i]) >= need[i]:
            continue
        for y in T3:
            for s in tq.nullspace(E[i][y], P.O):
                r = tq._reduce(P.flat(y, s), piv[i])
                if r and len(piv[i]) < need[i]:
                    piv[i][r.bit_length() - 1] = r
                    singles.append((i, y, s))
        if len(piv[i]) < need[i]:
            return None
    return len(picked) + len(singles), picked, singles


def _dimensiones(P, K, i, E):
    """Solution dimensions of every pair of contractions that involves triple i."""
    out = {}
    for j in range(len(GRUPOS)):
        for y in T3:
            for y2 in T3:
                if i == j and y2 <= y:
                    continue
                out[(j, y, y2)] = len(tq.nullspace(E[i][y] + E[j][y2], P.O))
    return out


def recocer(P, K, rng, tope):
    """Swap relations at fixed count towards more pairs with a solution: only the choice of K makes them exist."""
    E = [{y: [P.contrae(r, y) for r in K[i]] for y in T3} for i in range(len(GRUPOS))]
    t0, n = time.time(), 0
    while time.time() - t0 < tope:
        i = rng.randrange(len(GRUPOS))
        triv = P.triv[i]
        real = K[i][len(triv):]
        if not real or len(K[i]) >= len(P.N[i]):
            continue
        before = sum(_dimensiones(P, K, i, E).values())
        t = rng.randrange(len(real))
        out = real[t]
        rest = [x ^ out if rng.random() < 0.5 else x for k, x in enumerate(real) if k != t]
        v = 0
        for b in P.N[i]:
            if rng.random() < 0.5:
                v ^= b
        new = triv + rest + [v]
        piv = {}
        ok = True
        for r in new:
            red = tq._reduce(r, piv)
            if not red:
                ok = False
                break
            piv[red.bit_length() - 1] = red
        if not ok:
            continue
        old, oldE = K[i], E[i]
        K[i], E[i] = new, {y: [P.contrae(r, y) for r in new] for y in T3}
        if sum(_dimensiones(P, K, i, E).values()) < before:
            K[i], E[i] = old, oldE
        else:
            n += 1
    return n


def buscar(P, rng, tope=600.0, log=None):
    K = [list(t) for t in P.triv]
    ind = [dict() for _ in GRUPOS]
    for i in range(len(GRUPOS)):
        for r in K[i]:
            ind[i][r.bit_length() - 1] = r
    best = elegir(P, K, rng)
    assert best is not None
    t0, fallos = time.time(), 0
    order = list(range(len(GRUPOS)))
    while time.time() - t0 < tope:
        if fallos >= PACIENCIA:
            if RECOCIDO <= 0:
                break
            n = recocer(P, K, rng, RECOCIDO)
            ind = [dict() for _ in GRUPOS]
            for i in range(len(GRUPOS)):
                for r in K[i]:
                    red = tq._reduce(r, ind[i])
                    ind[i][red.bit_length() - 1] = red
            r = elegir(P, K, rng)
            if log:
                log(f"recocido: {n} cambios, ahora {r[0] if r else None}, mejor {best[0]}, relaciones {[len(k) for k in K]}, {time.time()-t0:.0f} s")
            if r is not None and r[0] < best[0]:
                best = r
            fallos = 0
        rng.shuffle(order)
        i = order[0]
        pool = []
        for _ in range(MUESTRA):
            v = 0
            for b in P.N[i]:
                if rng.random() < 0.5:
                    v ^= b
            if tq._reduce(v, ind[i]):
                pool.append(v)
        if not pool:
            fallos += 1
            continue
        scored = []
        for v in pool:                               # cheap screen: candidates left when v enters
            K2 = K[:i] + [K[i] + [v]] + K[i + 1:]
            scored.append((-soluciones(P, K2, rng, 1)[2], v))
        scored.sort(key=lambda t: t[0])
        top = None
        for _, v in scored[:FINOS]:
            K2 = K[:i] + [K[i] + [v]] + K[i + 1:]
            r = elegir(P, K2, rng)
            if r is not None and (top is None or r[0] < top[0][0]):
                top = (r, v)
        if top is None or top[0][0] > best[0] + 1:
            fallos += 1
            continue
        v = top[1]
        K[i] = K[i] + [v]
        red = tq._reduce(v, ind[i])
        ind[i][red.bit_length() - 1] = red
        if top[0][0] < best[0]:
            best, fallos = top[0], 0
            if log:
                log(f"{best[0]} productos, relaciones {[len(k) for k in K]}, {time.time()-t0:.0f} s")
        else:
            fallos += 1
    return best, K


def terminos(P, sel):
    """The (a1, b1, a2, b2, s) terms of tensorqrom from a selection of features."""
    _, picked, singles = sel
    feats = [[] for _ in GRUPOS]                     # (id, flat)
    prods = []
    for i, y, j, y2, s in picked:
        k = len(prods)
        prods.append([s, (i, y), (j, y2)])
        feats[i].append((k, 1, P.flat(y, s)))
        feats[j].append((k, 2, P.flat(y2, s)))
    for i, y, s in singles:
        k = len(prods)
        prods.append([s, (i, y), None])
        feats[i].append((k, 1, P.flat(y, s)))
    high = {}
    for i in range(len(GRUPOS)):
        vecs = [f[2] for f in feats[i]]
        co = tq.express(P.rows[i], vecs)
        for n, (k, side, _) in enumerate(feats[i]):
            high[(k, side)] = sum(1 << r for r in range(P.H) if co[r] >> n & 1)

    def low(g, y):
        return sum(1 << (GRUPOS[g][p] - 1) for p in range(3) if y >> p & 1)

    out = []
    for k, (s, f1, f2) in enumerate(prods):
        a1, b1 = low(*f1), high[(k, 1)]
        a2, b2 = (low(*f2), high[(k, 2)]) if f2 else (0, 0)
        if a1 and b1 and a2 and b2:
            out.append((a1, b1, a2, b2, s))
        elif a1 and b1:
            out.append((a1, b1, 0, 0, s))
        elif a2 and b2:
            out.append((a2, b2, 0, 0, s))
    return out


def plan(C, seed=0, tope=600.0, log=None):
    """Terms of one circuit from its tensor C (16, H, O)."""
    P = Problema(C)
    best, K = buscar(P, random.Random(seed), tope, log)
    return terminos(P, best)


if __name__ == "__main__":
    sys.path.insert(0, (_HOME + "/compiler"))
    import rmcode
    from fourqrom import batch_deltas
    src, k = sys.argv[1], int(sys.argv[2])
    tope = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
    with np.load(src) as z:
        words, deg = z["angle_words"].astype(np.int64), z["codes"].astype(np.int64)
    d = rmcode.pad(list(batch_deltas(words, 5))[k], rmcode.output_degrees(deg, k, 5, 8), 8)
    C = tq.anf_tensor(d, 8, 4)
    t0 = time.time()
    t = plan(C, k, tope, lambda *x: print(*x, flush=True))
    L, H, O = C.shape
    ok = np.array_equal(tq.mixed_of(t, L - 1, H - 1, O), C[1:, 1:])
    print(f"circuito {k}: {len(t)} productos, cubre el tensor {ok}, {time.time()-t0:.0f} s", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
