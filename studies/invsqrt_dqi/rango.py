# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Rango afin de los cables vivos a lo largo del circuito (muestra estratificada del dominio)
import random, sys, json, collections
random.seed(2)
body=[l for l in open('invsqrt.kmx').read().split('\n') if l and not l.startswith(('APPEND','REGISTER'))]
N=3133452
xs=set(range(1,2049))
for e in range(11,22):
    lo,hi=1<<e,min((1<<(e+1))-1,N)
    xs.update(random.randint(lo,hi) for _ in range(500))
xs=sorted(xs); S=len(xs); ALL=(1<<S)-1; print(S)
Q=62
w=[0]*Q
for b in range(22):
    v=0
    for i,x in enumerate(xs):
        if (x>>b)&1: v|=1<<i
    w[b]=v
live=[b<22 for b in range(Q)]
def rank():
    basis={}
    r=0
    items=[ALL]+[w[q] for q in range(Q) if live[q]]
    for v in items:
        while v:
            h=v.bit_length()-1
            if h in basis: v^=basis[h]
            else: basis[h]=v; r+=1; break
    return r-1  # sin la constante
depth=0
hist=collections.Counter()
minslack=99
rows=[]
for i,l in enumerate(body):
    t=l.split(); op=t[0]
    if op=='PUSH_CONDITION': depth+=1; continue
    if op=='POP_CONDITION': depth-=1; continue
    if depth>0 or ' if ' in l: continue
    qs=[int(a[1:]) for a in t[1:] if a[0]=='q']
    changed=False
    if op=='X': w[qs[0]]^=ALL; live[qs[0]]=True
    elif op=='CX':
        w[qs[1]]^=w[qs[0]]
        if not live[qs[1]]: live[qs[1]]=True; changed=True
    elif op=='SWAP': w[qs[0]],w[qs[1]]=w[qs[1]],w[qs[0]]; live[qs[0]]=live[qs[1]]=True; changed=True
    elif op in('HMR','R'): w[qs[0]]=0; live[qs[0]]=False; changed=True
    elif op=='CCX':
        a,b,c=qs; w[c]^=w[a]&w[b]; live[c]=True; changed=True
    elif op=='CSWAP':
        c,a,b=qs; p=w[c]&(w[a]^w[b]); w[a]^=p; w[b]^=p; changed=True
    else: continue
    if changed:
        n=sum(live)
        if n>=59:
            r=rank()
            rows.append((i,n,r))
            hist[(n,n-r)]+=1
print(sorted(hist.items(),reverse=True)[:30])
peak=[r for r in rows if r[1]==62]
print('puntos con 62 vivos',len(peak),'rango minimo/maximo',min(r[2] for r in peak),max(r[2] for r in peak))
# tramos con holgura 0 en 62
z=[r[0] for r in peak if r[2]==62]
print('62 sin holgura',len(z),z[:40],z[-10:])
json.dump(rows,open('rango.json','w'))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
