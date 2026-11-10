# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Toffolis and qubits per circuit of two families, to see where a cheaper compilation comes from."""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys
sys.path.insert(0, (_HOME + "/compiler/env"))
import kickmix
tot = {}
for name, d in (('base', (_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/dfthcsos")), ('m845L', (_HOME + "/compiler/corrida_m845L/submission"))):
    row = []
    for k in range(15):
        c = kickmix.Circuit.from_file(f'{d}/angle_k_{k}.kmb')
        s = c.operation_statistics()
        row.append((s.num_toffoli_like, c.num_qubits))
    tot[name] = row
    print(name, 'total', sum(r[0] for r in row), 'qubits', {r[1] for r in row})
    print(' ', [r[0] for r in row])
c = kickmix.Circuit.from_file((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/dfthcsos/angle_k_7.kmb"))
s = c.operation_statistics()
print([a for a in dir(s) if not a.startswith('_')])
print({a: getattr(s, a) for a in dir(s) if a.startswith('num_') and not callable(getattr(s, a))})
t = c.text_diagram()
print(len(t), t[:1500])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
