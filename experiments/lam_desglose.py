# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Where the Lambda_h2 gap to the public base sits: per group, the L1 part and the w_B part. Usage: lam_desglose.py A.npz B.npz"""
import sys

import numpy as np

for path in sys.argv[1:]:
    with np.load(path) as z:
        w = np.asarray(z["W"], np.float64)
        H = np.asarray(z["H2_I"], np.float64)
    l1 = np.abs(w).sum(axis=1)
    s = w.sum(axis=1)
    lam = 0.25 * (l1 + np.abs(H)) ** 2
    print(path)
    print(" forma", w.shape, "Lambda_h2", round(lam.sum(), 4), "| solo L1", round(0.25 * (l1 ** 2).sum(), 4),
          "| cruce", round(0.5 * (l1 * np.abs(H)).sum(), 4), "| H2", round(0.25 * (H ** 2).sum(), 4))
    print(" por grupo", np.round(lam.sum(axis=1), 3))
    print(" L1 por grupo", np.round(l1.sum(axis=1), 3), "|H| por grupo", np.round(np.abs(H).sum(axis=1), 3))
    print(" |sum w| / L1 medio", round(float((np.abs(s) / l1).mean()), 4), "canales con signo mixto", int(((np.abs(s) + 1e-9) < l1 * 0.999).sum()), "de", l1.size)
    print(" pesos nulos (<1e-6)", int((np.abs(w) < 1e-6).sum()), "de", w.size, "| max |w|", round(float(np.abs(w).max()), 4))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
