# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Perfil de qubits vivos en DQI por fases: qubit libre tras HMR/R y hasta el siguiente uso
import collections,json
top={'mask_projection','initial','extract','synthesis','convert','scan','unconvert','unsynthesis','unextract'}
live=[False]*892
for i in range(840): live[i]=True
n=840
phase='<pre>'
res=collections.OrderedDict()
samples=[]
step=20000
i=0
peak=0;psum=0;pc=0;hist=collections.Counter()
def new(p):
    res[p]={'max':0,'min':10**9,'sum':0,'n':0,'hist':collections.Counter()}
new(phase)
cur=res[phase]
with open('dqi.kmx') as f:
    for l in f:
        i+=1
        if l[0]=='I':
            if l.startswith('INFO_TAG'):
                t=l.strip()[10:-1]; kind,name=t[1:].split(':',1)
                if name in top:
                    phase=name if kind=='enter' else '<tras %s>'%name
                    new(phase); cur=res[phase]
            continue
        if l[0]=='A' or l[0]=='R' and l.startswith('REGISTER'): continue
        p=l.split()
        op=p[0]
        if op=='BIT_INVERT' or op[:3]=='BIT' or op=='PUSH_CONDITION' or op=='POP_CONDITION' or op=='NEG': continue
        if op=='HMR' or op=='R':
            q=int(p[1][1:])
            if live[q]: live[q]=False; n-=1
        else:
            for a in p[1:]:
                if a[0]=='q':
                    q=int(a[1:])
                    if not live[q]: live[q]=True; n+=1
                elif a=='if': break
        if n>cur['max']: cur['max']=n
        if n<cur['min']: cur['min']=n
        cur['sum']+=n; cur['n']+=1
        cur['hist'][n]+=1
for k,v in res.items():
    if v['n']:
        h=sorted(v['hist'].items(),reverse=True)[:6]
        print(f"{k:24s} max {v['max']} min {v['min']} media {v['sum']/v['n']:.1f} top {h}")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
