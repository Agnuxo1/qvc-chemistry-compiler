# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Clasifica las puertas Toffoli-like por actividad observada en uno o varios registros act/*.npy
import numpy as np, json, sys, glob
files = sys.argv[1:]
R = sum(np.load(f).astype(np.int64) for f in files)
F = np.load('fases_ord.npz'); fase = F['fase']; hoja = F['hoja']
meta = json.load(open('fases_ord.json')); top = meta['top']; hojas = {v: k for k, v in meta['hojas'].items()}
nm, act, c1, c2, eq = R.T
N = nm.max()
print('disparos', N, 'puertas', len(nm))
ex = nm > 0
dead = ex & (act == 0)
one1 = ex & (c1 == nm) & ~dead
one2 = ex & (c2 == nm) & ~dead & ~one1
same = ex & (eq == nm) & ~dead & ~one1 & ~one2
rare = ex & (act > 0) & (act <= max(1, N // 1000))
always = ex & (act == nm)
print('ejecutadas', ex.sum(), 'muertas', dead.sum(), 'ctrl1=1', one1.sum(), 'ctrl2=1', one2.sum(), 'iguales', same.sum(), 'raras(<=0.1%)', rare.sum(), 'siempre', always.sum())
for nmf, msk in [('muertas', dead), ('ctrl1', one1), ('ctrl2', one2), ('iguales', same), ('raras', rare)]:
    print('==', nmf)
    u, c = np.unique(fase[msk], return_counts=True)
    print('  por fase', {top[i] if i >= 0 else '-': int(x) for i, x in zip(u, c)})
    u, c = np.unique(hoja[msk], return_counts=True)
    print('  por hoja', {hojas[i] or '<fase>': int(x) for i, x in sorted(zip(u, c), key=lambda t: -t[1])[:8]})
# histograma de actividad relativa
fr = act[ex] / nm[ex]
print('hist actividad', np.histogram(fr, bins=[0, 1e-9, 1e-3, 0.01, 0.1, 0.2, 0.3, 0.4, 0.6, 0.9, 1 - 1e-9, 1.01])[0].tolist())
np.savez('clases.npz', dead=dead, one1=one1, one2=one2, same=same, rare=rare)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
