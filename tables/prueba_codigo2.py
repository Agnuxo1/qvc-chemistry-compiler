# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Real product count of one circuit when more bits carry a code: answers whether stronger codes pay before any rounding.

Bits are projected onto the nearest codeword per block, weighted by the measured curvature, on an already finished
table: the table is no longer valid, only its compilation cost is meaningful, plus the raw damage of the projection.
Usage: prueba_codigo2.py <table.npz> <circuit> <spec> [spec ...]; a spec is rmcode.parse text added to the table's codes.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys
import time

import numpy as np

sys.path.insert(0, (_HOME + "/compiler"))
import compila  # noqa: E402
import rmcode  # noqa: E402

src, k = sys.argv[1], int(sys.argv[2])
with np.load(src) as z:
    words0 = z["angle_words"].astype(np.int64)
    deg0 = z["codes"].astype(np.int64)
with np.load("sens_845.npz") as z:
    h = z["h"].astype(float)
n1 = len(words0) - len(h)
c = np.vstack([np.full((n1, h.shape[1]), h.max()), h])       # one-body rows: not to be flipped in this estimate
blk, pos = np.arange(len(words0)) // 16, np.arange(len(words0)) % 16


def project(words, deg):
    """Nearest codeword per block and coded bit; returns the words and the raw damage in mHa^2."""
    w, damage = words.copy(), 0.0
    for col, bit in zip(*np.nonzero(deg)):
        cw = rmcode.code(int(deg[col, bit]))
        have = (w[:, col] >> bit) & 1
        for b in range(blk.max() + 1):
            r = np.flatnonzero(blk == b)
            words_b = cw[:, pos[r]]
            cost = (c[r, col] * 4.0 ** bit)[None, :] * (words_b != have[r][None, :])
            i = int(cost.sum(1).argmin())
            damage += float(cost[i].sum())
            w[r, col] = (w[r, col] & ~(1 << int(bit))) | (words_b[i].astype(np.int64) << int(bit))
    return w, damage


for spec in sys.argv[3:]:
    t0 = time.time()
    extra = rmcode.parse(spec if spec != "-" else "", deg0.shape[0], deg0.shape[1])
    deg = np.maximum(deg0, extra)
    new = np.where((extra > 0) & (deg0 == 0), extra, 0)
    w, damage = project(words0, new)
    terms, _, _, groups = compila.plan(w, deg, k)
    print(f"{spec}: circuito {k}, {len(terms)} productos, grupos {groups}, dano crudo {damage:.0f} mHa2, {time.time()-t0:.0f} s", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
