# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Walk a shape through a path of channel counts on the CPU, in FP64.

One-shot cuts stopped in local minima on 07-11 (C=40 at 0.02139, C=38 at 0.02596). This
tests whether the path matters: cut one step at a time, or grow and cut back to change basin.
Usage: camino.py <src.npz> <tag> <wall_s_per_step> <C> [<C> ...]
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import os
import sys

J1 = _os.environ.get("QVC_RUNS", _HOME + "/work/")
sys.path.insert(0, J1)
os.environ["QVC_ROOT"] = J1
os.environ["QVC_DEV"] = "cpu"
from gpu_lib import *  # noqa: E402

torch.set_num_threads(int(os.environ.get("HILOS", "8")))
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
src, tag, WALL = sys.argv[1], sys.argv[2], float(sys.argv[3])
path = [int(x) for x in sys.argv[4:]]
m = Model()
m.fast = False
with np.load(src) as d:
    th = torch.tensor(d["th"], dtype=DT)
    w = torch.tensor(d["w"], dtype=DT)
print("inicio", w.shape, m.error2(th, w), flush=True)


def cut(th, w, Cn):
    R, B, _ = w.shape
    u = m.decode(th)
    s = (u[:, m.i] * u[:, m.j] * m.wgt).reshape(R, B, -1)
    return torch.stack([w[r] @ torch.linalg.svd(s[r].T @ w[r], full_matrices=False)[2][:Cn].T for r in range(R)])


for Cn in path:
    C = w.shape[2]
    if Cn < C:
        w = cut(th, w, Cn)
    elif Cn > C:
        w = grow_channels(m, th, w, Cn - C)[0]
    print(f"C={Cn} al llegar {m.error2(th, w):.6f}", flush=True)
    t0, best = time.time(), 9.0
    while time.time() - t0 < WALL:
        th, w, e = lbfgs(m, th, w, 10 ** 7, every=500, tag=f"{tag} C={Cn}", wall=min(600, WALL - (time.time() - t0)))
        if e > best - 1e-7:
            print("sin mejora en el tramo", e, flush=True)
            best = min(best, e)
            break
        best = e
        np.savez(OUT + f"camino_{tag}_C{Cn}.tmp.npz", th=th.numpy(), w=w.numpy())
        os.replace(OUT + f"camino_{tag}_C{Cn}.tmp.npz", OUT + f"camino_{tag}_C{Cn}.npz")
    print(f"fin {tag} C={Cn} error_2 {best:.6f}", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
