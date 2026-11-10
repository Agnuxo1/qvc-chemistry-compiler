# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Busca Toffolis cuyo producto es afin en los cables vivos sobre todo el dominio x (muestra estratificada, luego prueba exacta)
import numpy as np, random, sys, json
random.seed(1)
kmx=sys.argv[1] if len(sys.argv)>1 else 'invsqrt.kmx'
body=[l for l in open(kmx).read().split('\n') if l and not l.startswith(('APPEND','REGISTER'))]
N=3133452
xs=set(range(1,4097))
for e in range(12,22):
    lo,hi=1<<e,min((1<<(e+1))-1,N)
    xs.update(random.randint(lo,hi) for _ in range(1500))
xs.update(range(N-300,N+1))
xs=sorted(xs); S=len(xs); print('muestra',S)
ALL=(1<<S)-1
Q=62
w=[0]*Q
for b in range(22):
    v=0
    for i,x in enumerate(xs):
        if (x>>b)&1: v|=1<<i
    w[b]=v
live=[b<22 for b in range(Q)]
def span_test(p,exclude=()):
    # devuelve combinacion de cables (+1) que da p, o None
    basis={}  # pivote -> (vector, mascara)
    items=[(ALL,1<<Q)]+[(w[q],1<<q) for q in range(Q) if live[q] and q not in exclude]
    for v,m in items:
        while v:
            h=v.bit_length()-1
            if h in basis:
                bv,bm=basis[h]; v^=bv; m^=bm
            else:
                basis[h]=(v,m); break
    v=p;m=0
    while v:
        h=v.bit_length()-1
        if h in basis:
            bv,bm=basis[h]; v^=bv; m^=bm
        else: return None
    return m
hits=[]
depth=0
nT=0
for i,l in enumerate(body):
    t=l.split()
    op=t[0]
    if op=='PUSH_CONDITION': depth+=1; continue
    if op=='POP_CONDITION': depth-=1; continue
    if depth>0: continue
    if ' if ' in l: continue
    qs=[int(a[1:]) for a in t[1:] if a[0]=='q']
    if op=='X': w[qs[0]]^=ALL; live[qs[0]]=True
    elif op=='CX': w[qs[1]]^=w[qs[0]]; live[qs[1]]=True
    elif op=='SWAP': w[qs[0]],w[qs[1]]=w[qs[1]],w[qs[0]]; live[qs[0]]=live[qs[1]]=True
    elif op in('HMR','R'): w[qs[0]]=0; live[qs[0]]=False
    elif op=='CCX':
        nT+=1
        a,b,c=qs
        p=w[a]&w[b]
        if p==0: hits.append((i,l,'cero',0))
        else:
            m=span_test(p,exclude=())
            if m is not None: hits.append((i,l,'afin',m))
        w[c]^=p; live[c]=True
    elif op=='CSWAP':
        nT+=1
        c,a,b=qs
        p=w[c]&(w[a]^w[b])
        if p==0: hits.append((i,l,'cero',0))
        else:
            m=span_test(p)
            if m is not None: hits.append((i,l,'afin',m))
        w[a]^=p; w[b]^=p
    elif op=='CCZ':
        nT+=1
        a,b,c=qs
        for (u,v,z) in ((a,b,c),(a,c,b),(b,c,a)):
            p=w[u]&w[v]
            m=span_test(p,exclude=(z,))
            if m is not None or p==0:
                hits.append((i,l,'ccz-afin',m)); break
print('Toffolis no condicionados',nT,'candidatos',len(hits))
print('final vivos',[q for q in range(Q) if w[q]!=0 and q>=22])
for h in hits[:60]:
    m=h[3] or 0
    print(h[0],h[1],h[2],[q for q in range(Q+1) if (m>>q)&1])
json.dump(hits,open('semantica_hits.json','w'),default=str)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
