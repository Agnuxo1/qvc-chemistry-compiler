# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente (this port and its modifications)
# SPDX-License-Identifier: Apache-2.0
# Derived-From: public DFTHC refit pipeline by marculera (Apache-2.0); see NOTICE and docs/ATTRIBUTION.md
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (Apache-2.0): keep this notice, the NOTICE file and the credit to both authors in any copy.
"""The Givens decoder that onebody_quant and rmcode import from quantize.py.

Same functions as the public quantize.py (marculera, Apache-2.0), without that file's import of
the starter kit, which the one-body step does not need.
"""
from __future__ import annotations

import jax.numpy as jnp
import numpy as np


def levels(edges: np.ndarray) -> list[np.ndarray]:
    """Split the ordered edges into runs that touch disjoint orbitals."""
    runs, current, used = [], [], set()
    for t, (p, q) in enumerate(edges):
        if p in used or q in used:
            runs.append(np.array(current))
            current, used = [], set()
        current.append(t)
        used.update((int(p), int(q)))
    return runs + [np.array(current)]


def decode(theta, edges: np.ndarray, n: int):
    """Rows of theta/pi to vectors; edges within a level act on disjoint orbitals."""
    c, s = jnp.cos(jnp.pi * theta), jnp.sin(jnp.pi * theta)
    u = jnp.zeros((theta.shape[0], n), theta.dtype).at[:, 0].set(1.0)
    for ts in levels(edges):
        p, q = edges[ts, 0], edges[ts, 1]
        up, uq = u[:, p], u[:, q]
        u = u.at[:, p].set(c[:, ts] * up - s[:, ts] * uq).at[:, q].set(s[:, ts] * up + c[:, ts] * uq)
    return u

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: Apache-2.0 :: cite the author when reusing
