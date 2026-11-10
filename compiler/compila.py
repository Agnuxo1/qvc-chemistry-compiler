# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Angle circuits from a finished table, with the full low cache kept inside the 128-qubit cap.

The public compiler falls back to a grouped low cache, which confines features to 8 of the 15
low coordinates. Borrowing each word's top bit (heliosli's idea, in tensorqrom) keeps all 15
cached in 126 qubits. Fan-in with margin 0, groups of six: both measured public by
qwertykeypadapple; this code calls tensorqrom (marculera, Apache-2.0).
Usage: compila.py <table.npz> <outdir> [shots]: writes the submission folder and runs the official verifier.
"""
import json
import os
import sys
import time

import numpy as np

import encode
import rasgos
import rmcode
import tensorqrom as tq
from fourqrom import batch_deltas

BROT, J, LOW = 8, 5, 4
RASGOS = os.environ.get("QVC_RASGOS", "1") == "1"
SEMILLA = int(os.environ.get("QVC_SEMILLA", "0"))   # offset of every search seed, for a second try
SOLO = [int(x) for x in os.environ.get("QVC_SOLO", "").split(",") if x]   # circuits to re-plan; the rest come from QVC_PREVIO
PREVIO = os.environ.get("QVC_PREVIO", "")          # folder with terminos.pkl from an earlier build
EVOL = float(os.environ.get("QVC_EVOL", "0"))       # seconds of evolutionary search per circuit, after the seeds
BAJOS = float(os.environ.get("QVC_BAJOS", "0"))     # seconds per circuit for the low-side search; 0 keeps the output groups
if os.environ.get("QVC_REL", "1") == "1":
    import relaciones
    relaciones.activar()


def plan(words, deg, k, trials=6, margin=0, sizes=None):
    """Products of circuit k, its padded delta and its circuit."""
    A = len(words)
    n_sel = max(1, (A - 1).bit_length())
    d = list(batch_deltas(words, J))[k]
    out = rmcode.output_degrees(deg, k, J, BROT)
    d = rmcode.pad(d, out, BROT)
    perm, groups = rmcode.layout(out, sizes or {0: 6, 1: 5})
    C = tq.anf_tensor(d, BROT, LOW)
    terms = tq.shared(C[:, :, perm], groups, trials=1, seed=k, margin=margin)
    back = dict(enumerate(perm))
    terms = [(a1, b1, a2, b2, sum(1 << back[i] for i in tq._bits(s))) for a1, b1, a2, b2, s in terms]
    if BAJOS > 0:
        import bajos
        low = bajos.plan(C, seed=k, tope=BAJOS)
        if len(low) < len(terms):
            terms = low
    if EVOL > 0:                                       # Darwin cage over the relation sets, seeded by three greedy runs
        import random
        import bajos
        import evolucion
        P = bajos.Problema(C)
        seeds = [bajos.buscar(P, random.Random(100 + s + SEMILLA), 90.0)[1] for s in range(3)]
        _, _, sel = evolucion.evolucionar(P, random.Random(k + SEMILLA), EVOL, seeds, log=None)
        low = bajos.terminos(P, sel)
        if len(low) < len(terms):
            terms = low
    return terms, d, n_sel, groups


def _tarea(a):
    words, deg, k, trials = a
    t0 = time.time()
    terms, _, _, groups = plan(words, deg, k, trials)
    print(f"circuito {k}: {len(terms)} productos, grupos {groups}, {time.time()-t0:.0f} s", flush=True)
    return terms


def familia(words, deg, jobs=4, intentos=1):
    """The fifteen circuits. Each is planned `intentos` times with different seeds, keeping the cheapest."""
    from concurrent.futures import ProcessPoolExecutor
    import pickle
    prev = pickle.load(open(PREVIO + "/terminos.pkl", "rb")) if PREVIO else None
    todo = [k for k in range(15) if not prev or not SOLO or k in SOLO]
    with ProcessPoolExecutor(jobs) as ex:
        got = dict(zip(todo, ex.map(_tarea, [(words, deg, k, 1) for k in todo])))
    terms = []
    for k in range(15):
        t = got.get(k)
        if prev and (t is None or len(prev[k]) <= len(t)):
            t = prev[k]
        terms.append(t)
    print("productos por circuito", [len(t) for t in terms], flush=True)
    familia.terminos = terms
    A = len(words)
    n_sel = max(1, (A - 1).bit_length())
    out = []
    for k, t in enumerate(terms):
        d = rmcode.pad(list(batch_deltas(words, J))[k], rmcode.output_degrees(deg, k, J, BROT), BROT)
        out.append(rasgos.build_circuit(d, t, n_sel, k, A) if RASGOS else tq.build_circuit(d, t, n_sel, BROT, LOW, scratch=True))
    return out


def main():
    import build as bd
    src, dest = sys.argv[1], sys.argv[2]
    shots = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    with np.load(src) as z:
        data = {k: np.array(z[k]) for k in z.files}
    words = data["angle_words"].astype(np.int64)
    deg = data["codes"].astype(np.int64) if "codes" in data else np.zeros((75, BROT), np.int64)
    if RASGOS:
        edges = data["tree_edges"].astype(np.int64)
        new = rasgos.poner(words, edges, rasgos.flags(*words.shape))
        drift = np.abs(np.abs(np.sum(encode.decode(words, edges, BROT) * encode.decode(new, edges, BROT), axis=1)) - 1)
        assert drift.max() < 1e-9 and np.array_equal(words & 1, new & 1), "the gauge changed a vector or a bit 0"
        words = new
    fam = familia(words, deg)
    print("qubits", max(c.num_qubits for c in fam), "Toffolis por pasada", sum(c.operation_statistics().num_toffoli_like for c in fam), flush=True)
    os.makedirs(dest, exist_ok=True)
    np.savez(dest + "/submission.npz", **{k: data[k] for k in bd.KEYS}, tree_edges=data["tree_edges"], angle_words=words)
    bd.write_kmx_family(fam, dest, format="kmb")
    import pickle
    pickle.dump(familia.terminos, open(dest + "/terminos.pkl", "wb"))
    r = bd.verify(dest, shots_per_address=shots)
    res = dict(score=r["score"], mejora=bd.BASELINE_SCORE / r["score"], lambda_eff=r["lambda_eff"], toffolis=r["toffoli_count"],
               qubits=r["num_qubits"], error_1=1e3 * r["metrics"]["error_1"], error_2=1e3 * r["metrics"]["error_2"],
               E_gap=r["metrics"]["E_gap"], angulos=r["resources"]["angles_toffoli"])
    print("RESULTADO", json.dumps(res), flush=True)
    with open(dest + "/resultado.json", "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
