# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Tabla R(eps+) frente a k fallos en 102.400 disparos y Toffolis a ahorrar para compensar.
Usa las funciones del verificador oficial (clopper_pearson_upper_bound, repetition_overhead)."""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import json, math, sys
sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
sys.path.insert(0, (_HOME + "/compiler/env"))
from dqi.verify_submission_dqi import clopper_pearson_upper_bound as cp, repetition_overhead as R
N = 102400
Q, T0 = 892, 395394.06
R0 = R(cp(0, N))
S0 = R0 * Q * Q * T0
rows = []
for k in [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300, 500, 1000]:
    e = cp(k, N); r = R(e)
    T_eq = T0 * R0 / r
    rows.append(dict(k=k, p_hat=k / N, eps_plus=e, R=r, dR_pct=100 * (r / R0 - 1),
                     T_equal=T_eq, ahorro=T0 - T_eq, ahorro_pct=100 * (1 - R0 / r)))
print(f"R0={R0:.6f}  S0={S0:.6e}  ratio_base=65.2116")
print(f"{'k':>5} {'eps+':>10} {'R':>8} {'+R%':>7} {'ahorro T':>9} {'ahorro%':>8} {'por fallo':>9}")
for x in rows:
    pf = x['ahorro'] / x['k'] if x['k'] else 0
    print(f"{x['k']:>5} {x['eps_plus']:>10.3e} {x['R']:>8.5f} {x['dR_pct']:>7.3f} {x['ahorro']:>9.0f} {x['ahorro_pct']:>8.3f} {pf:>9.0f}")
json.dump(dict(R0=R0, T0=T0, Q=Q, filas=rows), open('tabla_k.json', 'w'), indent=1)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
