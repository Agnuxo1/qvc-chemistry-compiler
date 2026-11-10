# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Secuencia de etiquetas por fase de primer nivel con Toffolis entre etiquetas (compacta)
import collections,json
top={'mask_projection','initial','extract','synthesis','convert','scan','unconvert','unsynthesis','unextract'}
phase=None
seqs=collections.OrderedDict()
n=0;tof=0;hmr=0;cx=0
last='^'
def flush(t):
    global tof,hmr,cx
    if phase is not None:
        seqs[phase].append((t,tof,hmr,cx))
    tof=0;hmr=0;cx=0
with open('dqi.kmx') as f:
    for l in f:
        c=l[:3]
        if c=='CX ': cx+=1; continue
        if c=='CCX' or c=='CCZ' or c=='CSW': tof+=1; continue
        if c=='HMR': hmr+=1; continue
        if c=='INF':
            t=l.strip()[10:-1]
            kind,name=t[1:].split(':',1)
            if name in top:
                if kind=='enter':
                    phase=name; seqs[phase]=[]; tof=hmr=cx=0
                else:
                    flush('END'); phase=None
                continue
            if name=='gf_iadd': continue
            flush(('+' if kind=='enter' else '-')+name)
json.dump(seqs,open('seg_dqi_seq3.json','w'))
for k,v in seqs.items():
    print(k,len(v),sum(a[1] for a in v))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
