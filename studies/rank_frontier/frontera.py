# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Rank frontier: continuous floor of error_2 as channels are added.

First unit of GPU work. Checks the packed model against the CPU reference, then
for each C warm-starts from the previous shape and runs L-BFGS on angles and
weights. Reference: CPU floor 0.0192045 at (8, 143, 44); gate 0.02.
"""
import sys
from gpu_lib import *

ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
CS = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [44, 48, 52, 56]
WALL = float(sys.argv[3]) if len(sys.argv) > 3 else 420
m = Model()
c = np.load(ROOT + "chem_state.npz")
R, B, C0 = c["w"].shape
nth = R * B * (N - 1)
p = np.load(ROOT + "piloto4_p.npy")
th = torch.tensor(p[:nth].reshape(R * B, N - 1), device=DEV, dtype=DT)
w = torch.tensor(p[nth:].reshape(R, B, C0), device=DEV, dtype=DT)
print("dispositivo", DEV, torch.cuda.get_device_name(0) if DEV == "cuda" else "", flush=True)
print("control: error_2 inicial", m.error2(th, w), "debe ser 0.0192045", flush=True)
t = time.time()
for _ in range(10):
    th.requires_grad_(True)
    m.loss(th, w).backward()
    th = th.detach()
if DEV == "cuda":
    torch.cuda.synchronize()
print("ms por evaluacion con gradiente", (time.time() - t) * 100, flush=True)
res = []
for Cn in CS:
    if Cn > w.shape[2]:
        e0 = m.error2(th, w)
        w, top, nrm = grow_channels(m, th, w, Cn - w.shape[2])
        print(f"C={Cn} residuo {nrm:.6f} valores propios {[round(x,6) for x in top[:6]]} tras sembrar {m.error2(th,w):.6f} (antes {e0:.6f})", flush=True)
    th, w, e = lbfgs(m, th, w, ITERS, tag=f"C={Cn}", wall=WALL)
    res.append(dict(C=Cn, error_2=e))
    np.savez(ROOT + f"frontera_C{Cn}.npz", th=th.cpu().numpy(), w=w.cpu().numpy())
    json.dump(res, open(ROOT + "frontera.json", "w"), indent=1)
    if DEV == "cuda":
        print("VRAM pico GB", round(torch.cuda.max_memory_reserved() / 2**30, 2), flush=True)
print("fin", res, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
