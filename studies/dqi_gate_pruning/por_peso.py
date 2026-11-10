# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Peso máximo y mínimo con actividad por puerta, a partir de corridas ordenadas por peso.
import numpy as np, json, sys, glob
runs = sorted(glob.glob('act/peso256_s*.npy')); runs = [r for r in runs if not r.endswith('_pesos.npy')]
F = np.load('fases_ord.npz'); fase = F['fase']; hoja = F['hoja']
meta = json.load(open('fases_ord.json')); top = meta['top']
ref = json.load(open('tabla_k.json'))
# distribución oficial de pesos
import math
m, l, q, r = 4095, 35, 4096, 2016
k = np.arange(l + 1.); off = np.sqrt(k[1:] * (m - k[1:] + 1)); d = (q - 2 * r) / math.sqrt(r * (q - r))
_, v = np.linalg.eigh(np.diag(k * d) + np.diag(off, 1) + np.diag(off, -1)); w = np.abs(v[:, -1]); w /= np.linalg.norm(w); p = w ** 2
cum = np.cumsum(p)
wmax = np.full(395679, -1); wmin = np.full(395679, 99); act_tot = np.zeros(395679, np.int64)
for f in runs:
    R = np.load(f); W = np.load(f[:-4] + '_pesos.npy')
    hi = R[:, 5]; lo = R[:, 6]
    a = hi > 0
    wmax[a] = np.maximum(wmax[a], W[hi[a] - 1]); wmin[a] = np.minimum(wmin[a], W[lo[a] - 1])
    act_tot += R[:, 1]
print('corridas', runs)
print('nunca activas en ningún peso:', int((wmax < 0).sum()))
u, c = np.unique(fase[wmax < 0], return_counts=True); print('  por fase', {top[i]: int(x) for i, x in zip(u, c)})
print(' T0  puertas(wmax<=T0)  P(peso<=T0)  k_esperado')
out = []
for T0 in range(-1, 36):
    n = int((wmax <= T0).sum()); pt = cum[T0] if T0 >= 0 else 0.0
    out.append(dict(T0=T0, puertas=n, p=pt, k=pt * 102400))
    print(f'{T0:3d} {n:8d} {pt:12.3e} {pt*102400:10.3f}')
np.savez('por_peso.npz', wmax=wmax, wmin=wmin)
json.dump(out, open('por_peso.json', 'w'), indent=0)
# por fase para T0 = 20
for T0 in (17, 18, 19, 20, 22):
    sel = wmax <= T0
    u, c = np.unique(fase[sel], return_counts=True); print(T0, {top[i]: int(x) for i, x in zip(u, c)})

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
