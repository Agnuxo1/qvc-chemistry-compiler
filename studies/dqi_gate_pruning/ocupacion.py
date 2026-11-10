# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Ocupación por qubit en tramos: qubits que nunca (o casi nunca) valen 1 en un tramo no llevan información.
import numpy as np, glob, sys
files = sorted(glob.glob(sys.argv[1] + '_s*_seg.npy'))
S = sum(np.load(f).astype(np.int64) for f in files); N = 32768 * len(files)
occ = S[:, :892]; live_max = S[:, 892] // len(files)
print('archivos', len(files), 'disparos', N, 'tramos', len(S))
for thr in (0, 1, 5, 50):
    w = (occ > thr).sum(1)
    print(f'umbral {thr:3d} disparos (p<={thr/N:.1e}): ancho con información máx {w.max()}  tramos con ancho>=891: {(w>=891).sum()}  ==892: {(w==892).sum()}')
w0 = (occ > 0).sum(1)
print('vivos estáticos máx', live_max.max(), ' tramos con 892 vivos', (live_max == 892).sum())
# en los tramos de ancho máximo, qubits menos ocupados
top = np.argsort(-w0)[:5]
for t in top:
    o = occ[t]; lo = np.argsort(o)[:8]
    print('tramo', t, 'ancho', w0[t], 'vivos', live_max[t], 'menos ocupados', [(int(q), int(o[q])) for q in lo])
np.save(sys.argv[1] + '_ancho.npy', w0)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
