# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os
os.environ["QVC_DEV"] = "cpu"
from gpu_lib import *
m = Chem()
c = np.load(ROOT + "chem_state.npz")
R, B, C = c["w"].shape
th = torch.tensor(c["words"][N:] * (np.pi / 2 ** (int(c["brot"]) - 1)), dtype=DT)
w = torch.tensor(c["w"], dtype=DT)
print("error_2", m.error2(th, w), "oficial 0.01999999978")
L, g, l = m.costs(th, w, m.W0)
print("Lambda", float(L), "oficial 282.8058164357")
print("E_gap", float(g), "oficial 3.9148980015")
print("lambda_eff", float(l), "oficial 46.8933409429")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
