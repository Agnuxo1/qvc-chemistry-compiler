# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import sys,time,numpy as np,scipy.linalg as sl
from quant_lib import *
st,tei=load(); G=target(tei,st["S"]); del tei
words,tree,w,brot=st["words"],st["tree"],st["w"],st["brot"]
R,B,C=w.shape; BITS=7; step=np.pi/2**(BITS-1)
z=words[N:].astype(float)*2.0**(BITS-brot)
state=lambda z:decode(z*step,tree).reshape(R,B,N)
e,E,Xm=error2(state(z),w,G); print("inicio",e)
r=7; rows=slice(r*B,(r+1)*B)
uu,D=decode_jac(z[rows]*step,tree); X_g=Xm[:,r*C:(r+1)*C]
H0=group_hessian(uu,D,w[r],X_g,step); b=group_gradient(uu,D,w[r],X_g,E,step)
d=np.diag(H0).copy(); print("mean diag",d.mean(),"|b|",np.abs(b).max())
def run(alpha,order):
    H=H0.copy(); H[np.diag_indices_from(H)]+=alpha*d.mean()
    o={"asc":np.argsort(d),"nat":np.arange(d.size)}[order]
    L=sl.cholesky(H[np.ix_(o,o)],lower=True,check_finite=False,overwrite_a=True); del H
    delta=-sl.cho_solve((L,True),b[o],check_finite=False)
    y=z[rows].ravel()[o]+delta; n=y.size; err=np.zeros(n); zq=np.empty(n); Ld=np.diag(L).copy()
    for k in range(n-1,-1,-1):
        c=y[k]-(L[k+1:,k]@err[k+1:])/Ld[k]; zq[k]=np.round(c); err[k]=zq[k]-y[k]
    zn=z.copy(); f=zn[rows].ravel(); f[o]=zq; zn[rows]=f.reshape(B,N-1)
    pred=float(np.sqrt(((L.T@err)**2).sum()))
    return error2(state(zn),w,G)[0],pred,np.abs(delta).max(),np.abs(zq-z[rows].ravel()[o]).max()
print("redondeo solo grupo 7",error2(state(np.where(np.arange(z.shape[0])[:,None]//B==r,np.round(z),z)),w,G)[0])
for order in ("asc","nat"):
    for a in (1e-4,1e-3,1e-2,3e-2,1e-1,3e-1,1.0):
        t=time.time(); print(order,a,[round(float(x),4) for x in run(a,order)],round(time.time()-t,1),flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
