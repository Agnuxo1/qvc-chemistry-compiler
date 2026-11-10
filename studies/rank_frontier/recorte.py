# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Cut channels of the public shape and retrain: (8, 143, 44) -> (8, 143, C).

Channels of a group can be rotated freely, so the cut keeps the top right singular
directions of each group: the best truncation of X_r. FP32 GEMMs for most of the
run, FP64 for the last stretch. Usage: recorte.py <wall_s_total> <C> [<C> ...]
"""
import sys
from gpu_lib import *

WALL = float(sys.argv[1])
CS = [int(x) for x in sys.argv[2:]]
m = Model()
m.fast = True
m.G32 = m.Gp.float()
d = np.load(ROOT + "frontera_C44.npz")
th0 = torch.tensor(d["th"], device=DEV, dtype=DT)
w0 = torch.tensor(d["w"], device=DEV, dtype=DT)
d.close()
R, B, C0 = w0.shape
print("inicio", m.error2(th0, w0), flush=True)


def cut(w, Cn):
    u = m.decode(th0)
    s = (u[:, m.i] * u[:, m.j] * m.wgt).reshape(R, B, -1)
    out = []
    for r in range(R):
        X = s[r].T @ w[r]
        _, sv, Vh = torch.linalg.svd(X, full_matrices=False)
        out.append(w[r] @ Vh[:Cn].T)
    return torch.stack(out)


per = WALL / len(CS)
for Cn in CS:
    t0 = time.time()
    th, w = th0, cut(w0, Cn)
    print(f"C={Cn} tras recortar {m.error2(th, w):.6f}", flush=True)
    best = 9.0
    m.fast = True
    while time.time() - t0 < per:
        left = per - (time.time() - t0)
        if left < 0.2 * per:
            m.fast = False
        th, w, e = lbfgs(m, th, w, 10 ** 7, every=500, tag=f"C={Cn}{'' if m.fast else ' fp64'}", wall=min(240, left))
        if e < best:
            best = e
            np.savez(ROOT + f"recorte_C{Cn}.tmp.npz", th=th.cpu().numpy(), w=w.cpu().numpy())
            os.replace(ROOT + f"recorte_C{Cn}.tmp.npz", ROOT + f"recorte_C{Cn}.npz")
    print(f"fin C={Cn} error_2 {best:.6f}", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
