# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import sys,math,json
sys.path.insert(0,(_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1 as M
N=76;chi=10
def model(R,B,C,b,J,ang_pass=None,temp_ang=77):
    m=M(R,B,C,N,chi,b)
    o,i,g=m.outer_state_prep(),m.inner_state_prep(),m.givens_rotations()
    oq,iq=m.outer_state_prep_qubit_cost(),m.inner_state_prep_qubit_cost()
    temp=max(oq["temporary"],iq["temporary"],temp_ang)
    Q=oq["persistent"]+iq["persistent"]+J*b+temp
    return dict(o=o,i=i,g=g,Tnoang=o+i+g,Q=Q,temp=temp,pers=oq["persistent"]+iq["persistent"])
base=model(8,143,44,8,5)
print("base",base)
T0=base["Tnoang"]+8304;Q0=base["Q"];print("T,Q",T0,Q0,"T*Q",T0*Q0)
# angle cost model: proportional to table bits at fixed loader efficiency (bits/AND measured on the public loaders)
A0=76+8*143;bits0=A0*75*8;eff=bits0/4152
print("A",A0,"bits",bits0,"bits por AND",round(eff,1))
rows=[]
for R in (4,5,6,7,8,9,10,12,16):
 for B in (64,72,80,96,112,120,127,128,136,143,160,192,255,256):
  A=76+R*B
  if A>2048: continue
  for C in (28,32,36,40,44,48,52,56,60):
   for b in (5,6,7,8,9):
    for J in (3,4,5,6,8):
     try: m=model(R,B,C,b,J)
     except Exception: continue
     ang=2*(A*75*b/eff)
     T=m["Tnoang"]+ang
     rows.append((T*m["Q"]/(T0*Q0),R,B,C,b,J,round(T),m["Q"],m["temp"]))
rows.sort()
seen=set();n=0
for r in rows:
    k=(r[1],r[2],r[3],r[4])
    if k in seen: continue
    seen.add(k);n+=1
    if n<=14: print(r)
print("--- brot 8, misma forma, solo cambia una cosa")
for (R,B,C,b,J) in [(8,143,44,8,5),(8,143,44,7,5),(8,143,44,6,5),(8,143,44,7,6),(8,128,44,8,5),(8,127,44,8,5),(9,127,44,8,5),(8,143,40,8,5),(8,143,36,8,5),(7,143,44,8,5),(6,143,44,8,5)]:
    m=model(R,B,C,b,J);A=76+R*B;T=m["Tnoang"]+2*(A*75*b/eff)
    print((R,B,C,b,J),"A",A,"T",round(T),"Q",m["Q"],"temp",m["temp"],"TQ/base",round(T*m["Q"]/(T0*Q0),3))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
