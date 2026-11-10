# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Para cada puerta Toffoli-like (ordinal), la fase de primer nivel, la hoja de etiquetas y el número de línea.
import numpy as np, json
top = ['mask_projection','initial','extract','synthesis','convert','scan','unconvert','unsynthesis','unextract','uninitial','restore_masks']
stack = []; fase = []; hoja = []; linea = []; hojas = {}
with open('dqi.kmx') as f:
    for n, l in enumerate(f, 1):
        c0 = l[0]
        if c0 == 'I':
            t = l[10:-2]; kind, name = t[1:].split(':', 1)
            if kind == 'enter': stack.append(name)
            else: stack.pop()
            continue
        if c0 == 'C' and (l.startswith('CCX') or l.startswith('CCZ') or l.startswith('CSWAP')):
            fase.append(top.index(stack[0]) if stack else -1)
            h = '/'.join(stack[1:]); hoja.append(hojas.setdefault(h, len(hojas))); linea.append(n)
np.savez('fases_ord.npz', fase=np.array(fase), hoja=np.array(hoja), linea=np.array(linea))
json.dump(dict(top=top, hojas=hojas), open('fases_ord.json', 'w'))
print(len(fase))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
