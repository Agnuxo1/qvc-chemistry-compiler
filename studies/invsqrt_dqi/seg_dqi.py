# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Recorre dqi.kmx en streaming: tramos entre INFO_TAG con Toffolis y operaciones
import collections,json
tags=collections.OrderedDict()
cur='<inicio>'
stats=collections.defaultdict(collections.Counter)
seq=[]
n=0
qmax=-1
cond=0
with open('dqi.kmx','r') as f:
    for l in f:
        n+=1
        p=l.split(None,1)
        if not p: continue
        op=p[0]
        if op=='INFO_TAG':
            cur=l.strip()[9:]
            seq.append((n,cur))
            stats[cur]['n']+=1
            continue
        if op in('CCX','CCZ','CSWAP'):
            stats[cur]['tof']+=1
            if cond: stats[cur]['tof_cond']+=1
        elif op=='PUSH_CONDITION': cond+=1
        elif op=='POP_CONDITION': cond-=1
        stats[cur][op]+=1
print(n)
json.dump({k:dict(v) for k,v in stats.items()},open('seg_dqi.json','w'),indent=0)
json.dump(seq,open('seg_dqi_seq.json','w'))
print(len(seq))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
