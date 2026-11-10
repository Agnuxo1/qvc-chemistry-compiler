# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import numpy as np
from quant_lib import *
st,tei=load(); del tei
words,tree,w,brot=st["words"],st["tree"],st["w"],st["brot"]
R,B,C=w.shape; step=np.pi/64
th=words[N:]*(np.pi/2**(brot-1)); u,D=decode_jac(th[:B],tree)
X=channels(u[None],w[:1])
H=group_hessian(u,D,w[0],X,step)
rng=np.random.default_rng(0); f=np.sort(rng.choice(H.shape[0],3000,replace=False))
Hf,o,d=group_hessian_free(u,D,w[0],X,step,f)
print("max dif",np.abs(Hf-H[np.ix_(o,o)]).max(),"escala",np.abs(H).max(),"diag",np.abs(d-np.diag(H)[o]).max(),"orden",bool((np.diff(d)>=0).all()))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
