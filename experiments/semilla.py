# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Writes <dst> with only u and w of <src>, so that ajuste.py starts a new schedule at step 0 from that table.

Usage (in the work directory): python semilla.py mejor_8x143x44p.npz seed_8x143x44pb.npz
"""
import os
import sys

import numpy as np

src, dst = sys.argv[1:3]
with np.load(src) as d:
    u, w = d["u"], d["w"]
    extra = {k: float(d[k]) for k in ("e", "step") if k in d.files}
tmp = dst + ".tmp.npz"
np.savez(tmp, u=u, w=w)
os.replace(tmp, dst)
print("ok", dst, u.shape, w.shape, extra)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
