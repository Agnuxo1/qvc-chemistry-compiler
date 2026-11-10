# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Raw rounding noise of a code spec, before any refit: curvature times squared offset to the nearest lattice point.

Two-body rows only, on the continuous table, with the same code choice as the staged rounding. The refit absorbs most of
it (197.6 of 15,734 mHa^2 on the public run), so only differences against the current spec mean anything.
Usage: ruido_codigo.py <spec> [spec ...]
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys

import numpy as np

sys.path.insert(0, (_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/dfthc_refit/experiments"))
import rmcode  # noqa: E402

N, BITS = 76, 8
step = np.pi / 2 ** (BITS - 1)
with np.load("marc_845L.npz") as z:
    t = z["th"] / step
with np.load("sens_845.npz") as z:
    c = z["h"].astype(np.float64) * 1e6
addr = N + np.arange(len(t))
blk, pos = addr // 16, addr % 16


def noise(spec):
    deg = rmcode.parse(spec, N - 1, BITS)
    v = np.round(t)
    cols = np.flatnonzero(deg.any(axis=1))
    if len(cols):
        r, m = rmcode.residues(t[:, cols], c[:, cols], blk, pos, deg[cols])
        v[:, cols] = rmcode.residue_round(t[:, cols], r, m)
    return float((c * (v - t) ** 2).sum())


base = noise("0:1:3-14")
print(f"nada {noise(''):.0f}  referencia 0:1:3-14 {base:.0f} mHa2", flush=True)
for spec in sys.argv[1:]:
    n = noise(spec)
    print(f"{spec}: {n:.0f} mHa2, x{n/base:.3f}, absorbido estimado +{(n-base)*197.6/base:.1f}", flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
