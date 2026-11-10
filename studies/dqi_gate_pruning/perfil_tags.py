# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Perfil de Toffolis por ruta de etiquetas (INFO_TAG @enter/@exit) en dqi.kmx; cuenta condicionadas aparte.
import collections, json, sys
T = {'CCX', 'CCZ', 'CSWAP'}
stack = []; cnt = collections.Counter(); cond = collections.Counter(); ops = collections.Counter()
occ = collections.Counter(); hmr = collections.Counter()
depth_cond = 0
with open('dqi.kmx') as f:
    for l in f:
        c0 = l[0]
        if c0 == 'A' or (c0 == 'R' and l[1] == 'E'): continue
        if c0 == 'I':
            t = l[10:-2]; kind, name = t[1:].split(':', 1)
            if kind == 'enter':
                stack.append(name); occ['/'.join(stack)] += 1
            else:
                assert stack and stack[-1] == name, (stack, name); stack.pop()
            continue
        op = l.split(' ', 1)[0].rstrip()
        if op == 'PUSH_CONDITION': depth_cond += 1; continue
        if op == 'POP_CONDITION': depth_cond -= 1; continue
        key = '/'.join(stack)
        if op in T:
            if depth_cond or ' if ' in l: cond[key] += 1
            else: cnt[key] += 1
        elif op == 'HMR': hmr[key] += 1
        ops[key] += 1
keys = set(cnt) | set(cond) | set(occ)
res = {k: dict(tof=cnt[k], tof_cond=cond[k], occ=occ[k], hmr=hmr[k], ops=ops[k]) for k in keys}
json.dump(res, open('perfil_tags.json', 'w'), indent=0)
# agregado por nombre de hoja y por primer nivel
agg = collections.Counter(); aggc = collections.Counter()
for k in keys:
    agg[k.split('/')[0] if k else '<raiz>'] += cnt[k]; aggc[k.split('/')[0] if k else '<raiz>'] += cond[k]
print('total', sum(cnt.values()), 'cond', sum(cond.values()))
for k, v in sorted(agg.items(), key=lambda x: -x[1]): print(f'{k:20s} {v:8d} cond {aggc[k]}')
leaf = collections.Counter(); leafc = collections.Counter(); leafo = collections.Counter()
for k in keys:
    nm = k.split('/')[-1] if k else '<raiz>'
    leaf[nm] += cnt[k]; leafc[nm] += cond[k]; leafo[nm] += occ[k]
print()
for k, v in sorted(leaf.items(), key=lambda x: -(x[1] + leafc[x[0]])): print(f'{k:40s} {v:8d} cond {leafc[k]:6d} veces {leafo[k]}')

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
