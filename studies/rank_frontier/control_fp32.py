# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Check the FP32 GEMM path against FP64 on the same point: value, gradient, speed."""
from gpu_lib import *
d = np.load(ROOT + "frontera_C44.npz")
th = torch.tensor(d["th"], device=DEV, dtype=DT)
w = torch.tensor(d["w"], device=DEV, dtype=DT)
os.environ["QVC_FP32"] = "0"
a = Model()
os.environ["QVC_FP32"] = "1"
b = Model()
out = {}
for name, m in (("fp64", a), ("fp32", b)):
    t_ = th.clone().requires_grad_(True); w_ = w.clone().requires_grad_(True)
    f = m.loss(t_, w_); f.backward()
    out[name] = (float(f) ** .5, t_.grad.clone(), w_.grad.clone())
    torch.cuda.synchronize(); t0 = time.time()
    for _ in range(20):
        t_.grad = None; w_.grad = None
        m.loss(t_, w_).backward()
    torch.cuda.synchronize()
    print(name, "error_2", out[name][0], "ms", (time.time() - t0) / 20 * 1000, flush=True)
g = lambda x, y: float((x - y).norm() / y.norm())
print("gradiente: diferencia relativa angulos", g(out["fp32"][1], out["fp64"][1]), "pesos", g(out["fp32"][2], out["fp64"][2]), flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
