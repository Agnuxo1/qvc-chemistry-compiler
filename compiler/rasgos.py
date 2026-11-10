# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Derived from tensorqrom.py by marculera/Lera (Apache-2.0); preserve upstream notices.
# Open source (Apache-2.0): retain both upstream and project attribution.
"""Free features in the top bit of each word, and the circuits that use them.

A row of the table is a unit vector, so its angles have a gauge: moving an edge by pi and negating the angles that
follow leaves the vector unchanged up to sign. That makes the flag bit7 XOR bit6 of every word free, at no error and
keeping bit 0. Setting it to a monomial of the address on one word column makes that monomial already available in the
register at the start of the next circuit, by one CNOT, instead of costing an AND in every circuit. The trick is read
from the public 24.94 circuits; this code and the schedule below are ours. The builder is tensorqrom.build_circuit
(marculera, Apache-2.0) with the three word modes added.

Word modes in circuit k: `scratch` before the word starts (top bit equals bit 6, borrowed as a cache qubit), `change`
at its first batch (the top bit is an output, plus the feature), and `free` afterwards (the top bit holds the feature).
Only two words change per circuit: a word in `change` lends no qubit, and the cache must stay within the 128-qubit cap.
"""
import numpy as np
import tensorqrom as tq
from tensorqrom import _bits, _bits_vec, _monomial_values, anf_tensor, km, mixed_of, mobius

J, BROT, LOW = 5, 8, 4
MASK = {4: 5, 3: 6, 2: 7, 1: 9, 0: 10}     # high monomial of each word; all vanish on the one-body rows, so those keep their gauge
START = {4: 0, 3: 0, 2: 1, 1: 1, 0: 2}     # first batch of each word


def feature(addr, mask):
    """Value of a high monomial on addresses."""
    high = np.asarray(addr, np.int64) >> LOW
    return ((high & mask) == mask).astype(bool)


def flags(rows, cols):
    """The wanted bit7 XOR bit6 of the table: (rows, cols)."""
    addr = np.arange(rows)
    out = np.zeros((rows, cols), bool)
    for col in range(cols):
        k, w = divmod(col, J)
        if k >= START[w]:
            out[:, col] = feature(addr, MASK[w])
    return out


def poner(words, edges, want, brot=BROT):
    """The same vectors up to sign with the flag of every word equal to `want`; bit 0 does not move (exact, integer).

    As onebody.signed_gauge, walking the tree backwards: a node whose sign was flipped negates the angle that mixes it
    in, and an angle with the wrong flag moves by pi, which flips its first node.
    """
    mod = 1 << brot
    half, quarter = mod >> 1, mod >> 2
    out = np.asarray(words, np.int64).copy() % mod
    sign = np.ones((len(out), edges.shape[0] + 1), np.int8)
    for k in reversed(range(edges.shape[0])):
        p, q = edges[k]
        a = np.where(sign[:, p] != sign[:, q], (-out[:, k]) % mod, out[:, k])
        flip = ((a >= quarter) & (a < 3 * quarter)) != want[:, k]
        out[:, k] = np.where(flip, (a + half) % mod, a)
        sign[flip, p] *= -1
        sign[:, q] = 1
    return out


def modos(k):
    return {w: "scratch" if k < START[w] else "change" if k == START[w] else "free" for w in range(J)}


