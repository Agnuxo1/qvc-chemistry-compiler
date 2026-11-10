# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import numpy as np, math, time, json, sys
from fractions import Fraction
from scipy.optimize import linprog
d=np.load('rot_bits.npz')
n=int(d['n']); N=3133452
bits=np.unpackbits(d['bits'],axis=1)[:,:n].astype(bool)[:,:N]
ang=[str(a) for a in d['ang']]
K=len(ang)
a0=np.array([float(Fraction(a)) for a in ang])/2  # vueltas
xs=np.arange(1,N+1,dtype=np.float64)
tgt=1/np.sqrt(xs)
tol=2.0**-24/np.sqrt(xs)
def clase(s):
    f=Fraction(s)
    if f%Fraction(1,2)==0: return 'c'
    if f%Fraction(1,4)==0: return 't'
    return 'r'
cl=[clase(a) for a in ang]
free=[k for k in range(K) if cl[k]=='r']
fixed=[k for k in range(K) if cl[k]!='r']
print(len(free),len(fixed))
Bf=bits[free].astype(np.float64)   # 41 x N (1 GB)
fixphase=(bits[fixed].astype(np.float64)*a0[fixed][:,None]).sum(0)
def err(af):
    th=af@Bf+fixphase
    e=th-tgt
    e-=np.round(e)
    return e
af=a0[free].copy()
e=err(af)
m=(tol-np.abs(e)).min()
print('margen base',m,'peor |e|/tol',(np.abs(e)/tol).max(), 'x peor',np.argmax(np.abs(e)/tol)+1)
print('margen/tol(max)',m/tol[-1])
def ccost(margin,nrot=41,tof=1281.42,tb=1.0):
    eps=math.pi*margin/nrot
    r=0.56*math.log2(1/eps)+5.3
    C=tof+(tb+nrot*r)/4
    return C,r,62*C
print(ccost(m))
# planos de corte
act=set(np.argsort(tol-np.abs(e))[:4000].tolist())
intpart=np.zeros(N)
intpart=np.round(af@Bf+fixphase-tgt)  # entero fijo
best=None
for it in range(40):
    idx=np.array(sorted(act))
    A=Bf[:,idx].T
    rhs_t=tgt[idx]+intpart[idx]-fixphase[idx]
    # variables: da (41) + t ; maximize t ;  A a - rhs <= tol - t ; -(A a - rhs) <= tol - t
    nv=len(free)+1
    Aub=np.vstack([np.hstack([A,np.ones((len(idx),1))]),np.hstack([-A,np.ones((len(idx),1))])])
    bub=np.concatenate([tol[idx]+rhs_t,tol[idx]-rhs_t])
    sc=2.0**34
    c=np.zeros(nv);c[-1]=-1
    # cambio de variable para condicionamiento: a=a0+da/sc
    bub2=(bub-Aub[:,:-1]@af)*sc
    Aub2=Aub.copy()
    res=linprog(c,A_ub=Aub2,b_ub=bub2,bounds=[(-1e6,1e6)]*(nv-1)+[(None,None)],method='highs')
    if res.status!=0: print('lp',res.message);break
    an=af+res.x[:-1]/sc
    e2=err(an)
    slack=tol-np.abs(e2)
    mnew=slack.min()
    tlp=res.x[-1]/sc
    print(it,'LP t',tlp,'real',mnew,'filas',len(idx),flush=True)
    if best is None or mnew>best[0]: best=(mnew,an.copy())
    if tlp-mnew<1e-3*abs(tlp): break
    new=np.argsort(slack)[:3000]
    act.update(new.tolist())
print('mejor margen',best[0],'vs',m,'razon',best[0]/m)
print(ccost(best[0]),ccost(m))
np.save('ang_lp.npy',best[1]);json.dump({'free':free,'ang':ang},open('ang_lp.json','w'))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
