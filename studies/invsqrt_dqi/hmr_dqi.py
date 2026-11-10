# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import collections
top={'extract','synthesis','convert','scan','unconvert','unsynthesis','unextract'}
phase=None
c=collections.defaultdict(collections.Counter)
with open('dqi.kmx') as f:
    for l in f:
        h=l[:3]
        if h=='INF':
            t=l.strip()[10:-1]; kind,name=t[1:].split(':',1)
            if name in top: phase=name if kind=='enter' else None
            continue
        if phase is None: continue
        if h=='HMR' or h=='R q':
            q=int(l.split()[1][1:])
            k=('HMR' if h=='HMR' else 'R')+('_S' if q<840 else '_anc')
            c[phase][k]+=1
for k,v in c.items(): print(k,dict(v))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
