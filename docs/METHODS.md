# Methods

## Task and cost

This repository compiles the angle lookups in a double-factorized tensor-hypercontraction representation of the FeMoCo Hamiltonian. The official local chemistry cost is

\[
C_{chem}=\lambda_{eff}\,T_{total}\,Q_{total},\qquad
\lambda_{eff}=\sqrt{E_{gap}(2\Lambda-E_{gap})}.
\]

The improvement ratio uses the archived reference cost 3,355,599,588.3155365. The organizers' metric and thresholds are never modified. A local composite uses the geometric mean of the three task ratios; it is not a submitted leaderboard score.

## Source and frozen inputs

The selected recipe has eight groups, 143 vectors per group, rank 44 and 8-bit angle words. A saved fitted table is a numeric input. A saved plan is a list of integer masks describing GF(2) products, not encoded circuit instructions. Each loader is rebuilt by the credited source compiler. manifest.json pins all six source modules, the table, plan and 16 expected outputs.

The trained factorization is not guaranteed to recur bit for bit when fitting is rerun. Exact reconstruction begins at the frozen numeric table and algebraic plan. Training and exploratory sources are supplied separately for method study, with their historical entry points and external inputs. Frozen reconstruction is the acceptance test for the released chemistry.

## Free features and loader compilation

The compiler applies vector-sign-preserving pi gauges, computes Boolean address features, factors the output maps into shared GF(2) products, and emits each lookup within the 128-qubit per-loader limit. The signed vectors are checked by their inner products; the tensor represented by each loader must equal its declared truth table. Saved masks are checked during emission rather than trusted merely because they came from a prior search.

```mermaid
flowchart LR
  A[Official Hamiltonian] --> B[Credited initialization and fitting]
  B --> C[Saved numeric table]
  C --> D[Tree and 8-bit words]
  D --> E[GF2 feature and product plan]
  E --> F[15 source-built angle circuits]
  C --> G[Portable NPZ]
  F --> H[Unmodified official verifier]
  G --> H
  H --> I[Hashes, resources and error receipts]
```

## Experimental discipline

Keep the control, inputs, seeds, verifier version and acceptance rule fixed before comparing variants. Preserve failed or neutral trials. The rank-C1 experiment did not reduce the selected product count. The ancilla experiment exhaustively checks the stated small domains and samples larger words; it is a synthetic primitive result, not a measured full-QVC improvement.

## Orthogonal channel-gauge experiment

For each fitted group, stack the weights and identity channel as `A = [W; H2_I]`. An orthogonal channel rotation gives `A_new = A @ Q`, so `A_new @ A_new.T = A @ A.T` in exact arithmetic. This preserves the two-body tensor and offset contractions while leaving the fitted angle data unchanged. The official normalization being optimized is `lambda_h2 = (1/4) * sum_c ||A_new[:, c]||_1**2`.

The batched float64 GPU experiment in `experiments/gauge/gauge_search_v2.py` uses smoothed Riemannian descent, near and global starts, annealed smoothing and independent final SVD projection. It scales an existing public refinement idea. It does not invent this gauge transformation. CPU checks compare the official formula and directional derivatives and bound the augmented-Gram drift. `tools/apply_channel_gauge.py` preserves the validated base's encoded angle words and all fifteen compiled circuits; these words differ from the pre-encoding words stored in the fitted table.

The orthogonal invariant is a model-level check. Promotion also requires two full unmodified native checks, a lower actual official cost, exact reconstruction from the retained table/rotation and unchanged circuit hashes. The GPU search is an optimization experiment, not a claim that repeated training is bitwise deterministic.

## Observations

Verification is classical simulation of reversible/phase circuits, not quantum hardware or a measured physical speedup. Error margin, stochastic sampling, source completeness and competition eligibility are separate questions. The evidence table and source-recovery record state each scope explicitly.

---
Research author: **Francisco Angulo de Lafuente** · [ORCID](https://orcid.org/0009-0001-1634-7063) · 2026-11-10.
Own text: MIT OR Apache-2.0; third-party materials retain their notices.
