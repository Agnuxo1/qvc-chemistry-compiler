# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import sys,time,numpy as np
V=(_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers")
sys.path.insert(0,V)
from dfthcsos.verify import evaluate_circuits, evaluate_words, load_inputs, load_tree_edges
run=(_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/dfthcsos")
t=time.time()
inp=load_inputs(run+"/submission.npz")
tree=load_tree_edges(None,run)
r=evaluate_circuits(inp,run,tree)
print({k:(v if not hasattr(v,'shape') else v.shape) for k,v in r.items() if k not in('resources','metrics')})
W8=np.asarray(r["angle_words"])
print(W8.shape,W8.dtype,time.time()-t, r["metrics"])
np.savez((_HOME + "/work/chem_state.npz"),words=W8,tree=np.asarray(tree),w=inp.w,W=inp.W,S=inp.S,beta_1=inp.beta_1,brot=r["brot"])
ref=inp.ref
print(ref.keys(), ref["tei"].dtype, ref["electrons"], ref["ecore"])
np.save((_HOME + "/work/tei.npy"),np.asarray(ref["tei"]))
np.save((_HOME + "/work/oei.npy"),np.asarray(ref["oei"]))
print("w",inp.w.shape,"W",inp.W.shape,"bytes",(W8==0).mean(),"palabras cero por columna min/max",(W8==0).mean(0).min(),(W8==0).mean(0).max())

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
