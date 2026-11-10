# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Resumen por tramos de invsqrt.kmx: Toffolis, Z_POW, HMR por bloques de lineas y qubits tocados
import re,collections,sys
L=open('invsqrt.kmx').read().split('\n')
tof=('CCX','CCZ','CSWAP')
cum=0
acc=[]
step=1000
row=collections.Counter()
for i,l in enumerate(L):
    if not l: continue
    op=l.split()[0]
    row[op]+=1
    if (i+1)%step==0:
        t=row['CCX']+row['CCZ']+row['CSWAP']
        cum+=t
        print(i+1,'tof',t,'cum',cum,'CCX',row['CCX'],'CCZ',row['CCZ'],'CSW',row['CSWAP'],'HMR',row['HMR'],'ZP',row['Z_POW'],'PUSH',row['PUSH_CONDITION'],'R',row['R'])
        row=collections.Counter()

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
