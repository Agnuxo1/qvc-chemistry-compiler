"""Independent check of the sign-mixture identity on the saved chemistry weights.

The hypothetical normalization estimate holds the verifier's gap fixed. It is
not a feasible factorization, a new circuit, or a prediction of a future score.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def check(table, verifier):
    with np.load(table, allow_pickle=False) as z:
        w = z["W"]
        h = np.abs(z["H2_I"])
    p = np.maximum(w, 0).sum(axis=1)
    n = np.maximum(-w, 0).sum(axis=1)
    l1, signed = np.abs(w).sum(axis=1), w.sum(axis=1)
    lhs = 0.25 * np.sum(l1 ** 2 - signed ** 2)
    pn = np.sum(p * n)
    assert math.isclose(float(lhs), float(pn), rel_tol=1e-12, abs_tol=1e-11)
    direct = 0.25 * np.sum((h + l1) ** 2 - (h + np.abs(signed)) ** 2)
    cross = np.sum(h * np.minimum(p, n))
    assert math.isclose(float(direct), float(pn + cross), rel_tol=1e-12, abs_tol=1e-11)
    result = {"table": str(table), "W_shape": list(w.shape), "D": float(2 * pn), "D_over_2": float(pn), "cross_H_minPN": float(cross), "hypothetical_raw_Lambda_reduction": float(direct), "identity_residual": float(direct - pn - cross), "scope": "Algebraic identity on current weights. The hypothetical values do not demonstrate feasible preservation of energies, error_1/error_2 or E_gap."}
    if verifier:
        r = json.loads(verifier.read_text(encoding="utf-8"))["official_result"]
        gap, raw = r["metrics"]["E_gap"], r["metrics"]["Lambda"]
        conditional = math.sqrt(gap * (2 * (raw - direct) - gap))
        result["conditional_fixed_gap"] = {"actual_Lambda": raw, "actual_lambda_eff": r["lambda_eff"], "hypothetical_lambda_eff": conditional, "hypothetical_improvement": 3355599588.3155365 / (conditional * r["toffoli_count"] * r["num_qubits"]), "not_a_prediction": True}
    return result


if __name__ == "__main__":
    output = HERE / "resultados/h13-identidad.json"
    if output.exists():
        raise FileExistsError(output)
    rows = [check(ROOT / "generador/corrida_m844Uc/refit.npz", None), check(HERE / "receta-s37/table.npz", HERE / "resultados/quimica-s37-64-a.json")]
    output.write_text(json.dumps({"status": "PASS", "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "rows": rows}), flush=True)
