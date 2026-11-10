# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Is each stall a real limit? Compares every saved shape with the rank bound of the target.

Best rank-K PSD approximation of G: keep the top K positive eigenvalues (Eckart-Young),
so sqrt(sum of everything else squared) is a floor no (R, B, C) with R*C = K can beat.
Also reports the FP64 gradient, the rank actually used and the dead channels.
"""
import os
import sys

J1 = os.environ.get("QVC_RUNS_A", "work/runs_a/")  # run folder of the shape sweep (forma_*.npz)
J2 = os.environ.get("QVC_RUNS_B", "work/runs_b/")  # run folder of the channel cuts (recorte_*.npz)
sys.path.insert(0, J1)
os.environ["QVC_ROOT"] = J1
os.environ["QVC_DEV"] = "cpu"
from gpu_lib import *  # noqa: E402

torch.set_num_threads(8)
m = Model()
m.fast = False
ev = torch.linalg.eigvalsh(m.Gp).flip(0)
print("autovalores: positivos", int((ev > 0).sum()), "negativos", int((ev < 0).sum()),
      "min", float(ev[-1]), "max", float(ev[0]))
print("parte negativa sola (suelo para cualquier rango)", float(torch.sqrt((ev[ev < 0] ** 2).sum())))


def bound(K):
    pos = ev.clamp(min=0)
    return float(torch.sqrt((ev ** 2).sum() - (pos[:K] ** 2).sum()))


for K in (280, 304, 320, 336, 344, 348, 350, 352, 360, 384, 416, 448, 512):
    print(f"cota rango {K}: {bound(K):.6f}")

for path in (J2 + "recorte_C40.npz", J2 + "recorte_C38.npz", J1 + "forma_R7_C50.npz", J1 + "forma_R6_C58.npz",
             J2 + "frontera_C44.npz"):
    with np.load(path) as d:
        th = torch.tensor(d["th"], dtype=DT, requires_grad=True)
        w = torch.tensor(d["w"], dtype=DT, requires_grad=True)
    R, B, C = w.shape
    f = m.loss(th, w)
    f.backward()
    e = float(torch.sqrt(f))
    X = m.channels(th.detach(), w.detach())
    sv = torch.linalg.svdvals(X)
    colnorm = X.reshape(X.shape[0], R, C).norm(dim=0)
    print(f"{os.path.basename(path):22s} R={R} B={B} C={C} K={R*C} error_2 {e:.6f} cota {bound(R*C):.6f}"
          f" |g_th| {float(th.grad.norm()):.3e} |g_w| {float(w.grad.norm()):.3e} f {float(f):.4e}"
          f" sv_min {float(sv[-1]):.3e} sv_max {float(sv[0]):.3e} rango(1e-6) {int((sv > 1e-6 * sv[0]).sum())}"
          f" nan {bool(torch.isnan(th).any() or torch.isnan(w).any())}", flush=True)
    print("   norma min de canal por grupo", [round(float(x), 5) for x in colnorm.min(1).values])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
