# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""A Givens tree other than the public log-depth one, for the whole tail of the chain.

The public modules call encode.log_depth_tree() wherever they need the tree, so setting QVC_TREE (an .npy of edges) replaces it there.
The verifier takes any tree rooted at 0 with parents before children, and reads it from submission.npz.
"""
import os

import numpy as np

import encode

if os.environ.get("QVC_TREE"):
    _edges = np.load(os.environ["QVC_TREE"]).astype(np.int64)
    encode.log_depth_tree = lambda n=76: _edges.copy()

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
