# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Cost model of a shape, with the loaders scaled from the public 4,152 Toffolis per pass."""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys
sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1 as M
N, CHI = 76, 10


def model(R, B, C, b, J=5):
    m = M(R, B, C, N, CHI, b)
    o, i, g = m.outer_state_prep(), m.inner_state_prep(), m.givens_rotations()
    oq, iq = m.outer_state_prep_qubit_cost(), m.inner_state_prep_qubit_cost()
    temp = max(oq["temporary"], iq["temporary"], 77)
    return o, i, g, oq["persistent"] + iq["persistent"] + J * b + temp, temp


o0, i0, g0, Q0, _ = model(8, 143, 44, 8)
T0 = o0 + i0 + g0 + 8304
eff = (76 + 8 * 143) * 75 * 8 / 4152
print("base", o0, i0, g0, "T", T0, "Q", Q0)
shapes = [(8,143,44,8),(8,143,45,8),(8,143,40,8),(7,143,50,8),(7,143,48,8),(7,143,44,8),(7,135,48,8),(7,135,44,8),(7,129,48,8),
          (6,158,48,8),(6,158,56,8),(6,143,56,8),(6,143,50,8),(6,129,56,8),(5,189,56,8),(5,189,64,8),(5,159,64,8),(4,239,64,8),(4,239,80,8),
          (7,143,48,7),(7,127,48,7),(6,143,56,7),(6,127,56,7)]
print("forma filas Touter Tinner Tgivens Tload T Q temp TQrel quimica global")
for s in shapes:
    R, B, C, b = s
    o, i, g, Q, temp = model(R, B, C, b)
    A = 76 + R * B
    ld = 2 * A * 75 * b / eff
    T = o + i + g + ld
    rel = T * Q / (T0 * Q0)
    print(s, A, o, i, g, round(ld), round(T), Q, temp, round(rel, 3), round(11.1976 / rel, 2), round((21.2464 * 65.2117 * 11.1976 / rel) ** (1 / 3), 2))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
