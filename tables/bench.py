# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import time, numpy as np, torch
from rapido import Canales, Gram, pack, N
torch.set_num_threads(4)
R, B, C = 8, 143, 45
u = torch.randn(R, B, N); u /= u.norm(dim=2, keepdim=True); W = torch.randn(R, B, C) * .01
G = torch.randn(2926, 2926); i, j, wg = pack("cpu", torch.float32)
def old(u, W):
    return torch.einsum("rbp,rbc->prc", u[:, :, i] * u[:, :, j] * wg, W).reshape(-1, R * C)
for name, f in (("indices", old), ("analitico", Canales.apply)):
    a, b = u.clone().requires_grad_(True), W.clone().requires_grad_(True)
    t = [0, 0]
    for k in range(4):
        t0 = time.time(); X = f(a, b); t1 = time.time(); l = Gram.apply(X, G); t2 = time.time(); l.backward(); t3 = time.time()
        if k: print(name, "canales", round(t1 - t0, 3), "gram", round(t2 - t1, 3), "atras", round(t3 - t2, 3), flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
