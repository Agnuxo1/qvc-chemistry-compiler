# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys

import numpy as np

import arboles as A

P = (_HOME + "/")
d = np.load(P + "tables/mejor_8x143x45r.npz")
U, W = d["u"], d["w"]
U = U / np.linalg.norm(U, axis=2, keepdims=True)
R, B, C = W.shape
a = (U ** 2).reshape(R * B, A.N)
rho = (W ** 2).sum(axis=2).reshape(R * B)
rho /= rho.sum()
p = (rho[:, None] * a).sum(0)
base = np.load((_os.environ.get("QVC_PUBLIC_BASE", _HOME + "/third_party/public_baseline") + "/dfthcsos/submission.npz"))["tree_edges"].astype(np.int64)
A.check(base)
trees = {"log_depth": A.log_depth_tree(), "base_publica": base, "huffman": A.huffman(p)}
H = -(p * np.log2(p + 1e-300)).sum()
print("entropia marginal", round(H, 3), "bits; maximo", round(np.log2(76), 3), "| p max", round(float(p.max()), 4), "p min", float(p.min()))
ent = -(a * np.log2(a + 1e-300)).sum(1)
print("entropia media por fila", round(float((rho * ent).sum()), 3))
for k, e in trees.items():
    m = A.split_mass(a, e)
    s = (rho[:, None] * m).sum(0)
    print(f"{k:14s} suma ponderada de masas {s.sum():.3f}  sin ponderar {m.sum(1).mean():.3f}  top7 aristas {np.sort(s)[-7:].sum()/s.sum():.3f}")
np.save("huffman.npy", trees["huffman"])
print("base", base[:12].tolist())
print("huffman", trees["huffman"][:12].tolist())

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
