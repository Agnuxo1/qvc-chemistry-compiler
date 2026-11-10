# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import kickmix as km,time,psutil,os
t=time.time()
c=km.Circuit.from_file((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/dqi.kmb"),format='kmb')
print('cargado',time.time()-t,psutil.Process().memory_info().rss/2**30)
s=c.operation_statistics()
print(c.num_qubits,c.num_bits,len(c),s, dict(s.items()) if hasattr(s,'items') else '')
print(len(c.register_data))
t=time.time()
c.to_file('dqi.kmx',format='kmx')
print('volcado',time.time()-t)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
