# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Independent virtual-lab transfer test of Fran's scratch-lifetime experiment.

This is a component experiment, not a measured improvement in a QVC submission.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("output",type=Path)
parser.add_argument("--runtime",type=Path,required=True)
ARGS=parser.parse_args()
sys.path.insert(0, str(ARGS.runtime.resolve()))
import kickmix as km


def main():
    source = ROOT / "experiments/ancillas/measure_kickmix.py"
    module_spec = importlib.util.spec_from_file_location("fran_ancilla_experiment", source)
    original = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(original)
    rng = random.Random(20261110)
    report = {"scope": "Synthetic 16-bit accumulator only; local Kickmix simulation, no QVC benchmark score and no physical hardware", "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "author": "Francisco Angulo de Lafuente", "seed": 20261110, "rows": []}
    start = time.perf_counter()
    for k in (2, 4, 8, 16, 32):
        if k <= 4:
            cases = [(a, c, (a * 7919 + c * 104729) & 65535) for a in range(1 << k) for c in range(1 << k)]
            kind = "all a,c basis pairs, one deterministic accumulator per pair"
        else:
            cases = [(rng.getrandbits(k), rng.getrandbits(k), rng.randrange(65536)) for _ in range(1024)]
            cases[:4] = [(0, 0, 0), ((1 << k) - 1, (1 << k) - 1, 65535), (0, (1 << k) - 1, 65535), ((1 << k) - 1, 0, 0)]
            kind = "1024 preregistered-seed cases, including extrema and overflow"
        row = {"k": k, "cases_per_variant": len(cases), "coverage": kind}
        for name, serial in (("parallel", False), ("serial", True)):
            circuit, (acc, aa, cc) = original.construir(k, 16, serial)
            resources = original.medir(circuit)
            checked = 0
            for offset in range(0, len(cases), 256):
                batch = cases[offset:offset + 256]
                sim = km.Simulator(batch_size=len(batch), seed=20261110 + offset)
                for shot, (a, c, initial) in enumerate(batch):
                    for register, value in ((aa, a), (cc, c), (acc, initial)):
                        for bit, q in enumerate(register):
                            sim.write_within_shot(q, shot, bool((value >> bit) & 1))
                sim.do(circuit)
                for shot, (a, c, initial) in enumerate(batch):
                    def read(register):
                        return sum(int(sim.read_within_shot(q, shot)) << bit for bit, q in enumerate(register))
                    assert read(aa) == a and read(cc) == c
                    assert read(acc) == (initial + (a & c).bit_count()) & 65535
                    assert abs((float(sim.read_shot_phase(shot)) + 1) % 2 - 1) < 1e-12
                    for q in range(16 + 2 * k, circuit.num_qubits):
                        assert not sim.read_within_shot(km.q(q), shot)
                    checked += 1
            row[name] = {**resources, "checked": checked, "value_input_scratch_phase": "PASS"}
        assert row["parallel"]["C_toffoli_like"] == row["serial"]["C_toffoli_like"]
        assert row["parallel"]["Q"] > row["serial"]["Q"]
        row["synthetic_QC_improvement"] = row["parallel"]["coste_Q_por_C"] / row["serial"]["coste_Q_por_C"]
        report["rows"].append(row)
    report["seconds"] = time.perf_counter() - start
    report["status"] = "PASS"
    output = ARGS.output
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "PASS", "seconds": report["seconds"], "cases_per_variant": sum(x["cases_per_variant"] for x in report["rows"]), "rows": [{"k": x["k"], "Q_parallel": x["parallel"]["Q"], "Q_serial": x["serial"]["Q"], "Toffoli": x["serial"]["C_toffoli_like"]} for x in report["rows"]]}), flush=True)


if __name__ == "__main__":
    main()
