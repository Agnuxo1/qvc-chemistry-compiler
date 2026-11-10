# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import collections,json
top={'mask_projection','initial','extract','synthesis','convert','scan','unconvert','unsynthesis','unextract'}
# segmentos: pila por enter/exit de etiquetas de primer nivel
cur='<pre>'
acc=collections.OrderedDict()
def get(k):
    if k not in acc: acc[k]=collections.Counter()
    return acc[k]
n=0;cond=0
c=get(cur)
with open('dqi.kmx','r') as f:
    for l in f:
        n+=1
        if not l or l[0]=='\n': continue
        op=l.split(None,1)[0]
        if op=='INFO_TAG':
            t=l.strip()[10:-1]
            kind,name=t[1:].split(':',1)
            if name in top:
                cur=name if kind=='enter' else '<tras '+name+'>'
                c=get(cur)
                c['linea0']=c['linea0'] or n
            c['tags']+=1
            continue
        if op in('CCX','CCZ','CSWAP'):
            c['tof']+=1
            if cond: c['tof_cond']+=1
        elif op=='PUSH_CONDITION': cond+=1; c['push']+=1
        elif op=='POP_CONDITION': cond-=1
        elif op=='HMR': c['HMR']+=1
        elif op=='CX': c['CX']+=1
        elif op=='R': c['R']+=1
tot=0
for k,v in acc.items():
    tot+=v['tof']
    print(f"{k:28s} linea {v['linea0']:>9} tof {v['tof']:>7} cond {v['tof_cond']:>6} CX {v['CX']:>9} HMR {v['HMR']:>6} push {v['push']:>5}")
print(tot)
json.dump({k:dict(v) for k,v in acc.items()},open('seg_dqi_top.json','w'),indent=0)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
