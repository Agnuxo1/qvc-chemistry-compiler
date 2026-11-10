# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: Apache-2.0
"""Generate all three QVC tasks from source and a frozen numeric chemistry recipe.

Inverse square root and DQI use the organizers' attributed reference generators.
Chemistry uses the pinned trained table and the team's declarative GF(2) plan.
This generates the source-complete control, not the optimized public portfolio.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("--data", type=Path, required=True, help="Organizer data directory, containing verifiers/")
    p.add_argument("--runtime", type=Path, required=True, help="Directory containing a Python-3.13-compatible native Kickmix build")
    p.add_argument("--recipe", type=Path, default=HERE / "receta-s37")
    p.add_argument("--verify", action="store_true", help="Run unmodified official full checks on all three generated tasks")
    p.add_argument("--workers", type=int, default=3)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(name, "1")
    sys.path[:0] = [str(a.runtime.resolve()), str((a.data / "verifiers").resolve())]
    from invsqrt import nr_reference_circuit as invgen
    from dqi import dqi_reference_circuit as dqigen
    pins = json.loads((HERE / "reference-pins.json").read_text(encoding="utf-8")) if (HERE / "reference-pins.json").exists() else json.loads((HERE / "servidor-src/reference-pins.json").read_text(encoding="utf-8"))
    a.output.mkdir(parents=True)
    result = {"scope": "Source-complete control: organizer reference invsqrt/DQI plus the team's optimized chemistry", "author": "Francisco Angulo de Lafuente", "orcid": "https://orcid.org/0009-0001-1634-7063", "reference_attribution": "Competition organizers, Apache-2.0", "builds": {}}
    for task, module in (("invsqrt", invgen), ("dqi", dqigen)):
        start = time.perf_counter()
        c = module.build_nr_circuit(10) if task == "invsqrt" else module.build_reference_circuit(4095, 70, 12)
        target = a.output / (task + ".kmb")
        c.to_file(str(target), format="kmb")
        assert sha(target) == pins[task], f"Source/runtime changed the reference circuit: {task}"
        result["builds"][task] = {"sha256": sha(target), "qubits": c.num_qubits, "static_toffoli": c.operation_statistics().num_toffoli_like, "source_sha256": sha(Path(module.__file__)), "seconds": time.perf_counter() - start}
        del c
    subprocess.run([sys.executable, str(HERE / "reconstruir_quimica.py"), "build", str(a.recipe.resolve()), str((a.output / "dfthcsos").resolve()), "--data", str(a.data.resolve()), "--runtime", str(a.runtime.resolve())], check=True)
    if a.verify:
        import kickmix as km
        from invsqrt import verify_submission_invsqrt as invverify
        from dqi import verify_submission_dqi as dqiverify
        from dfthcsos import verify as chemverify
        result["verifications"] = {}
        for task, verifier in (("invsqrt", invverify), ("dqi", dqiverify)):
            circuit = km.Circuit.from_file(str(a.output / (task + ".kmb")), format="kmb")
            spec = verifier.ProblemSpecInvSqrt.for_n_p(10) if task == "invsqrt" else verifier.ProblemSpecDQI.benchmark_instance()
            receipt = verifier.verify(circuit, spec, salt="codex-source-control-20261110", max_workers=a.workers)
            receipt.pop("shot_operation_counts", None)
            assert receipt["status"] == "PASS"
            result["verifications"][task] = receipt
            del circuit
        result["verifications"]["dfthcsos"] = chemverify.verify(a.output / "dfthcsos", shots_per_address=64, salt="codex-source-control-20261110")
        assert result["verifications"]["dfthcsos"]["status"] == "PASS"
    report = a.output.parent / (a.output.name + "-generator-report.json")
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "GENERATED_AND_VERIFIED" if a.verify else "GENERATED_HASH_MATCH", "report": str(report), "output": str(a.output)}), flush=True)


if __name__ == "__main__":
    main()
