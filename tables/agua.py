# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Reverse water-filling on the measured word sensitivities: bits a table needs at a given raw noise."""
import numpy as np

with np.load("sens_845.npz") as d:
    h, s = d["h"], d["s"]
R, B = 8, 143
S0 = h.sum() / 12
print("ruido crudo uniforme", S0 * 1e6, "mHa2; absorbido real ~", 19.95 ** 2 - 14.155 ** 2, "=> razon", (19.95 ** 2 - 14.155 ** 2) / (S0 * 1e6))
# step 2^k on word i: raw noise h 4^k / 12. Level L: largest k with h 4^k / 12 <= L.
for ratio in (1.02, 1.05, 1.1, 1.25, 1.5, 2, 3, 4, 6):
    lo, hi = 1e-12, 1e3
    for _ in range(80):
        L = (lo * hi) ** .5
        k = np.clip(np.floor(0.5 * np.log2(np.maximum(12 * L / h, 1e-300))), 0, 7).astype(int)
        tot = (h * 4.0 ** k).sum() / 12
        if tot > ratio * S0:
            hi = L
        else:
            lo = L
    kept = 7 - k
    print(f"ruido crudo x{ratio}: bits medios {kept.mean():.2f} de 7; sin bits {np.mean(k >= 7):.3f}; "
          f"histograma {[round(float(np.mean(kept == b)), 3) for b in range(8)]}")
# care per 16-row block, per edge, at x2: how much of the block matters
ratio = 2
lo, hi = 1e-12, 1e3
for _ in range(80):
    L = (lo * hi) ** .5
    k = np.clip(np.floor(0.5 * np.log2(np.maximum(12 * L / h, 1e-300))), 0, 7).astype(int)
    if (h * 4.0 ** k).sum() / 12 > ratio * S0:
        hi = L
    else:
        lo = L
kept = 7 - k
order = np.argsort(-h.sum(0))
print("bits medios por arista (de mas a menos sensible):", np.round(kept.mean(0)[order][:20], 1), "...", np.round(kept.mean(0)[order][-8:], 1))
rs = h.sum(1)
print("bits medios por fila, cuartiles de fuerza:", [round(float(kept[(rs >= a) & (rs <= b)].mean()), 2) for a, b in zip(np.quantile(rs, [0, .25, .5, .75]), np.quantile(rs, [.25, .5, .75, 1]))])
print("reparto de sensibilidad por fila: 10 % de filas tienen", float(np.sort(rs)[::-1][:len(rs) // 10].sum() / rs.sum()))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
