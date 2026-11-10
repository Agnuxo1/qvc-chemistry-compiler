# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Shrink the table: drop the weakest groups, regrow channels, retrain on GPU.

Usage: formas.py <R> <C> <iters> <wall_s>. Addresses fall from 1220 to 76 + R*143,
which the cost model prices at T*Q 0.906 for R = 7 and 0.811 for R = 6. Reference:
gate 0.02, and quantization at 8 bits adds about 0.002.
"""
import sys
from gpu_lib import *

Rn, Cn, ITERS, WALL = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
m = Model()
d = np.load(ROOT + "frontera_C44.npz")
th = torch.tensor(d["th"], device=DEV, dtype=DT)
w = torch.tensor(d["w"], device=DEV, dtype=DT)
R, B, C = w.shape
X = m.channels(th, w).reshape(-1, R, C)
power = (X * X).sum((0, 2))
keep = torch.argsort(power, descending=True)[:Rn].sort().values
print("potencia por grupo", [round(float(x), 3) for x in power], "conservo", keep.tolist(), flush=True)
th = th.reshape(R, B, N - 1)[keep].reshape(Rn * B, N - 1)
w = w[keep]
print("tras quitar grupos", m.error2(th, w), flush=True)
w, top, nrm = grow_channels(m, th, w, Cn - C)
print(f"sembrado C={Cn} residuo {nrm:.5f} propios {[round(x, 5) for x in top[:4]]} error_2 {m.error2(th, w):.5f}", flush=True)
th, w, e = lbfgs(m, th, w, ITERS, every=500, tag=f"R={Rn} C={Cn}", wall=WALL)
np.savez(ROOT + f"forma_R{Rn}_C{Cn}.npz", th=th.cpu().numpy(), w=w.cpu().numpy(), keep=keep.cpu().numpy())
print("fin", Rn, Cn, e, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
