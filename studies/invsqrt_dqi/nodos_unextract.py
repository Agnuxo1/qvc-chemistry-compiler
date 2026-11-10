# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Tramos de unextract y extract separados por rafagas de HMR sobre cables S (q<840): coste por tramo
import sys
def tramos(a,b):
    cum=0;last=-1;out=[];burst=0;t0=0
    with open('dqi.kmx') as f:
        for i,l in enumerate(f,1):
            if i<a: continue
            if i>b: break
            h=l[:3]
            if h in('CCX','CCZ','CSW'): cum+=1
            elif h=='HMR':
                q=int(l.split()[1][1:])
                if q<840:
                    if cum-last>40:
                        out.append([cum,0])
                    out[-1][1]+=1
                    last=cum
    return out
for nombre,a,b in (('extract',2698119,6591539),('unextract',52196368,57991164)):
    o=tramos(a,b)
    d=[o[i][0]-(o[i-1][0] if i else 0) for i in range(len(o))]
    print(nombre,len(o),'tramos; Toffolis entre rafagas:',d[:60]);print(' bits por rafaga:',[x[1] for x in o][:60])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
