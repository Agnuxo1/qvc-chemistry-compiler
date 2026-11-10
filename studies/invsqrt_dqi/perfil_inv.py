# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Perfil de qubits vivos en invsqrt: un qubit esta libre desde HMR/R hasta su siguiente uso no-R
import re,collections
L=[l for l in open('invsqrt.kmx').read().split('\n') if l and not l.startswith(('APPEND','REGISTER'))]
N=len(L)
ins=[]
for l in L:
    t=l.split()
    op=t[0]
    qs=[int(a[1:]) for a in t[1:] if a[0]=='q']
    ins.append((op,qs,l))
# vida: un qubit esta 'vivo' si desde este punto hasta su proxima R/HMR-ultimo ... usamos: vivo entre primer toque tras limpiar y HMR/R que lo limpia
live=set(range(22))
cnt=[]
hist=[]
# dos pasadas: ultima operacion antes de un HMR/R marca fin
for i,(op,qs,l) in enumerate(ins):
    if op in('R','HMR'):
        for q in qs:
            live.discard(q)
    else:
        if op in('PUSH_CONDITION','POP_CONDITION','BIT_STORE0','BIT_STORE1','BIT_INVERT','NEG'):
            pass
        else:
            for q in qs: live.add(q)
    cnt.append(len(live))
import numpy as np
c=np.array(cnt)
print('N',N,'max',c.max())
for a in range(0,N,1500):
    print(a,c[a:a+1500].min(),c[a:a+1500].max(),round(c[a:a+1500].mean(),1), 'tof',sum(1 for o,_,_ in ins[a:a+1500] if o in('CCX','CCZ','CSWAP')))
print('puntos con 62:',(c==62).sum(),'61:',(c==61).sum(),'60:',(c==60).sum())

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
