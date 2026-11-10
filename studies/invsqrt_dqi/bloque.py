# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Separa unextract en tramos y analiza un tramo grande: palabras destino, palabras fuente, simetria espejo
import sys,collections
a,b=52196368,57991164
tr=[];cum=0;last=-1;cur=[];lines=[]
blocks=[]  # (linea_ini, linea_fin, ops)
ops=[];start=a
with open('dqi.kmx') as f:
    for i,l in enumerate(f,1):
        if i<a: continue
        if i>b: break
        h=l[:3]
        if h in('CCX','CCZ','CSW'):
            t=l.split()
            ops.append((t[0],int(t[1][1:]),int(t[2][1:]),int(t[3][1:]),i))
            cum+=1
        elif h=='HMR':
            q=int(l.split()[1][1:])
            if q<840:
                if cum-last>40:
                    blocks.append((start,i,ops)); ops=[]; start=i
                last=cum
blocks.append((start,b,ops))
print(len(blocks),[len(x[2]) for x in blocks[:24]])
def w(q): return q//12 if q<840 else 'a'
import json
def resumen(k):
    s,e,o=blocks[k]
    tg=collections.Counter(w(x[3]) for x in o)
    src=collections.Counter()
    for x in o: src[w(x[1])]+=1; src[w(x[2])]+=1
    print('bloque',k,'lineas',s,e,'ops',len(o))
    print(' destinos',tg.most_common(14))
    print(' fuentes',src.most_common(14))
    # espejo: compara primera mitad con segunda invertida
    h=len(o)//2
    A=[x[:4] for x in o[:h]]; B=[x[:4] for x in o[::-1][:h]]
    print(' iguales espejo',sum(1 for p,q in zip(A,B) if p==q),'de',h)
    c=collections.Counter(x[:4] for x in o)
    print(' triples repetidos',sum(v for v in c.values() if v>1),'distintos',len(c))
for k in (12,15,21,24): resumen(k)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
