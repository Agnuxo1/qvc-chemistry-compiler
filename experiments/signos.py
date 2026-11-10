# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Mixed-sign channels and L1 of w at each stage of the chain. Usage: signos.py A.npz B.npz ..."""
import sys
import numpy as np
for path in sys.argv[1:]:
    with np.load(path) as z:
        keys = z.files
        w = np.asarray(z["W"] if "W" in keys else z["w"], np.float64)
        H = np.asarray(z["H2_I"], np.float64) if "H2_I" in keys else None
    l1 = np.abs(w).sum(axis=1)
    s = w.sum(axis=1)
    P = np.clip(w, 0, None).sum(axis=1)
    N = -np.clip(w, None, 0).sum(axis=1)
    menor = np.minimum(P, N)
    txt = f"{path}\n forma {w.shape} L1^2/4 {0.25*(l1**2).sum():.4f} | mixtos {int((menor > 1e-3*l1).sum())}/{l1.size} | masa minoritaria {menor.sum():.4f} de L1 {l1.sum():.3f} | nulos {int((np.abs(w)<1e-6).sum())} | D {2*(P*N).sum():.4f}"
    if H is not None:
        txt += f" | Lambda_h2 {0.25*((l1+np.abs(H))**2).sum():.4f} | |H| {np.abs(H).sum():.3f}"
    print(txt)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
