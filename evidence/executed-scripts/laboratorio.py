"""Run the unmodified official QVC verifiers and retain input/code fingerprints.

This wrapper does not alter circuits, metrics, acceptance thresholds, or seeds.
All results are local virtual-laboratory results, not Kaggle submissions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT.parent / "concursos-24h/sprints/20261029-google-quantum-ai-verifiable-quantum-cir/datos"
VERIFIERS = DATA / "verifiers"
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("JAX_PLATFORMS", "cpu")
sys.path[:0] = [str(ROOT / "generador/entorno"), str(VERIFIERS)]
BASELINES = {"chem": 3355599588.3155365, "invsqrt": 2076774.233715282, "dqi": 24439463583672.93}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("task", choices=BASELINES)
    p.add_argument("source", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--shots", type=int, help="chem shots/address, invsqrt shots/x, DQI total shots")
    p.add_argument("--salt", default="codex-independent-20261110-a")
    p.add_argument("--workers", type=int, default=1)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(f"Preserve existing evidence: {a.out}")
    if a.shots is not None and a.shots < 1:
        p.error("shots must be positive")
    paths = ([a.source / "submission.npz"] + sorted(a.source.glob("angle_k_*.kmb"))) if a.task == "chem" else [a.source]
    inputs = {str(x.resolve()): {"sha256": sha256(x), "bytes": x.stat().st_size} for x in paths}
    start = time.perf_counter()
    if a.task == "chem":
        from dfthcsos import verify as official
        result = official.verify(a.source, shots_per_address=a.shots or 64, salt=a.salt)
        m, r = result["metrics"], result["resources"]
        recomputed = math.sqrt(m["E_gap"] * (2 * m["Lambda"] - m["E_gap"]))
        assert math.isclose(recomputed, result["lambda_eff"], rel_tol=1e-12)
        assert math.isclose(result["score"], recomputed * result["toffoli_count"] * result["num_qubits"], rel_tol=1e-12)
        assert m["error_1"] <= 0.020 and m["error_2"] <= 0.020
        assert m["Lambda"] > 49 and m["E_gap"] > 3.914898
        assert result["num_circuits"] == len(paths) - 1
    else:
        import kickmix as km
        circuit = km.Circuit.from_file(str(a.source), format="kmb")
        if a.task == "invsqrt":
            from invsqrt import verify_submission_invsqrt as official
            spec = official.ProblemSpecInvSqrt.for_n_p(10, shots_per_x=a.shots or 64)
            result = official.verify(circuit, spec, salt=a.salt)
        else:
            from dqi import verify_submission_dqi as official
            spec = official.ProblemSpecDQI.benchmark_instance(num_shots=a.shots or 102400)
            result = official.verify(circuit, spec, salt=a.salt, max_workers=a.workers)
        result.pop("shot_operation_counts", None)
    assert result["status"] == "PASS", result
    code_paths = sorted(VERIFIERS.rglob("*.py"))
    versions = {}
    for name in ("numpy", "scipy", "jax", "kaggle", "kickmix"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unpackaged or unavailable"
    record = {
        "task": a.task, "scope": "local official verifier; no external submission",
        "command": sys.argv, "salt": a.salt, "shots_argument": a.shots,
        "seconds": time.perf_counter() - start, "python": platform.python_version(),
        "platform": platform.platform(), "versions": versions, "inputs": inputs,
        "official_source_sha256": {str(x.relative_to(VERIFIERS)): sha256(x) for x in code_paths},
        "wrapper_sha256": sha256(Path(__file__)), "official_result": result,
        "baseline": BASELINES[a.task], "improvement": BASELINES[a.task] / result["score"],
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(a.out), "status": result["status"], "seconds": record["seconds"], "improvement": record["improvement"], "score": result["score"]}), flush=True)


if __name__ == "__main__":
    main()
