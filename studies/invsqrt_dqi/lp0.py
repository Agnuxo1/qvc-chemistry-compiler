# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import numpy as np, math
from fractions import Fraction
d=np.load('rot_bits.npz')
n=int(d['n']); N=3133452
K=d['bits'].shape[0]
bits=np.unpackbits(d['bits'],axis=1)[:,:n].astype(bool)[:,:N]
resid=d['resid'][:N]
ang=[Fraction(a) if False else a for a in d['ang']]
lines=d['lines'];qs=d['qs'];cond=d['cond']
print(K,bits.mean(1).round(3))
# angulos en vueltas: Z_POW exponent en medias vueltas -> vueltas = e/2
ang_f=[float(a)/2 for a in ang]
print([ (int(l),int(q),a[:14],int(c)) for l,q,a,c in zip(lines,qs,ang,cond)][:50])
xs=np.arange(1,N+1,dtype=np.float64)
tgt=1/np.sqrt(xs)
print('resid distintos',len(np.unique(resid)),np.unique(resid)[:5])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
