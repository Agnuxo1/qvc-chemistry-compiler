# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
# Coste medio por tramo de invsqrt con el simulador oficial (chunks de lineas, profundidad de condicion 0)
import numpy as np, kickmix as km, sys, re
from invsqrt import verify_submission_invsqrt as v
txt=open('invsqrt.kmx').read().split('\n')
hdr=[l for l in txt if l.startswith(('APPEND','REGISTER'))]
body=[l for l in txt if l and not l.startswith(('APPEND','REGISTER'))]
# fronteras: cada ~500 lineas en profundidad 0
depth=0;bounds=[0];last=0
for i,l in enumerate(body):
    if l.startswith('PUSH'): depth+=1
    elif l.startswith('POP'): depth-=1
    if depth==0 and i-last>=int(sys.argv[1]) :
        bounds.append(i+1);last=i
bounds.append(len(body))
chunks=[km.Circuit('\n'.join(body[a:b])) for a,b in zip(bounds,bounds[1:])]
full=km.Circuit.from_file((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/invsqrt.kmb"),format='kmb')
spec=v.ProblemSpecInvSqrt.for_n_p(10,shots_per_x=1)
x_reg,scr=v.validate_registers(full,spec)
sim=km.Simulator(batch_size=256,debug_print=False,counting_operations=True,seed=7)
rng=np.random.default_rng(3)
B=200
acc=np.zeros((len(chunks),3))
for r in range(B):
    xs=rng.integers(1,spec.max_x+1,size=256,dtype=np.uint64)
    sim.clear_for_shot()
    sim.write_across_shots(x_reg,v.to_bits(xs,spec.width))
    p=(0,0,0)
    for i,c in enumerate(chunks):
        sim.do(c)
        s=sim.operation_statistics()
        q=(s.num_toffoli_like,s.num_t_like,s.num_z_pow(min_clifford_hierarchy_level=4))
        acc[i]+=np.array(q)-np.array(p); p=q
acc/=B*256
cum=0
for i,(a,b) in enumerate(zip(bounds,bounds[1:])):
    cum+=acc[i,0]
    print(f'{a:6d}-{b:6d} tof {acc[i,0]:8.2f} cum {cum:8.2f} T {acc[i,1]:6.2f} rot {acc[i,2]:6.2f}')
print(acc.sum(0))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
