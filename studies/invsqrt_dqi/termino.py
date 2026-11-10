# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Extrae el mapa bilineal de un termino de 99 AND del bloque D de unextract
import collections, json, kickmix as km
a,b=52749812,52960536
L=[]
with open('dqi.kmx') as f:
    for i,l in enumerate(f,1):
        if i<a: continue
        if i>b: break
        L.append(l.rstrip())
# localiza terminos: indices de CCX cuyo control esta en palabra p
def word_of(l):
    t=l.split()
    for x in t[1:3]:
        q=int(x[1:])
        if q<840: return q//12
    return None
idx={}
for i,l in enumerate(L):
    if l.startswith('CCX'):
        w=word_of(l)
        if w is not None: idx.setdefault(w,[]).append(i)
ws=sorted([w for w in idx if len(idx[w])==99],reverse=True)
print(ws[:5],len(ws))
w0=ws[2]; w1=ws[3]
s,e=idx[w0][0],idx[w1][0]
# retrocede hasta despues del ultimo CCX de la palabra previa
s=idx[ws[1]][-1]+1
e=idx[w1][0]
# cerca del final del termino w1 anterior: toma tramo [s, ultimoCCX(w0)] mas CX restantes hasta equilibrar
seg=L[s:e]
print('lineas',len(seg),collections.Counter(x.split()[0] for x in seg))
wires=set()
for l in seg:
    for x in l.split()[1:]:
        if x[0]=='q': wires.add(int(x[1:]))
tgt=sorted(q for q in wires if q//12==64 and q<840)
src=sorted(q for q in wires if q<840 and q//12==w0)
oth=sorted(q for q in wires if q not in tgt and q not in src)
print('destino',len(tgt),'fuente',len(src),'otros',[ (q-840 if q>=840 else ('S',q//12,q%12)) for q in oth])
def run(init):
    v=dict(init)
    for l in seg:
        t=l.split();op=t[0]
        q=[int(x[1:]) for x in t[1:] if x[0]=='q']
        if op=='CX': v[q[1]]=v.get(q[1],0)^v.get(q[0],0)
        elif op=='CCX': v[q[2]]=v.get(q[2],0)^(v.get(q[0],0)&v.get(q[1],0))
        elif op=='X': v[q[0]]=v.get(q[0],0)^1
        elif op=='SWAP': v[q[0]],v[q[1]]=v.get(q[1],0),v.get(q[0],0)
        elif op in('Z','CZ','INFO_TAG','BIT_INVERT','BIT_STORE0','BIT_STORE1'): pass
        else: raise Exception(op)
    return v
import random
# matriz bilineal: destino bit t, fuente i, otro j
n_s=len(oth)
M=[[[0]*n_s for _ in src] for _ in tgt]
base={q:0 for q in wires}
r0=run(base)
print('efecto en cero',[q for q in wires if r0[q]])
for i,qi in enumerate(src):
    for j,qj in enumerate(oth):
        init=dict(base);init[qi]=1;init[qj]=1
        r=run(init)
        for t,qt in enumerate(tgt): M[t][i][j]=r[qt]
used=[j for j in range(n_s) if any(M[t][i][j] for t in range(len(tgt)) for i in range(len(src)))]
print('entradas escalares usadas',len(used),[oth[j]-840 if oth[j]>=840 else ('S',oth[j]//12,oth[j]%12) for j in used])
json.dump({'tgt':tgt,'src':src,'oth':oth,'M':M},open('termino.json','w'))
# rango sobre el espacio de escalares: dimension del espacio de matrices 12x12 generado
import numpy as np
vec=[]
for j in used:
    v=0
    for t in range(len(tgt)):
        for i in range(len(src)):
            v=(v<<1)|M[t][i][j]
    vec.append(v)
basis={}
r=0
for v in vec:
    while v:
        h=v.bit_length()-1
        if h in basis: v^=basis[h]
        else: basis[h]=v;r+=1;break
print('dimension del espacio de escalares',r)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
