# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import json,sys,glob,os
for p in glob.glob('../kernels_publicos/*/*.ipynb'):
    nb=json.load(open(p,encoding='utf-8'))
    out=[]
    for i,c in enumerate(nb['cells']):
        src=''.join(c['source'])
        out.append(f'### [{i}] {c["cell_type"]}\n{src}\n')
        if c['cell_type']=='code':
            for o in c.get('outputs',[]):
                t=o.get('text') or o.get('data',{}).get('text/plain') or ''
                t=''.join(t)
                if t: out.append('--- out\n'+t[:1500]+'\n')
    name=os.path.basename(os.path.dirname(p))
    open(f'notas/{name}.txt','w',encoding='utf-8').write('\n'.join(out))
    print(name,len('\n'.join(out)))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
