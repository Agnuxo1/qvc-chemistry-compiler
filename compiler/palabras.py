# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""From the rounding state to the words the tail of the chain reads.

Usage: palabras.py <red_tag.npz> <rounded.npz> [codes]. Moves each row into the signed gauge,
which keeps every vector up to sign and keeps bit 0.
"""
import sys

import numpy as np

import encode
import arbol_env  # noqa: F401  (a tree other than the public one, if QVC_TREE is set)
import onebody
import rmcode

src, out = sys.argv[1], sys.argv[2]
spec = sys.argv[3] if len(sys.argv) > 3 else ""
BROT = 8
with np.load(src) as d:
    assert d["fr"].all(), "rounding not finished"
    k = np.round(d["qv"]).astype(np.int64)
    w = d["w"].astype(float)
edges = encode.log_depth_tree()
raw = k % (1 << BROT)
words = onebody.signed_gauge(raw, edges, BROT)
deg = rmcode.parse(spec, edges.shape[0], BROT)
ccols = np.flatnonzero(deg.any(axis=1))
rmcode.check(words, 76 + np.arange(len(words)), deg)
drift = np.abs(np.abs(np.sum(encode.decode(raw, edges, BROT) * encode.decode(words, edges, BROT), axis=1)) - 1)
assert drift.max() < 1e-9, "gauge changed a vector"
np.savez(out, words=words, w=w, brot=BROT, coded=ccols, coded2=ccols[:0], codes=deg)
print("palabras", words.shape, "codigos", len(ccols), "guardado", out)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
