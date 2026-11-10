"""Build a deterministic, receipt-bound three-task ZIP and run official input readers."""
from __future__ import annotations
import argparse
import gc
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import stat
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / "generador/entorno"), str(ROOT.parent / "concursos-24h/sprints/20261029-google-quantum-ai-verifiable-quantum-cir/datos/verifiers")]


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def input_hashes(receipt):
    if "inputs" in receipt:
        return {Path(p).name: d["sha256"] for p, d in receipt["inputs"].items()}
    return {"dqi.kmb": receipt["input_sha256"]}


def deterministic_zip(paths, target):
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, path in sorted(paths.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            with path.open("rb") as src, z.open(info, "w", force_zip64=True) as dst:
                shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("chemistry", type=Path)
    p.add_argument("public_portfolio", type=Path)
    p.add_argument("invsqrt_receipt", type=Path)
    p.add_argument("dqi_a", type=Path)
    p.add_argument("dqi_b", type=Path)
    p.add_argument("chem_a", type=Path)
    p.add_argument("chem_b", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--reference-control", action="store_true", help="A separately labelled organizer-reference control with one full DQI salt")
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    records = {name: load(path) for name, path in {"invsqrt": a.invsqrt_receipt, "dqi_a": a.dqi_a, "dqi_b": a.dqi_b, "chem_a": a.chem_a, "chem_b": a.chem_b}.items()}
    for name, record in records.items():
        assert record["official_result"]["status"] == "PASS", name
    assert records["invsqrt"]["shots_argument"] == 64
    for name in ("chem_a", "chem_b"):
        assert records[name]["shots_argument"] == 64
    for name in ("dqi_a", "dqi_b"):
        assert records[name]["official_result"]["verified_shots"] == 102400
    if not a.reference_control:
        assert records["dqi_a"]["salt"] != records["dqi_b"]["salt"]
    else:
        pins = load(HERE / "servidor-src/reference-pins.json")
        assert input_hashes(records["invsqrt"])["invsqrt.kmb"] == pins["invsqrt"]
        assert input_hashes(records["dqi_a"])["dqi.kmb"] == pins["dqi"]
    assert records["chem_a"]["salt"] != records["chem_b"]["salt"]
    paths = {name: a.public_portfolio / name for name in ("invsqrt.kmb", "dqi.kmb")}
    paths.update({"dfthcsos/" + path.name: path for path in a.chemistry.glob("angle_k_*.kmb")})
    paths["dfthcsos/submission.npz"] = a.chemistry / "submission.npz"
    assert len(paths) == 18
    for task, record_names in {"invsqrt": ["invsqrt"], "dqi": ["dqi_a", "dqi_b"], "chem": ["chem_a", "chem_b"]}.items():
        for record_name in record_names:
            pins = input_hashes(records[record_name])
            for name, path in paths.items():
                relevant = name.startswith("dfthcsos/") if task == "chem" else name == task + ".kmb"
                if relevant:
                    assert sha(path) == pins[path.name], (record_name, name)
    a.out.mkdir(parents=True)
    target = a.out / "submission.zip"
    deterministic_zip(paths, target)
    unpacked = a.out / "unpacked"
    unpacked.mkdir()
    members = {}
    with zipfile.ZipFile(target) as z:
        assert z.namelist() == sorted(paths)
        assert z.testzip() is None
        for info in z.infolist():
            assert (unpacked / info.filename).resolve().is_relative_to(unpacked.resolve())
            z.extract(info, unpacked)
            got = sha(unpacked / info.filename)
            assert got == sha(paths[info.filename]), info.filename
            members[info.filename] = {"sha256": got, "bytes": info.file_size}
    module_path = HERE / "fuentes/official-metric/metric-source.py"
    spec = importlib.util.spec_from_file_location("official_qvc_metric", module_path)
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    readers = []
    for name in sorted(paths):
        if not name.endswith(".kmb"):
            continue
        maximum = 1 if name == "invsqrt.kmb" else 4165 if name == "dqi.kmb" else 128
        circuit = metric.read_circuit(unpacked / name, maximum)
        readers.append({"file": name, "qubits": circuit.num_qubits, "bits": circuit.num_bits, "registers": circuit.num_registers, "official_reader": "PASS"})
        del circuit
        gc.collect()
    n = 76
    arrays = metric.read_npz(unpacked / "dfthcsos/submission.npz", {"U": ("f", ("R", "B", n)), "W": ("f", ("R", "B", "C")), "H2_I": ("f", ("R", "C")), "H1_I": ("f", ()), "Hsym_lower": ("f", (n * (n + 1) // 2,)), "tree_edges": ("iu", (n - 1, 2))})
    import pandas as pd
    reference = {"invsqrt": records["invsqrt"]["baseline"], "dqi": records["dqi_a"]["baseline"], "dfthcsos": records["chem_a"]["baseline"]}
    scores = {}
    for suffix in ("a", "b"):
        costs = {"invsqrt": records["invsqrt"]["official_result"]["score"], "dqi": records["dqi_" + suffix]["official_result"]["score"], "dfthcsos": records["chem_" + suffix]["official_result"]["score"]}
        solution = pd.DataFrame([{"row_id": k, "benchmark": k, "baseline_cost": reference[k]} for k in costs])
        submission = pd.DataFrame([{"row_id": k, "cost": costs[k], "seconds": 0.0} for k in costs])
        value, details = metric.score(solution, submission, "row_id")
        assert math.isclose(value, math.prod(reference[k] / costs[k] for k in costs) ** (1 / 3), rel_tol=1e-14)
        scores[suffix] = {"local_index": value, "details": details}
    report = {"status": "PASS", "reference_control": a.reference_control, "independent_DQI_salts": 1 if a.reference_control else 2, "scope": "Prepared local artifact; all 18 files bound to full official-verifier receipts, extracted and accepted by official metric input readers. Not submitted to Kaggle; this does not certify prize eligibility.", "author": "Francisco Angulo de Lafuente", "orcid": "https://orcid.org/0009-0001-1634-7063", "zip_sha256": sha(target), "zip_bytes": target.stat().st_size, "official_metric_sha256": sha(module_path), "members": members, "input_readers": readers, "npz_shapes": {k: list(v.shape) for k, v in arrays.items()}, "local_composite_indices": scores, "composite_caveat": "Uses archived local reference costs. Kaggle uses private salts and salt-specific reference costs; these are neither official scores nor a confidence interval.", "receipts": {str(path.resolve()): sha(path) for path in (a.invsqrt_receipt, a.dqi_a, a.dqi_b, a.chem_a, a.chem_b)}}
    (a.out / "MANIFIESTO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "zip_sha256", "zip_bytes", "local_composite_indices")}), flush=True)


if __name__ == "__main__":
    main()
