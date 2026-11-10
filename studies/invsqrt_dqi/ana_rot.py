# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import numpy as np
from fractions import Fraction
d=np.load('rot_bits.npz')
n=int(d['n']); N=3133452
bits=np.unpackbits(d['bits'],axis=1)[:,:n].astype(bool)[:,:N]
ang=[str(a) for a in d['ang']]
a=np.array([float(Fraction(s)) for s in ang])/2
xs=np.arange(1,N+1)
ex=np.floor(np.log2(xs)).astype(int)  # exponente
hi=list(range(3,19)); lo=list(range(22,48))
th=1/np.sqrt(xs)
H=(a[hi]@bits[hi].astype(float)); Lw=(a[lo]@bits[lo].astype(float))
print('exp  n   media hi/theta  media lo/theta  min lo/theta max lo/theta  bits hi activos   bits lo activos')
for e in range(0,22):
    m=ex==e
    act_h=[i for i,k in enumerate(hi) if bits[k][m].any()]
    act_l=[i for i,k in enumerate(lo) if bits[k][m].any()]
    print(e,m.sum(),round((H[m]/th[m]).mean(),4),round((Lw[m]/th[m]).mean(),6),round((Lw[m]/th[m]).min(),6),round((Lw[m]/th[m]).max(),6),(min(act_h),max(act_h),len(act_h)) if act_h else None,(min(act_l),max(act_l),len(act_l)) if act_l else None)
# los primeros: bits 0..2 y 19..21
for k in (0,1,2,19,20,21):
    print(k,ang[k],bits[k].mean())
# bits 0,1,2 vs 19,20,21
print((bits[0]^bits[19]).mean(),(bits[1]^bits[20]).mean(),(bits[2]^bits[21]).mean())

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
