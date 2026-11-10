"""Freeze and rebuild chemistry from numeric tables and a declarative GF(2) plan.

No randomized or wall-clock-dependent search is performed during reconstruction.
The frozen plan is an optimization result, not a compiled circuit.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import shutil
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DEFAULT = ROOT.parent / "concursos-24h/sprints/20261029-google-quantum-ai-verifiable-quantum-cir/datos"
KEYS = ("U", "W", "H2_I", "H1_I", "Hsym_lower")


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class DataOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError("The local optimization plan must contain only integers, tuples and lists")


def write_portable_npz(path, arrays):
    """NumPy's numeric payload with explicit ZIP host metadata.

    np.savez otherwise records Windows as create_system=0 and Linux as 3.
    Keeping that field explicit makes the same numeric archive byte-identical.
    """
    import numpy as np
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name, array in arrays.items():
            info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            with archive.open(info, "w", force_zip64=True) as member:
                np.lib.format.write_array(member, np.asanyarray(array), allow_pickle=False)


def freeze(source, table, target):
    if target.exists():
        raise FileExistsError(target)
    terms = DataOnlyUnpickler(io.BytesIO((source / "terminos.pkl").read_bytes())).load()
    if not isinstance(terms, list) or len(terms) != 15:
        raise ValueError("Expected 15 declarative plans")
    for family in terms:
        for term in family:
            if len(term) != 5 or not all(type(x) is int and x >= 0 for x in term):
                raise ValueError("Expected five nonnegative integer masks per product")
    target.mkdir(parents=True)
    (target / "src").mkdir()
    public = ROOT / "pipeline_publico/paquete/dfthc_refit"
    sources = [ROOT / "generador/rasgos.py", public / "tensorqrom.py", public / "fourqrom.py", public / "encode.py", public / "paths.py", public / "experiments/rmcode.py"]
    for path in sources:
        shutil.copy2(path, target / "src" / path.name)
    shutil.copy2(table, target / "table.npz")
    (target / "plan.json").write_text(json.dumps(terms, separators=(",", ":")), encoding="utf-8")
    for name in ("LICENSE", "NOTICE"):
        original = ROOT / "pipeline_publico/paquete" / name
        if original.exists():
            shutil.copy2(original, target / ("UPSTREAM_" + name))
    expected = {p.name: digest(p) for p in source.glob("angle_k_*.kmb")}
    expected["submission.npz"] = digest(source / "submission.npz")
    manifest = {"format": 1, "author": "Francisco Angulo de Lafuente", "orcid": "https://orcid.org/0009-0001-1634-7063", "provenance": {str(p): digest(p) for p in sources}, "table_sha256": digest(target / "table.npz"), "plan_sha256": digest(target / "plan.json"), "source_sha256": {p.name: digest(p) for p in (target / "src").glob("*.py")}, "expected_files": expected, "products_per_circuit": [len(x) for x in terms], "scope": "Exact reconstruction from a saved trained table and optimized algebraic plan. It does not claim deterministic training from Hamiltonian."}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"frozen": str(target), "products": manifest["products_per_circuit"]}), flush=True)


def rebuild(recipe, output, data, runtime, plan_override=None):
    if output.exists():
        raise FileExistsError(output)
    start = time.perf_counter()
    manifest = json.loads((recipe / "manifest.json").read_text(encoding="utf-8"))
    assert digest(recipe / "table.npz") == manifest["table_sha256"]
    assert digest(recipe / "plan.json") == manifest["plan_sha256"]
    for name, sha in manifest["source_sha256"].items():
        assert digest(recipe / "src" / name) == sha, name
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ["DFTHC_DATA"] = str(data)
    sys.path[:0] = [str(runtime), str(recipe / "src"), str(data / "verifiers")]
    import numpy as np
    import encode
    import rasgos
    import rmcode
    from fourqrom import batch_deltas
    import tensorqrom as tq
    with np.load(recipe / "table.npz", allow_pickle=False) as f:
        arrays = {k: np.array(f[k]) for k in f.files}
    words = arrays["angle_words"].astype(np.int64)
    edges = arrays["tree_edges"].astype(np.int64)
    codes = arrays["codes"].astype(np.int64)
    gauged = rasgos.poner(words, edges, rasgos.flags(*words.shape))
    drift = np.abs(np.abs(np.sum(encode.decode(words, edges, 8) * encode.decode(gauged, edges, 8), axis=1)) - 1)
    assert drift.max() < 1e-9 and np.array_equal(words & 1, gauged & 1)
    terms = json.loads((plan_override or recipe / "plan.json").read_text(encoding="utf-8"))
    selection_bits = max(1, (len(gauged) - 1).bit_length())
    deltas = list(batch_deltas(gauged, 5))
    output.mkdir(parents=True)
    stats = []
    for k, plan in enumerate(terms):
        delta = rmcode.pad(deltas[k], rmcode.output_degrees(codes, k, 5, 8), 8)
        circuit = rasgos.build_circuit(delta, plan, selection_bits, k, len(gauged))
        assert circuit.num_qubits <= 128
        name = f"angle_k_{k}.kmb"
        circuit.to_file(str(output / name), format="kmb")
        if plan_override is None:
            assert digest(output / name) == manifest["expected_files"][name], f"Circuit bytes differ: {name}"
        stats.append({"k": k, "qubits": circuit.num_qubits, "toffoli": circuit.operation_statistics().num_toffoli_like, "sha256": digest(output / name)})
    write_portable_npz(output / "submission.npz", {**{k: arrays[k] for k in KEYS}, "tree_edges": edges, "angle_words": gauged})
    assert digest(output / "submission.npz") == manifest["expected_files"]["submission.npz"], "Numerical archive bytes differ"
    identical = sum(digest(output / name) == sha for name, sha in manifest["expected_files"].items())
    report = {"status": "PASS", "scope": "Algebraic tensor decomposition asserted; gauge and 128-qubit bounds asserted; numerical archive byte-identical", "byte_identical_files": identical, "plan_override": str(plan_override) if plan_override else None, "plan_used_sha256": digest(plan_override or recipe / "plan.json"), "max_gauge_vector_drift": float(drift.max()), "seconds": time.perf_counter() - start, "files": stats, "submission_npz_sha256": digest(output / "submission.npz")}
    (output.parent / (output.name + "-reconstruction.json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "files"}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("source", type=Path)
    f.add_argument("table", type=Path)
    f.add_argument("recipe", type=Path)
    r = sub.add_parser("build")
    r.add_argument("recipe", type=Path)
    r.add_argument("output", type=Path)
    r.add_argument("--data", type=Path, default=DATA_DEFAULT)
    r.add_argument("--runtime", type=Path, default=ROOT / "generador/entorno")
    r.add_argument("--plan", type=Path, help="Experimental algebraic plan; bypasses byte-equality only for circuit files, not tensor checks")
    a = p.parse_args()
    if a.operation == "freeze":
        freeze(a.source, a.table, a.recipe)
    else:
        rebuild(a.recipe, a.output, a.data, a.runtime, a.plan)


if __name__ == "__main__":
    main()
