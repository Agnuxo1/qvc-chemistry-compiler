# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Erasure coding of the angle table: each output bit keeps only low-degree patterns per block.

An output bit whose pattern in every 16-address block lies in a small space of functions costs
about half that dimension in Toffolis instead of 6.3. Inside a block, positions are served by
weight (harm of flipping that bit there) with a greedy matroid pass, so weak rows absorb the
restriction. Levels: dimension 0, 4, 10 and 15 over the low monomials, plus the free constant.
Usage: codigo.py <mu> [circuit to compile ...]; mu is mHa^2 of raw noise per product saved.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import json
import pickle
import sys
import time
from itertools import combinations

import numpy as np

sys.path.insert(0, (_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/dfthc_refit"))
import tensorqrom as tq  # noqa: E402

MU = float(sys.argv[1]) * 1e-6
COMP = [int(x) for x in sys.argv[2:]]
R, B, J, brot = 8, 143, 5, 8
with np.load((_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/refit_845.npz")) as d:
    words = d["angle_words"].astype(np.int64)
with np.load("sens_845.npz") as d:
    h = d["h"].astype(float)
n1 = 76
A = len(words)
hh = np.zeros(words.shape)
hh[n1:] = h
ONE = float(__import__("os").environ.get("QVC_ONE", "0"))
hh[:n1] = ONE * 1e-6                                 # mHa^2 per step^2 on the one-body rows
FIRST = 0 if ONE else (n1 + 15) // 16                # without a weight their blocks stay as they are
NB = -(-A // 16)
EST = {0: 0.0, 4: 1.6, 10: 4.2, 15: 6.3}             # products per output, from (a-1)(m-1) ~ 71


def functions(deg):
    """Values of the constant and of every monomial of degree <= deg at the 16 positions."""
    masks = [0] + [sum(1 << b for b in c) for k in range(1, deg + 1) for c in combinations(range(4), k)]
    return [[int((p & m) == m) for m in masks] for p in range(16)]


LV = {0: functions(0), 4: functions(1), 10: functions(2), 15: functions(4)}


def fit_block(vals, want, wts, nb):
    """Greedy max-weight solve: returns the pattern and the weight lost. vals: 16 lists of nb bits."""
    piv = {}
    lost = 0.0
    fixed = []
    for p in sorted(range(16), key=lambda q: -wts[q]):
        if wts[p] <= 0:
            continue
        v = sum(b << i for i, b in enumerate(vals[p])) | (want[p] << nb)
        low = (1 << nb) - 1
        while v & low:
            q = (v & low).bit_length() - 1
            if q in piv:
                v ^= piv[q]
            else:
                piv[q] = v
                break
        else:
            if v >> nb:
                lost += wts[p]
    # back-substitute with free coordinates at zero
    x = [0] * nb
    for q in sorted(piv):
        v = piv[q]
        r = v >> nb
        for i in range(q):
            if v >> i & 1:
                r ^= x[i]
        x[q] = r
    pat = [sum(a & b for a, b in zip(vals[p], x)) & 1 for p in range(16)]
    return pat, lost


wbits = (words[:, :, None] >> np.arange(7)[None, None, :]) & 1      # (A, 75, 7)
t0 = time.time()
plan = {}
tot_loss = 0.0
tot_prod = 0.0
hist = {k: 0 for k in LV}
newD = {}
for c in range(15):
    cols = list(range(5 * c, 5 * c + 5))
    prev = list(range(5 * c - 5, 5 * c)) if c else [None] * 5
    D = np.zeros((A, J), np.int64)
    for jw, (cj, pj) in enumerate(zip(cols, prev)):
        D[:, jw] = words[:, cj] ^ (words[:, pj] if pj is not None else 0)
    for jw, cj in enumerate(cols):
        for k in range(7):
            pj = prev[jw]
            tgt = (wbits[:, cj, k] ^ (wbits[:, pj, k] if pj is not None else 0)).astype(int)
            wt = hh[:, cj] * 4.0 ** k
            best = None
            res = {}
            for lv, vals in LV.items():
                nb = len(vals[0])
                loss, pats = 0.0, {}
                for b in range(FIRST, NB):
                    a0 = 16 * b
                    n = min(16, A - a0)
                    want = [int(x) for x in tgt[a0:a0 + n]] + [0] * (16 - n)
                    wts = [float(x) for x in wt[a0:a0 + n]] + [0.0] * (16 - n)
                    pat, l = fit_block(vals, want, wts, nb)
                    loss += l
                    pats[b] = pat
                res[lv] = (loss, pats)
                cost = loss + MU * EST[lv]
                if best is None or cost < best[0]:
                    best = (cost, lv)
            lv = best[1]
            hist[lv] += 1
            tot_loss += res[lv][0]
            tot_prod += EST[lv]
            plan[(c, jw, k)] = lv
            for b, pat in res[lv][1].items():
                a0 = 16 * b
                n = min(16, A - a0)
                bit = np.array(pat[:n], np.int64)
                D[a0:a0 + n, jw] = (D[a0:a0 + n, jw] & ~(1 << k)) | (bit << k)
                if k == 6:
                    D[a0:a0 + n, jw] = (D[a0:a0 + n, jw] & ~(1 << 7)) | (bit << 7)
    newD[c] = D
    print(f"circuito {c}: niveles {[sum(plan[(c, j, k)] == lv for j in range(5) for k in range(7)) for lv in LV]} t={time.time()-t0:.0f}s", flush=True)
S0 = h.sum() / 12
print(f"mu {MU*1e6}: perdida cruda {tot_loss*1e6:.0f} mHa2 (x{1 + tot_loss / S0:.3f} del uniforme {S0*1e6:.0f}); productos estimados {tot_prod:.0f} (+ una parte fija), niveles {hist}", flush=True)
pickle.dump(dict(plan=plan, newD=newD, loss=tot_loss), open(f"codigo_{sys.argv[1]}.pkl", "wb"))
for c in COMP:
    t1 = time.time()
    d = newD[c]
    C = tq.anf_tensor(d, brot, 4)
    O = C.shape[2]
    lv = [plan[(c, o // 7, o % 7)] for o in range(O)]
    perm = sorted(range(O), key=lambda o: -lv[o])
    sizes = []
    for L, m in ((15, 6), (10, 8), (4, 8), (0, 8)):
        n = sum(x == L for x in lv)
        sizes += [m] * (n // m) + ([n % m] if n % m else [])
    terms = tq.shared(C[:, :, perm], sizes, trials=3, seed=c)
    print(f"compilado circuito {c}: productos {len(terms)} (referencia 237); grupos {sizes} t={time.time()-t1:.0f}s", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
