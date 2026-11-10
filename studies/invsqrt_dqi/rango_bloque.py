# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Forma cuadrática exacta de un bloque de dqi.kmx: rango decide si los términos comparten factor.
# Uso: rango_bloque.py linea_inicio linea_fin palabra_primera palabra_ultima
import json, random, sys

a, b, w_first, w_last = (int(x) for x in sys.argv[1:5])
L = []
with open('dqi.kmx') as f:
    for i, l in enumerate(f, 1):
        if i < a:
            continue
        if i > b:
            break
        L.append(l.rstrip())


def word(l):
    for x in l.split()[1:3]:
        q = int(x[1:])
        if q < 840:
            return q // 12
    return None


first = next(i for i, l in enumerate(L) if l.startswith('CCX') and word(l) == w_first)
last = max(i for i, l in enumerate(L) if l.startswith('CCX') and word(l) == w_last)
# incluye los CX previos que preparan el primer término y los posteriores que deshacen formas
s = first
while s > 0 and L[s - 1].split()[0] in ('CX', 'SWAP'):
    s -= 1
e = last + 1
while e < len(L) and L[e].split()[0] in ('CX', 'SWAP'):
    e += 1
seg = L[s:e]
ops = []
for l in seg:
    t = l.split()
    ops.append((t[0], [int(x[1:]) for x in t[1:] if x[0] == 'q']))
kinds = {}
for o, _ in ops:
    kinds[o] = kinds.get(o, 0) + 1
print('tramo', s + a, e + a, kinds)
wires = sorted({q for _, qs in ops for q in qs})
n = len(wires)
print('cables', n, 'palabras S', len({q // 12 for q in wires if q < 840}), 'auxiliares', sum(1 for q in wires if q >= 840))


def run(v):
    v = dict(v)
    for o, q in ops:
        if o == 'CX':
            v[q[1]] ^= v[q[0]]
        elif o == 'CCX':
            v[q[2]] ^= v[q[0]] & v[q[1]]
        elif o == 'SWAP':
            v[q[0]], v[q[1]] = v[q[1]], v[q[0]]
        elif o == 'X':
            v[q[0]] ^= (1 << 4096) - 1
    return v


# qué cables cambian de valor neto
rng = random.Random(1)
v0 = {q: rng.getrandbits(4096) for q in wires}
v1 = run(v0)
changed = [q for q in wires if v0[q] != v1[q]]
print('cambian', len(changed), sorted({(q // 12 if q < 840 else 'a') for q in changed}, key=str))

# una ejecución con enteros de muchos bits: posición 0 = cero, 1..n = sencillos, resto = parejas
idx = {q: i for i, q in enumerate(wires)}
pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
W = 1 + n + len(pairs)
print('asignaciones', W)
vec = [0] * n
for i in range(n):
    vec[i] |= 1 << (1 + i)
base = 1 + n
bits = [bytearray((W + 7) // 8) for _ in range(n)]
for k, (i, j) in enumerate(pairs):
    p = base + k
    bits[i][p >> 3] |= 1 << (p & 7)
    bits[j][p >> 3] |= 1 << (p & 7)
init = {q: vec[idx[q]] | int.from_bytes(bits[idx[q]], 'little') for q in wires}
del bits
out = run(init)
res = {}
for t in changed:
    d = out[t] ^ init[t]
    res[t] = d
# forma cuadrática de cada salida
rows_by_t = {}
for t in changed:
    d = res[t]
    db = d.to_bytes((W + 7) // 8, 'little')

    def g(p):
        return (db[p >> 3] >> (p & 7)) & 1

    f0 = g(0)
    fi = [g(1 + i) for i in range(n)]
    M = [0] * n
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if g(base + k) ^ fi[i] ^ fi[j] ^ f0:
                M[i] |= 1 << j
                M[j] |= 1 << i
            k += 1
    rows_by_t[t] = M


def rank(rows):
    basis = {}
    r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                r += 1
                break
    return r


ranks = {t: rank(M) for t, M in rows_by_t.items()}
print('rango por salida (forma simétrica; producto simple = 2):', sorted(ranks.values()))
acc = [0] * n
for t, M in rows_by_t.items():
    if rng.random() < .5:
        acc = [x ^ y for x, y in zip(acc, M)]
print('rango de una combinación aleatoria de salidas:', rank(acc))
# soporte: cables que intervienen en algún término cuadrático
sup = 0
for M in rows_by_t.values():
    for i, r in enumerate(M):
        if r:
            sup |= 1 << i
act = [wires[i] for i in range(n) if (sup >> i) & 1]
print('cables con término cuadrático', len(act), 'S', len({q // 12 for q in act if q < 840}), 'aux', sum(1 for q in act if q >= 840))
json.dump({'tramo': [s + a, e + a], 'ranks': sorted(ranks.values()), 'cambian': changed}, open('rango_bloque.json', 'w'))

# prueba decisiva: dimension del espacio conjunto de formas lineales
def grupo(nombre, ts):
    rows = []
    for t in ts:
        rows += rows_by_t[t]
    print(nombre, 'salidas', len(ts), 'dimension conjunta de formas', rank(rows))
    return rows

gS = [t for t in changed if t < 840]
gA = [t for t in changed if t >= 840]
r1 = grupo('palabras destino', gS)
r2 = grupo('auxiliares', gA)
print('ambos', rank(r1 + r2))
# formas entre si: dimension del espacio de formas cuadraticas
def flat(M):
    v = 0
    for i, r in enumerate(M):
        v |= r << (i * n)
    return v
print('dim espacio de formas, destino', rank([flat(rows_by_t[t]) for t in gS]), 'aux', rank([flat(rows_by_t[t]) for t in gA]), 'todas', rank([flat(rows_by_t[t]) for t in changed]))
# restringe las formas a la parte S x S y S x aux
auxmask = sum(1 << i for i, q in enumerate(wires) if q >= 840)
Smask = ((1 << n) - 1) ^ auxmask
xx = sum(1 for t in changed for i, r in enumerate(rows_by_t[t]) if wires[i] < 840 and r & Smask)
print('filas con termino S*S', xx)
rowsS = [r & auxmask for t in changed for i, r in enumerate(rows_by_t[t]) if wires[i] < 840]
rowsA = [r & Smask for t in changed for i, r in enumerate(rows_by_t[t]) if wires[i] >= 840]
print('dim formas en aux', rank(rowsS), 'dim formas en S (Y)', rank(rowsA))

# ¿grado 2 de verdad? compara con entradas aleatorias en todas las salidas
B = 1024
MASK = (1 << B) - 1
vr = {q: rng.getrandbits(B) for q in wires}
orr = run(vr)
malos = 0
for t in changed[:8] + changed[-8:]:
    d = res[t]
    db = d.to_bytes((W + 7) // 8, 'little')
    g = lambda p: (db[p >> 3] >> (p & 7)) & 1
    f0 = g(0)
    pred = MASK if f0 else 0
    fi = [g(1 + i) for i in range(n)]
    for i in range(n):
        if fi[i] ^ f0:
            pred ^= vr[wires[i]]
    M = rows_by_t[t]
    for i in range(n):
        r = M[i] >> (i + 1)
        j = i + 1
        acc2 = 0
        while r:
            if r & 1:
                acc2 ^= vr[wires[j]]
            r >>= 1
            j += 1
        pred ^= vr[wires[i]] & acc2
    real = orr[t] ^ vr[t]
    dif = bin(pred ^ real).count('1')
    malos += dif > 0
    print('salida', t, 'difieren', dif, 'de', B)
print('salidas con grado mayor que 2:', malos)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