def build_circuit(delta, terms, n_sel, k, rows):
    """tensorqrom.build_circuit for circuit k with the word modes above; `rows` is the length of the real table."""
    brot, lowbits = BROT, LOW
    mode = modos(k)
    delta = np.asarray(delta, dtype=np.int64)
    count, nj = delta.shape
    addr = np.arange(rows)
    for w, m in mode.items():
        want = feature(addr, MASK[w]) if m == "change" else np.zeros(rows, bool)
        got = (((delta[:rows, w] >> (brot - 1)) ^ (delta[:rows, w] >> (brot - 2))) & 1).astype(bool)
        assert np.array_equal(got, want), f"word {w} of circuit {k}: top bit does not follow its mode {m}"
    C = anf_tensor(delta, brot, lowbits)
    L, H, O = C.shape
    assert np.array_equal(mixed_of(terms, L - 1, H - 1, O), C[1:, 1:]), "decomposition does not cover the tensor"

    low = C[:, 0].copy()
    high = C[0].copy()
    high[0] = 0
    vl, vh = _monomial_values(L, L), _monomial_values(H, H)
    hb = max(1, (H - 1).bit_length())
    for a1, b1, a2, b2, s in terms:
        outs = np.array(_bits(s))
        if a2:
            pl = mobius((vl @ np.array(_bits_vec(a1, L - 1)) & 1) & (vl @ np.array(_bits_vec(a2, L - 1)) & 1))
            low[:, outs] ^= pl[:, None]
        if b2:
            th = np.zeros(1 << hb, np.uint8)
            th[:H] = (vh @ np.array(_bits_vec(b2, H - 1)) & 1) & (vh @ np.array(_bits_vec(b1, H - 1)) & 1)
            ph = mobius(th)[:H]
            high[:, outs] ^= ph[:, None]
    low[0] ^= high[0]
    high[0] = 0

    b = km.CircuitBuilder()
    sel = b.create_quantum_register(n_sel, "selection")
    words = [b.create_quantum_register(brot, f"word_{j}") for j in range(nj)]
    kept = [w for w in range(nj) if mode[w] != "change"]
    for w in kept:                                   # clears a scratch top bit, and leaves the feature on a free one
        b.cx(words[w][brot - 2], words[w][brot - 1])
    outputs = [[words[j][i]] + ([words[j][brot - 1]] if i == brot - 2 and mode[j] == "change" else [])
               for j in range(nj) for i in range(brot - 1)]
    pool = [words[w][brot - 1] for w in range(nj) if mode[w] == "scratch"]
    free = {MASK[w]: words[w][brot - 1] for w in range(nj) if mode[w] == "free"}
    borrowed = []

    def take():
        if pool:
            borrowed.append(pool[-1])
            return pool.pop()
        return b.alloc_qubits(1)[0]

    def give(t):
        if any(t is q for q in borrowed):
            borrowed[:] = [q for q in borrowed if q is not t]
            pool.append(t)
        else:
            b.free(t)

    def cache(size, offset, made, given):
        q = {}
        for mask in range(1, size):
            top = mask.bit_length() - 1
            if mask == 1 << top:
                q[mask] = sel[offset + top]
            elif mask in given:
                q[mask] = given[mask]
            else:
                t = take()
                b.init_and(q[mask ^ (1 << top)], sel[offset + top], t)
                q[mask] = t
                made.append((q[mask ^ (1 << top)], sel[offset + top], t))
        return q

    made = []
    Y = cache(H, lowbits, made, free)
    X = cache(L, 0, made, {})

    def qubit(q):
        return X[q + 1] if q < L - 1 else Y[q - L + 2]

    def targets(s):
        return [q for o in s for q in outputs[o]]

    def fan_ccx(c1, c2, ts):
        first, rest = ts[0], ts[1:]
        for t in rest:
            b.cx(first, t)
        b.ccx(c1, c2, first)
        for t in reversed(rest):
            b.cx(first, t)

    def product(a1, b1, a2, b2, s):
        m1, m2 = a1 | (b2 << (L - 1)), a2 | (b1 << (L - 1))
        if not m1 or not m2 or m1 == m2:
            return
        p1 = _bits(m1)[0]
        ops = [(q, p1) for q in _bits(m1) if q != p1]
        if m2 >> p1 & 1:
            m2 ^= m1 ^ (1 << p1)
        p2 = next(q for q in _bits(m2) if q != p1)
        ops += [(q, p2) for q in _bits(m2) if q != p2]
        for src, dst in ops:
            b.cx(qubit(src), qubit(dst))
        fan_ccx(qubit(p1), qubit(p2), targets(_bits(s)))
        for src, dst in reversed(ops):
            b.cx(qubit(src), qubit(dst))

    for t in terms:
        product(*t)
    for m in range(L):
        ts = targets(np.flatnonzero(low[m]))
        if ts:
            if m == 0:
                b.x(km.array(ts))
            else:
                b.cx(X[m], km.array(ts))
    for m in range(1, H):
        ts = targets(np.flatnonzero(high[m]))
        if ts:
            b.cx(Y[m], km.array(ts))
    for w in range(nj):
        if mode[w] == "change":                      # the new word's flag, once, from the cached monomial
            b.cx(Y[MASK[w]], words[w][brot - 1])

    for c1, c2, t in reversed(made):
        b.del_and(c1, c2, t)
        give(t)
    for w in kept:
        b.cx(words[w][brot - 2], words[w][brot - 1])
    return b.finish_circuit()


__all__ = ["build_circuit", "flags", "modos", "poner", "tq"]

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: Apache-2.0 :: preserve upstream and project notices
