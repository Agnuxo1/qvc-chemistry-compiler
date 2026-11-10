# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Do free low bits make the loaders cheaper? One table, words cut per 16-row block and edge.

Rows sorted by strength inside each group make blocks homogeneous; each (block, edge) then
drops low bits by water-filling on the measured sensitivities, and tensorqrom compiles the delta
of one circuit with outputs grouped by how many blocks use them.
Usage: prueba_bits.py <ratio> <circuit> [<circuit> ...]; ratio 0 keeps the words.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import json
import sys
import time

import numpy as np

sys.path.insert(0, (_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/dfthc_refit"))
import tensorqrom as tq  # noqa: E402

ratio = float(sys.argv[1])
circs = [int(x) for x in sys.argv[2:]]
R, B, J, brot = 8, 143, 5, 8
with np.load((_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/refit_845.npz")) as d:
    words = d["angle_words"].astype(np.int64)
with np.load("sens_845.npz") as d:
    h = d["h"].astype(float)
n1 = 76
A = len(words)
s = np.where(words >= 128, words - 256, words)
hh = np.zeros(s.shape)
hh[n1:] = h
hh[:n1] = np.inf                                    # one-body rows keep every bit here
for r in range(R):                                   # sort rows of each group by strength
    a = n1 + r * B
    o = a + np.argsort(-h[r * B:(r + 1) * B].sum(1))
    s[a:a + B], hh[a:a + B] = s[o].copy(), hh[o].copy()
blk = np.arange(A) // 16
nb = blk.max() + 1
hb = np.zeros((nb, 75))
np.add.at(hb, blk, hh)
S0 = h.sum() / 12
if ratio > 0:
    lo, hi = 1e-12, 1e3
    fin = np.isfinite(hb)
    for _ in range(80):
        L = (lo * hi) ** .5
        k = np.zeros(hb.shape, int)
        k[fin] = np.clip(np.floor(0.5 * np.log2(np.maximum(12 * L / np.maximum(hb[fin], 1e-300), 1e-300))), 0, 7)
        tot = (hb[fin] * 4.0 ** k[fin]).sum() / 12
        if tot > ratio * S0:
            hi = L
        else:
            lo = L
    kr = k[blk]
    q = 2 ** kr
    s2 = np.round(s / q).astype(np.int64) * q
    s2 = np.clip(s2, -64, 64 - q)
else:
    kr = np.zeros(s.shape, int)
    s2 = s.copy()
raw = (hh[n1:] * (s2[n1:] - s[n1:]) ** 2).sum()
print(f"ratio {ratio}: ruido crudo {raw*1e6:.0f} (uniforme {S0*1e6:.0f}), bits medios {7 - kr[n1:].mean():.2f}", flush=True)
w2 = s2 % 256
batches = w2.reshape(A, 15, J).transpose(1, 0, 2)
out = {}
for c in circs:
    t0 = time.time()
    d = batches[c] ^ (batches[c - 1] if c else 0)
    C = tq.anf_tensor(d, brot, 4)
    O = C.shape[2]
    bits = np.zeros((A + (-A) % 16, O), np.uint8)
    for j in range(J):
        for b in range(brot - 1):
            bits[:A, j * (brot - 1) + b] = (d[:, j] >> b) & 1
    alive = bits.reshape(-1, 16, O).any(1).sum(0)
    perm = list(np.argsort(-alive))
    sizes = [6] * (O // 6) + ([O % 6] if O % 6 else [])
    terms = tq.shared(C[:, :, perm], sizes, trials=4, seed=c)
    out[c] = len(terms)
    print(f"circuito {c}: productos {len(terms)} cache {tq.cost(terms, C.shape[0], C.shape[1]) - len(terms)} bloques vivos {sorted(alive.tolist())[::6]} t={time.time()-t0:.0f}s", flush=True)
print(json.dumps(dict(ratio=ratio, productos=out)))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
