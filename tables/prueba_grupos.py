# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Products of one circuit for several group layouts: which order and sizes reuse earlier products best."""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import sys
import time

import numpy as np

sys.path.insert(0, (_HOME + "/compiler"))
import compila  # noqa: E402
import rmcode  # noqa: E402
import tensorqrom as tq  # noqa: E402
from fourqrom import batch_deltas  # noqa: E402

src, k = sys.argv[1], int(sys.argv[2])
with np.load(src) as z:
    words = z["angle_words"].astype(np.int64)
    deg = z["codes"].astype(np.int64)
d = list(batch_deltas(words, 5))[k]
out = rmcode.output_degrees(deg, k, 5, 8)
d = rmcode.pad(d, out, 8)
C = tq.anf_tensor(d, 8, 4)
dense = [int(i) for i in np.flatnonzero(out == 0)]
coded = [int(i) for i in np.flatnonzero(out == 1)]
print("densas", len(dense), "codificadas", len(coded), flush=True)
for margin in (0,):
    t0 = time.time()
    msgs = []
    terms = tq.shared(C[:, :, dense + coded], [6, 6, 6, 6, 6, 5], trials=1, seed=k, margin=margin, log=msgs.append)
    print(f"margen {margin}: {len(terms)} productos, {time.time()-t0:.0f} s; " + " | ".join(m.split(': ')[1].replace('features ', 'f').replace('products ', 'p').replace('shared ', '') for m in msgs), flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
