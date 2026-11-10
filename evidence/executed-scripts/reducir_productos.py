"""Deterministic exact common-control GF(2) rank reductions; no verifier tuning."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import time


def bits(value):
    while value:
        bit = value & -value
        yield bit.bit_length() - 1
        value ^= bit


def plane(c, d):
    return tuple(sorted((c, d, c ^ d))) if c and d and c != d else None


def canon(items):
    out = defaultdict(int)
    for c, d, s in items:
        key = plane(c, d)
        if key is not None:
            out[key] ^= s
    return [(p[0], p[1], s) for p, s in sorted(out.items()) if s]


def factor(common, group):
    """Represent sum d*s by a basis of its output columns, modulo common."""
    pivot = 1 << (common.bit_length() - 1)
    columns = defaultdict(int)
    for c, d, s in group:
        other = d if c == common else c if d == common else c
        # For the third point c+d, either original point spans the plane.
        if other & pivot:
            other ^= common
        for output in bits(s):
            columns[output] ^= other
    basis = {}
    vectors = []
    coefficients = []
    for output, vector in sorted(columns.items()):
        selected = 0
        while vector:
            top = vector.bit_length() - 1
            if top in basis:
                v, index = basis[top]
                vector ^= v
                selected ^= 1 << index
            else:
                index = len(vectors)
                basis[top] = (vector, index)
                vectors.append(vector)
                coefficients.append(0)
                selected ^= 1 << index
                break
        for index in bits(selected):
            coefficients[index] ^= 1 << output
    return [(common, v, s) for v, s in zip(vectors, coefficients) if s]


def reduce_terms(terms, width):
    mask = (1 << width) - 1
    items = canon([(a1 | (b2 << width), a2 | (b1 << width), s) for a1, b1, a2, b2, s in terms])
    changes = []
    while True:
        by_control = defaultdict(list)
        for index, (c, d, s) in enumerate(items):
            for common in (c, d, c ^ d):
                by_control[common].append(index)
        best = None
        for common, indices in sorted(by_control.items()):
            if len(indices) < 2:
                continue
            result = factor(common, [items[i] for i in indices])
            saving = len(indices) - len(result)
            if saving > 0 and (best is None or saving > best[0]):
                best = saving, common, indices, result
        if best is None:
            break
        saving, common, indices, result = best
        chosen = set(indices)
        items = canon([item for i, item in enumerate(items) if i not in chosen] + result)
        changes.append({"saving": saving, "common_control": str(common), "terms_after": len(items)})
    # Preserve the five-mask convention expected by tensorqrom/rasgos.
    return [(c & mask, d >> width, d & mask, c >> width, s) for c, d, s in items], changes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("recipe", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parent.parent / "generador/entorno")
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    sys.path[:0] = [str(a.runtime), str(a.recipe / "src")]
    import numpy as np
    import tensorqrom as tq
    started = time.perf_counter()
    plans = json.loads((a.recipe / "plan.json").read_text(encoding="utf-8"))
    with np.load(a.recipe / "table.npz", allow_pickle=False) as f:
        rows = len(f["angle_words"])
    low, high, outputs = 15, (rows + 15) // 16 - 1, 35
    report = []
    new_plans = []
    for k, terms in enumerate(plans):
        new, changes = reduce_terms(terms, low)
        assert np.array_equal(tq.mixed_of(terms, low, high, outputs), tq.mixed_of(new, low, high, outputs)), f"Mixed tensor changed: {k}"
        assert len(new) <= len(terms)
        new_plans.append(new)
        report.append({"k": k, "before": len(terms), "after": len(new), "tensor_equal": True, "changes": changes})
    a.out.mkdir(parents=True)
    (a.out / "plan.json").write_text(json.dumps(new_plans, separators=(",", ":")), encoding="utf-8")
    result = {"status": "PASS", "seconds": time.perf_counter() - started, "products_before": sum(len(x) for x in plans), "products_after": sum(len(x) for x in new_plans), "circuits": report, "scope": "Exact algebraic comparison only; no claim of a new verified circuit"}
    (a.out / "resultado.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "circuits"}), flush=True)


if __name__ == "__main__":
    main()
