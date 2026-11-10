# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""How much of the public base's error budget is rounding: refit its weights at fixed words towards a very low error_2.

The words stay as published; only w and W move, so the error_2 reached is the floor of those words. Usage: mirar_base2.py <submission.npz> <target_mHa>
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys

sys.path.insert(0, (_HOME + "/compiler"))
import numpy as np

import quantize  # noqa: F401
import build  # noqa: F401
import reajuste  # noqa: F401  (installs the jitter on L-BFGS-B)
import refit_al

d = np.load(sys.argv[1])
data = {k: np.array(d[k]) for k in d.files if k != "offset_W"}
data["brot"] = np.array(8)
refit_al.solve(data, float(sys.argv[2]), 0.0005, 25, 3000, 0, log=lambda *x: print(*x, flush=True))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
