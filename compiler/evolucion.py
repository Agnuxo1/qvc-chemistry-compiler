# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Evolutionary search of the relation sets of bajos.py, after the author's "Darwin cage" idea: start from noise and a few greedy
solutions, keep what reaches the reference points (here: every row covered with the fewest products), and let selection
find a rule nobody wrote down.

An individual is the five relation lists K (one per low triple). Fitness: products of the best greedy pairing of K
(bajos.elegir), infeasible sets lose. Crossover takes each triple's K from one parent, since triples only interact through
the pairs; mutation swaps, adds or drops one relation of one triple. Usage: evolucion.py <table.npz> <circuit> [seconds]
"""
import os
import random
import sys
import time

import numpy as np
import tensorqrom as tq

import bajos

POB, TORNEO = (int(os.environ.get(k, v)) for k, v in (("QVC_EP", 16), ("QVC_ET", 3)))
INF = 10 ** 9


def coste(P, K, rng):
    r = bajos.elegir(P, K, rng)
    return (INF, None) if r is None else (r[0], r)


def independiente(P, i, K):
    piv = {}
    for r in K:
        red = tq._reduce(r, piv)
        if not red:
            return False
        piv[red.bit_length() - 1] = red
    return True


def mutar(P, K, rng):
    K = [list(k) for k in K]
    for _ in range(20):
        i = rng.randrange(len(bajos.GRUPOS))
        triv = P.triv[i]
        real = K[i][len(triv):]
        op = rng.random()
        if real:                                       # a random change of basis first, so any relation can leave
            piv = real[rng.randrange(len(real))]
            real = [x ^ piv if rng.random() < 0.5 and x != piv else x for x in real]
        v = 0
        for b in P.N[i]:
            if rng.random() < 0.5:
                v ^= b
        if op < 0.5 and real:
            new = real[:]
            new[rng.randrange(len(new))] = v
        elif op < 0.8 and len(K[i]) < len(P.N[i]):
            new = real + [v]
        elif real:
            new = real[:]
            new.pop(rng.randrange(len(new)))
        else:
            continue
        cand = triv + new
        if independiente(P, i, cand):
            K[i] = cand
            return K
    return K


def cruzar(A, B, rng):
    return [list(a if rng.random() < 0.5 else b) for a, b in zip(A, B)]


def evolucionar(P, rng, tope, semillas, log=print):
    t0 = time.time()
    pob = []
    for K in semillas:
        c, sel = coste(P, K, rng)
        pob.append((c, K, sel))
    while len(pob) < POB:                              # noise: mutants of the seeds, several steps away
        K = rng.choice(pob)[1]
        for _ in range(rng.randrange(1, 6)):
            K = mutar(P, K, rng)
        c, sel = coste(P, K, rng)
        pob.append((c, K, sel))
    pob.sort(key=lambda x: x[0])
    gen = 0
    while time.time() - t0 < tope:
        hijos = []
        for _ in range(POB):
            a = min(rng.sample(pob, TORNEO), key=lambda x: x[0])
            b = min(rng.sample(pob, TORNEO), key=lambda x: x[0])
            K = cruzar(a[1], b[1], rng) if rng.random() < 0.5 else [list(k) for k in a[1]]
            for _ in range(rng.randrange(1, 3)):
                K = mutar(P, K, rng)
            c, sel = coste(P, K, rng)
            hijos.append((c, K, sel))
        pob = sorted(pob + hijos, key=lambda x: x[0])[:POB]
        gen += 1
        if log and gen % 5 == 0:
            log(f"generación {gen}: mejor {pob[0][0]}, mediana {pob[POB // 2][0]}, relaciones {[len(k) for k in pob[0][1]]}, {time.time()-t0:.0f} s")
    return pob[0]


if __name__ == "__main__":
    import rmcode
    from fourqrom import batch_deltas
    src, k = sys.argv[1], int(sys.argv[2])
    tope = float(sys.argv[3]) if len(sys.argv) > 3 else 900.0
    with np.load(src) as z:
        words, deg = z["angle_words"].astype(np.int64), z["codes"].astype(np.int64)
    d = rmcode.pad(list(batch_deltas(words, 5))[k], rmcode.output_degrees(deg, k, 5, 8), 8)
    C = tq.anf_tensor(d, 8, 4)
    P = bajos.Problema(C)
    say = lambda *x: print(*x, flush=True)  # noqa: E731
    semillas = []
    for s in range(3):
        best, K = bajos.buscar(P, random.Random(100 + s), 90.0)
        semillas.append(K)
        say(f"semilla {s}: {best[0]} productos")
    c, K, sel = evolucionar(P, random.Random(k), tope, semillas, say)
    t = bajos.terminos(P, sel)
    L, H, O = C.shape
    ok = np.array_equal(tq.mixed_of(t, L - 1, H - 1, O), C[1:, 1:])
    say(f"circuito {k}: {len(t)} productos tras evolución, cubre el tensor {ok}")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
