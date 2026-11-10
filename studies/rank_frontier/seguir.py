# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Continue training one saved shape for a short ticket, then save and exit.

Usage: seguir.py <shape.npz> <wall_s>. Short tickets let the FIFO queue interleave
other work; the FP32 GEMM path is on, and reported errors stay FP64.
"""
import sys
from gpu_lib import *

src, WALL = sys.argv[1], float(sys.argv[2])
m = Model()


def read(path):
    """Windows keeps an open NpzFile locked, so close it before replacing the file."""
    with np.load(path) as d:
        return (torch.tensor(d["th"], device=DEV, dtype=DT), torch.tensor(d["w"], device=DEV, dtype=DT))


th, w = read(ROOT + src)
e0 = m.error2(th, w)
tmp = ROOT + src + ".tmp.npz"
if os.path.exists(tmp):                      # a ticket that could not replace the file
    t2, w2 = read(tmp)
    e2 = m.error2(t2, w2)
    print("rescate", e0, "->", e2, flush=True)
    if e2 < e0:
        th, w, e0 = t2, w2, e2
    os.remove(tmp)
th2, w2, e, t0, best = th, w, e0, time.time(), e0
while time.time() - t0 < WALL:              # save often: a queue cut must not lose the run
    th2, w2, e = lbfgs(m, th2, w2, 10 ** 7, every=500, tag=src, wall=min(240, WALL - (time.time() - t0)))
    stalled = e > best - 1e-7               # a stalled L-BFGS spins for nothing: free the ticket
    if e < best:
        best = e
        np.savez(tmp, th=th2.cpu().numpy(), w=w2.cpu().numpy())
        os.replace(tmp, ROOT + src)
    if stalled:
        print("sin mejora en el tramo", e, flush=True)
        break
print(json.dumps(dict(src=src, antes=e0, despues=e, t=time.strftime("%H:%M"))), flush=True)
with open(ROOT + "seguir.jsonl", "a") as f:
    f.write(json.dumps(dict(src=src, antes=e0, despues=e, t=time.strftime("%Y-%m-%d %H:%M"))) + "\n")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
