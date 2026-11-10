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
a0=np.array([float(Fraction(a)) for a in ang])/2
xs=np.arange(1,N+1,dtype=np.float64)
tgt=1/np.sqrt(xs); tol=2.0**-24/np.sqrt(xs)
free0=[k for k in range(K) if Fraction(ang[k])%Fraction(1,4)!=0]
fixed=[k for k in range(K) if k not in free0]
Bf0=bits[free0].astype(np.float32)
fixphase=(bits[fixed].astype(np.float64)*a0[fixed][:,None]).sum(0)
intpart=np.round(a0[free0].astype(np.float64)@Bf0.astype(np.float64)+fixphase-tgt)
def solve(drop):
    free=[i for i,k in enumerate(free0) if k not in drop]
    B=Bf0[free]
    af=a0[np.array(free0)[free]].copy()
    def err(a):
        return (a.astype(np.float64)@B.astype(np.float64))+fixphase-tgt-intpart
    e=err(af)
    act=set(np.argsort(tol-np.abs(e))[:6000].tolist())
    best=-1
    for it in range(30):
        idx=np.array(sorted(act))
        A=B[:,idx].T.astype(np.float64)
        rhs=tgt[idx]+intpart[idx]-fixphase[idx]
        nv=len(free)+1
        Aub=np.vstack([np.hstack([A,np.ones((len(idx),1))]),np.hstack([-A,np.ones((len(idx),1))])])
        bub=np.concatenate([tol[idx]+rhs,tol[idx]-rhs])
        sc=2.0**34
        c=np.zeros(nv);c[-1]=-1
        bub2=(bub-Aub[:,:-1]@af)*sc
        res=linprog(c,A_ub=Aub,b_ub=bub2,bounds=[(-1e7,1e7)]*(nv-1)+[(None,None)],method='highs')
        if res.status!=0: return None,it
        an=af+res.x[:-1]/sc
        slack=tol-np.abs(err(an))
        m=slack.min(); t=res.x[-1]/sc
        if m>best: best=m;ab=an
        if t-m<2e-3*abs(t): return (t,m,ab),it
        act.update(np.argsort(slack)[:4000].tolist())
    return (t,best,ab),it
def cc(m,nrot):
    eps=math.pi*m/nrot
    return (nrot*(0.56*math.log2(1/eps)+5.3)+1)/4
base=None
for drop in ([],[22],[23],[22,23],[47],[46],[45],[18],[17],[16]):
    t0=time.time()
    r,it=solve(set(drop))
    if r is None: print(drop,'infactible'); continue
    t,m,_=r
    nrot=41-len(drop)
    print(drop,'t',t,'m',m,'it',it,'coste T/4',cc(m,nrot) if m>0 else None,round(time.time()-t0),flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
