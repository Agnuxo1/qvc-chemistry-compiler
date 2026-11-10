# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import collections
a,b=52749812,52960536
ops=[]
cx=0
with open('dqi.kmx') as f:
    for i,l in enumerate(f,1):
        if i<a: continue
        if i>b: break
        h=l[:3]
        if h in('CCX','CCZ','CSW'):
            t=l.split(); ops.append((i,cx,t[0],int(t[1][1:]),int(t[2][1:]),int(t[3][1:]))); cx=0
        elif h=='CX ': cx+=1
        elif h=='HMR' or h=='R q': ops.append((i,cx,l.split()[0],int(l.split()[1][1:]),0,0)); cx=0
print(len(ops))
def n(q): return f'{q//12}.{q%12}' if q<840 else f'a{q-840}'
s=[]
for o in ops[:150]:
    s.append(f'{o[1]}cx {o[2][:3]} {n(o[3])} {n(o[4])}>{n(o[5])}' if o[2] not in('HMR','R') else f'{o[1]}cx {o[2]} {n(o[3])}')
print(' | '.join(s))
# ventana: que palabras-fuente en orden y cuantos CCX consecutivos por palabra fuente
seq=[]
for o in ops:
    if o[2]=='CCX':
        ws=[x//12 for x in (o[3],o[4]) if x<840]
        seq.append(ws[0] if ws else 'a')
out=[];cur=None;c=0
for w in seq:
    if w!=cur:
        if cur is not None: out.append((cur,c))
        cur=w;c=0
    c+=1
out.append((cur,c)); print(out[:80])
print()
idx=[k for k,o in enumerate(ops) if o[2]=='CCX' and any(x<840 and x//12==60 for x in (o[3],o[4]))]
print(len(idx),idx[:3],idx[-3:])
k0=idx[23]
s=[]
for o in ops[k0-3:k0+112]:
    s.append(f'{o[1]} {n(o[3])},{n(o[4])}>{n(o[5])}' if o[2] not in('HMR','R') else f'{o[1]} {o[2]} {n(o[3])}')
print(' | '.join(s))
c=collections.Counter()
for o in ops:
    if o[2]=='CCX':
        for x in (o[3],o[4]):
            if x>=840: c[x-840]+=1
print(c.most_common(30))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
