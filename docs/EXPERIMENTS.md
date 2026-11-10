# Experiments and observations

## Synthetic ancilla scheduling

The project checks a measurement-based carry schedule with a 16-bit accumulator. It exhausts the operand pairs for k = 2 and 4 with one deterministic accumulator value per pair, and checks 1,024 seeded cases per larger operand width (k = 8, 16, 32), including overflow and boundary cases. There are 3,344 checked cases per variant. At k = 32 the example resource count changes from 128 to 97 qubits while retaining 896 Toffolis. The input/output, phase and scratch conditions in the saved experiment were checked. This is a primitive experiment; no full QVC improvement is inferred.

## Rank-C1 algebraic reduction

The tested product-elimination candidate did not improve the selected 2,961-product s2 plan. All 15 tensors remained equal. The negative result is retained to prevent repeating that trial as if unexplored. It does not prove that every low-rank search is exhausted.

## Reproducibility correction

The first Linux NPZ reconstruction had identical array payloads but a different archive hash. Diagnosis isolated the ZIP creator-system metadata. The portable writer fixes that field explicitly, after which all 18 control outputs matched across environments. Both the diagnostic and the passing proof are retained.

## Further scientific questions

Normalization improvements must include both the signed-weight term and the cross term; a conditional cost calculation is not a feasible fitted table. Decoder sampling variation must be reported with the salt and shot count, without selecting only the best salt. Any new source-based invsqrt/DQI result must first pass the exact-source and full native checks.

---
Research author: **Francisco Angulo de Lafuente** · [ORCID](https://orcid.org/0009-0001-1634-7063) · 2026-11-10.
Own text: MIT OR Apache-2.0; third-party materials retain their notices.
