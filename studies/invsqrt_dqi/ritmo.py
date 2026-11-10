# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Ritmo de Toffolis y HMR en un rango de lineas de dqi.kmx: Txn Hxn con CX omitidos
import sys
a,b=int(sys.argv[1]),int(sys.argv[2])
out=[];cur=None;n=0
with open('dqi.kmx') as f:
    for i,l in enumerate(f,1):
        if i<a: continue
        if i>b: break
        op=l.split(None,1)[0]
        if op in('CCX','CCZ','CSWAP'): k='T'
        elif op=='HMR': k='H'
        elif op=='R': k='R'
        elif op=='INFO_TAG': k='#'+l.split('"')[1].replace('@','')
        else: continue
        if k!=cur:
            if cur: out.append(f'{cur}{n}' if cur[0]!='#' else cur)
            cur=k;n=0
        n+=1
out.append(f'{cur}{n}')
print(' '.join(out)[:int(sys.argv[3]) if len(sys.argv)>3 else 3000])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
