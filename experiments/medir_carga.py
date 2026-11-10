# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""H5: how the loader cost follows the number of rows. Compiles a finished table and copies with fewer rows per group.

Rows come off the end of the table in whole 16-address blocks, so the remaining blocks keep their codewords. The table is not refit:
the Toffoli count is the measure, the error of a truncated table means nothing. Usage: medir_carga.py <refit.npz>
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import json
import sys

import numpy as np

sys.path.insert(0, (_HOME + "/compiler"))
import compila
import rasgos


def medir(words, deg, edges):
    new = rasgos.poner(words, edges, rasgos.flags(*words.shape))
    fam = compila.familia(new, deg)
    return sum(c.operation_statistics().num_toffoli_like for c in fam), max(c.num_qubits for c in fam), [len(t) for t in compila.familia.terminos]


def main():
    with np.load(sys.argv[1]) as z:
        words, deg, edges = z["angle_words"].astype(np.int64), z["codes"].astype(np.int64), z["tree_edges"].astype(np.int64)
    out = []
    for B in (143, 127, 111):
        rows = list(range(76 + 8 * B))    # whole blocks off the end, so every remaining 16-address block keeps its codeword
        t, q, p = medir(words[rows], deg, edges)
        rec = dict(B=B, A=len(rows), toffolis_pasada=t, qubits=q, productos=p)
        out.append(rec)
        print(json.dumps(rec), flush=True)
    a = np.array([r["A"] for r in out], float)
    t = np.array([r["toffolis_pasada"] for r in out], float)
    m, c = np.polyfit(a, t, 1)
    print("ajuste T = m A + c", round(m, 3), round(c, 1), "T(1092)/T(1220)", round(t[1] / t[0], 4), "lineal seria", round(1092 / 1220, 4), flush=True)
    with open("medir_carga2.json", "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    main()

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
