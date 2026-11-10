# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import time
import numpy as np
import torch
from rapido import Canales, Gram, pack, N
torch.set_num_threads(4)
torch.manual_seed(0)
R, B, C = 3, 20, 7
u = torch.randn(R, B, N, dtype=torch.float64); u /= u.norm(dim=2, keepdim=True)
W = torch.randn(R, B, C, dtype=torch.float64)
i, j, wg = pack("cpu", torch.float64)
def ref(u, W):
    s = u[:, :, i] * u[:, :, j] * wg
    return torch.einsum("rbp,rbc->prc", s, W).reshape(-1, R * C)
a = u.clone().requires_grad_(True); b = W.clone().requires_grad_(True)
c = u.clone().requires_grad_(True); d = W.clone().requires_grad_(True)
V = torch.randn(len(i), R * C, dtype=torch.float64)
x1, x2 = ref(a, b), Canales.apply(c, d)
print("adelante", float((x1 - x2).abs().max()))
(x1 * V).sum().backward(); (x2 * V).sum().backward()
print("du", float((a.grad - c.grad).abs().max()), "dw", float((b.grad - d.grad).abs().max()))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
