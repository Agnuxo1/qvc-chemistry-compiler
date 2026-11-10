# Measured results

All results below are local runs of the unmodified official verifiers. They are not Kaggle submissions or quantum hardware measurements.

| Chemistry circuit | Reference/cost | Total Toffolis | Total qubits | Evidence |
|---|---:|---:|---:|---|
| Public 24.94 base, heliosli | 11.1976100951 | 14,966 | 427 | quimica-base2494-64-a.json |
| Public gengsr portfolio | 11.2040924214 | 14,958 | 427 | quimica-gengsr-64-a.json |
| Project s2 | 11.2298650271 | 14,852 | 427 | quimica-s2-64-a.json |
| **Project s37** | **11.2328903140** | **14,848** | **427** | quimica-s37-64-a.json and -b.json |
| Project H14 GPU | 11.2343975372 | 14,848 | 427 | chemistry-h14-main-a.json and -b.json |
| **Project deep GPU** | **11.2346608655** | **14,848** | **427** | chemistry-h14-deep512-a.json and -b.json |

s37 improves the measured chemistry ratio by **0.2570301%** over the tested gengsr chemistry. This compares these pinned artifacts, not every current leaderboard solution. lambda_eff = 47.1175587131; error_1 = 11.197358 mHa; error_2 = 19.9784971080 mHa, against a 20 mHa ceiling. Margin = 0.0215028920 mHa. Each chemistry salt uses 64 shots per lookup address, 78,080 shots in total.

H14 lowers actual cost a further **0.0134161%** against s37, to **298,689,767.493265**, with lambda_eff **47.111237352442**. Its physical error and resource counts remain equal within floating-point precision. Two independent salts pass, all fifteen angle circuits are unchanged and all sixteen source-rebuilt files match exactly. The retained GPU trace contains 58,962 optimization steps. [Experiment and reproduction](GPU_EXPERIMENT.md).

The deep GPU continuation lowers chemistry cost to **298,682,766.527190**, a further **0.0023439%** reduction, with lambda_eff **47.110133115838**. Both full salts pass; all sixteen outputs reconstruct identically on Windows and Linux. The selected source portfolio uses DQI883 with **59.6973029x / 59.6973071x** and local composites **21.4984844 / 21.4984849**. The earlier rows and receipts remain historical controls.

| Reused public performance task | Measured ratio | Coverage |
|---|---:|---|
| invsqrt | 21.9677093447 | 3,133,452 legal inputs × 64 shots = 200,540,928; PASS |
| DQI, salt a | 64.9282009429 | 102,400 shots; 0 value errors, 1 phase error; PASS |
| DQI, salt b | 65.2263866415 | 102,400 shots; 0 value errors, 0 phase errors; PASS |

The corresponding local composite indices are **25.2098282614** and **25.2483617580** using the archived baselines. They reflect those two salts; they are not confidence limits, a future score prediction or an official score. Both salts are retained. The organizers use private sampling and may use salt-specific baselines.

## Observations

The exact optimized invsqrt/DQI generators remain a separate acceptance gate. The performance ZIP has passed circuit checks, while the complete-source reference control uses different and more expensive circuits. Chemistry is exactly reproducible from the saved table; deterministic retraining from the Hamiltonian is not established. The small error margin is material when experimenting with new tables or runtimes: rerun the full stock check for a changed artifact.

---
Research author: **Francisco Angulo de Lafuente** · [ORCID](https://orcid.org/0009-0001-1634-7063) · 2026-11-10.
Own text: MIT OR Apache-2.0; third-party materials retain their notices.
