# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Programa a nivel de palabra de una fase: runs de CCX con (palabra control1, control2, destino)
import sys,json,collections
a,b=int(sys.argv[1]),int(sys.argv[2])
def w(q):
    q=int(q[1:])
    return q//12 if q<840 else 'a%d'%(q-840)
runs=[];cur=None;n=0
with open('dqi.kmx') as f:
    for i,l in enumerate(f,1):
        if i<a: continue
        if i>b: break
        if l.startswith('CCX'):
            t=l.split()
            k=tuple(sorted(map(str,(w(t[1]),w(t[2]))))) + ('->',str(w(t[3])))
            if k!=cur:
                if cur: runs.append((cur,n))
                cur=k;n=0
            n+=1
runs.append((cur,n))
print(len(runs))
c=collections.Counter(n for k,n in runs)
print(sorted(c.items(),key=lambda kv:-kv[1])[:15])
print(runs[:int(sys.argv[3])])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
