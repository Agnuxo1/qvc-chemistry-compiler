# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
# Coste medio por fase semantica de invsqrt (simulador oficial, muestra uniforme de x)
import numpy as np, kickmix as km, json
from invsqrt import verify_submission_invsqrt as v
txt=open('invsqrt.kmx').read().split('\n')
body=[l for l in txt if l and not l.startswith(('APPEND','REGISTER'))]
marks=[('normalizar x',0),('tabla K0,K1,C2 (decodificacion)',262),('pasada alta: seleccion+15 rot',14950),('tras pasada alta, reparaciones',15640),('filas C2·delta y K1',20400),('segunda decodificacion',22480),('filas R·delta',23000),('pasada baja: seleccion+26 rot',25400),('reparaciones de medida',25720),('deshacer filas (condicionado)',27978),('deshacer filas (fijo)',32047),('deshacer decodificacion',34547),('fases de tabla (Clifford)',36500),('limpieza',43000),('desnormalizar x',46360)]
depth=[0]*(len(body)+1)
d=0
for i,l in enumerate(body):
    depth[i]=d
    if l.startswith('PUSH'): d+=1
    elif l.startswith('POP'): d-=1
bounds=[]
for n,a in marks:
    while depth[a]!=0: a+=1
    bounds.append((n,a))
bounds.append(('fin',len(body)))
chunks=[km.Circuit('\n'.join(body[a:b])) for (n,a),(m,b) in zip(bounds,bounds[1:])]
stat=[sum(1 for l in body[a:b] if l.startswith(('CCX','CCZ','CSWAP'))) for (n,a),(m,b) in zip(bounds,bounds[1:])]
full=km.Circuit.from_file((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/invsqrt.kmb"),format='kmb')
spec=v.ProblemSpecInvSqrt.for_n_p(10,shots_per_x=64)
x_reg,scr=v.validate_registers(full,spec)
sim=km.Simulator(batch_size=256,debug_print=False,counting_operations=True,seed=7)
rng=np.random.default_rng(3)
B=400
acc=np.zeros((len(chunks),3))
p=np.zeros(3)
for r in range(B):
    xs=rng.integers(1,spec.max_x+1,size=256,dtype=np.uint64)
    sim.clear_for_shot()
    sim.write_across_shots(x_reg,v.to_bits(xs,spec.width))
    for i,c in enumerate(chunks):
        sim.do(c)
        s=sim.operation_statistics()
        q=np.array((s.num_toffoli_like,s.num_t_like,s.num_z_pow(min_clifford_hierarchy_level=4)),dtype=float)
        acc[i]+=q-p; p=q
acc/=B*256
rows=[]
for i,((n,a),(m,b)) in enumerate(zip(bounds,bounds[1:])):
    rows.append(dict(fase=n,lineas=(a,b),estaticos=stat[i],media=round(acc[i,0],2),T=round(acc[i,1],2),rot=round(acc[i,2],2)))
    print(f'{n:38s} {a:6d}-{b:6d} estat {stat[i]:5d} media {acc[i,0]:8.2f} rot {acc[i,2]:5.1f}')
print(acc.sum(0),sum(stat))
json.dump(rows,open('fases_inv.json','w'),indent=1,ensure_ascii=False)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
