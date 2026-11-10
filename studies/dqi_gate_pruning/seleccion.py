# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Selección TPF sobre la muestra A: qué puertas borrar para maximizar la razón esperada.
Coste de un conjunto D: Toffolis ahorrados = sum nm/N; fallos = |base ∪ disparos activos de D| / N_A.
La nota esperada usa K ~ Poisson(102400·p) y R(eps+) oficial."""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import numpy as np, json, math, sys, collections
sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
sys.path.insert(0, (_HOME + "/compiler/env"))
from dqi.verify_submission_dqi import clopper_pearson_upper_bound as cp, repetition_overhead as Rf
tag = sys.argv[1] if len(sys.argv) > 1 else 'A'
Z = np.load(f'agg/{tag}.npz'); J = json.load(open(f'agg/{tag}.json'))
nm, act = Z['nm'], Z['act']; NA = J['n']; base_bad = set(J['bad'])
rare = {int(k): v for k, v in J['rare'].items()}
F = np.load('fases_ord.npz'); fase = F['fase']; top = json.load(open('fases_ord.json'))['top']
NOF = 102400; Q = 892; T0 = 395394.06; REF = 24439463583672.93
Rk = [Rf(cp(k, NOF)) for k in range(400)]
def exp_ratio(T, lam):
    # E[REF / (R(K) Q^2 T)] con K ~ Poisson(lam)
    ks = np.arange(400); lp = -lam + ks * math.log(lam) - np.array([math.lgamma(k + 1) for k in ks]) if lam > 0 else None
    if lam == 0: return REF / (Rk[0] * Q * Q * T)
    p = np.exp(lp); return float((p * REF / (np.array(Rk) * Q * Q * T)).sum())
dead = np.flatnonzero((act == 0) & (nm > 0))
w = nm / NA  # Toffolis medios por puerta
print('muestra', NA, 'fallos base', len(base_bad), 'puertas nunca activas', len(dead), 'Toffolis', round(w[dead].sum(), 1))
u, c = np.unique(fase[dead], return_counts=True); print('  por fase', {top[i]: int(x) for i, x in zip(u, c)})
# grupos de puertas raras con conjunto completo, por firma de disparos
groups = collections.defaultdict(list)
for g, s in rare.items():
    if len(s) == act[g]:
        groups[tuple(sorted(s))].append(g)
print('puertas raras completas', sum(len(v) for v in groups.values()), 'grupos', len(groups))
# greedy: ganancia en razón esperada
sel_sh = set(base_bad); T = T0 - w[dead].sum(); chosen = list(dead)
lam = lambda: NOF * len(sel_sh) / NA
cur = exp_ratio(T, lam())
base_ratio = exp_ratio(T0, NOF * len(base_bad) / NA)
print(f'razón esperada base {base_ratio:.4f}; con las nunca activas {cur:.4f}')
G = [(set(k), v, w[v].sum()) for k, v in groups.items()]
pasos = []
while True:
    best = None
    for i, (s, v, tw) in enumerate(G):
        new = len(s - sel_sh)
        r = exp_ratio(T - tw, NOF * (len(sel_sh) + new) / NA)
        if best is None or r > best[0]: best = (r, i)
    if best is None or best[0] <= cur: break
    r, i = best; s, v, tw = G.pop(i)
    sel_sh |= s; T -= tw; chosen.extend(v); cur = r
    pasos.append(dict(toffolis=round(T0 - T, 1), fallos_A=len(sel_sh), lam=round(lam(), 3), razon=round(r, 4), grupo=len(v), disparos=len(s)))
    if len(pasos) % 10 == 1: print(pasos[-1])
print('final', pasos[-1] if pasos else None)
json.dump(dict(dead=[int(x) for x in dead], chosen=[int(x) for x in chosen], pasos=pasos), open(f'seleccion_{tag}.json', 'w'))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
