# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
# Captura, para cada x, el bit que rota cada Z_POW no Clifford y la fase restante; guarda en .npz
import numpy as np, kickmix as km, sys, time
from invsqrt import verify_submission_invsqrt as v
kmx=sys.argv[1] if len(sys.argv)>1 else 'invsqrt.kmx'
txt=open(kmx).read().split('\n')
body=[l for l in txt if l and not l.startswith(('APPEND','REGISTER'))]
full=km.Circuit.from_file((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/invsqrt.kmb"),format='kmb')
spec=v.ProblemSpecInvSqrt.for_n_p(10,shots_per_x=64)
x_reg,scr=v.validate_registers(full,spec)
# localiza rotaciones
rots=[]  # (linea, qubit, angulo txt, condicionada)
depth=0
for i,l in enumerate(body):
    if l.startswith('PUSH'): depth+=1
    elif l.startswith('POP'): depth-=1
    if l.startswith('Z_POW'):
        t=l.split()
        rots.append((i,int(t[1][1:]),t[2],depth,' '.join(t[3:])))
print(len(rots), [r for r in rots if r[3]>0][:5])
from fractions import Fraction
keep=[r for r in rots]
bounds=[0]+[r[0] for r in keep]+[len(body)]
# parte cada tramo: hasta la rotacion (sin incluir), la rotacion se quita (angulo 0) para medir fase residual
chunks=[]
for a,b in zip(bounds,bounds[1:]):
    s=a+1 if a in [r[0] for r in keep] else a
    chunks.append(km.Circuit('\n'.join(body[s:b])) if b>s else None)
N=spec.max_x
xs_all=np.arange(1,N+1,dtype=np.uint64)
B=256
pad=(-N)%B
xs_all=np.concatenate([xs_all,np.full(pad,1,dtype=np.uint64)])
nb=len(xs_all)//B
bits=np.zeros((len(keep),len(xs_all)),dtype=bool)
resid=np.zeros(len(xs_all),dtype=np.uint64)
sim=km.Simulator(batch_size=B,debug_print=False,counting_operations=False,seed=11)
t=time.time()
qs=[km.array([km.q(r[1])]) for r in keep]
for ib in range(nb):
    xs=xs_all[ib*B:(ib+1)*B]
    sim.clear_for_shot()
    sim.write_across_shots(x_reg,v.to_bits(xs,spec.width))
    for k,c in enumerate(chunks):
        if c is not None: sim.do(c)
        if k<len(keep):
            bits[k,ib*B:(ib+1)*B]=sim.read_across_shots(qs[k])[0]
    resid[ib*B:(ib+1)*B]=[v.half_turns_to_units(sim.read_shot_phase(i)) for i in range(B)]
    if ib%2000==0: print(ib,nb,time.time()-t,flush=True)
np.savez_compressed('rot_bits.npz',bits=np.packbits(bits,axis=1),resid=resid,n=len(xs_all),lines=np.array([r[0] for r in keep]),qs=np.array([r[1] for r in keep]),ang=np.array([r[2] for r in keep]),cond=np.array([r[3] for r in keep]))
print('fin',time.time()-t)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
