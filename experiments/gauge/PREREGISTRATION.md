# H14 — scale the orthogonal channel-gauge search

Author: Francisco Angulo de Lafuente, https://orcid.org/0009-0001-1634-7063. Date: 2026-11-10. Own code/document: MIT OR Apache-2.0. The fitted starting table descends from the credited marculera pipeline and the project's frozen s37 recipe.

User authorization: one of the three GPUs while free, for deeper and larger experiments. Server GPU1 was observed idle; use the managed queue, declared timeout and an isolated source folder. No other job is stopped. H13 sign-constrained training and its working files remain Claude-owned.

## Model and hypothesis

For each group r, form A_r = [W_r; H2_I_r], with B+1 rows and C columns. For an orthogonal Q_r, use A'_r = A_r Q_r. This preserves A_r A_r^T. Therefore the two-body tensor and offset/weight contractions are invariant, as are the reconstructed one-body operator and gap in exact arithmetic. The angle table and its 15 compiled circuits do not change.

The official two-body normalization is F = (1/4) sum_(r,c) ||A'_r[:,c]||_1^2. This is the objective to minimize. Native total resource counts and final cost will be recomputed rather than inferred from the angle circuits alone.

The existing CPU study used Jacobi polishing and a small number of global random starts on an earlier table, with negative results. The public refine code already includes smoothed Riemannian descent. H14 is a scale experiment on the selected s37 table, not a claim to invent orthogonal gauge optimization: batch many near and global starts on GPU, anneal smoothing, retain independent group minima and periodically perturb around the best states.

## Protocol fixed before execution

- Control: unchanged saved s37 table; retain identity start and its exact normalization.
- CPU gate: objective matches the official formula; check an independent directional derivative; a random orthogonal transform preserves the augmented Gram and offset contractions to 1e-10; polar retraction reaches the declared orthogonality tolerance; a small descent smoke test improves its smoothed objective.
- GPU pilot: 60 seconds, 32 starts per group, no publication of improvement until invariants are checked.
- Main scale: up to 256 starts per each of eight groups, at most 45 minutes inside a declared 50-minute job; adjust only batch size downward if measured resource requirements demand it. Fixed seed 20261110. Save best states and progress every 30 seconds; float64 computations.
- Smooth objective uses sqrt(y^2 + delta^2), with annealed delta. Updates use the tangent gradient and Newton–Schulz polar retraction; any saved result receives an independent SVD polar projection in float64 before acceptance.
- Acceptance: projected augmented-Gram drift <= 1e-10 and normalization lower than control. Then regenerate the numerical submission, preserve the exact 15 circuit hashes, and run the full unchanged official chemistry verifier on at least two salts. Promote only if its actual official cost is lower and all error/gap limits pass. Report the measured size of any gain; no minimum gain is invented.
- Retain negative results, attempted starts, runtime, resources, source hashes and seeds. Native validation and publication follow the experiment; no Kaggle submission is authorized.

## Pilot outcome and main-run continuation, fixed before the main run

The first 60-second pilot saved lambda_h2 = 272.4098586314409 from 272.44041078498174. One full official check passed at cost 298713748.6192173, 14,848 Toffolis, 427 qubits, ratio 11.23349562524843; a second salt is being checked. The v2 pilot, after the independent review fixes below, completed with a final saved lambda_h2 = 272.4068476928064 and augmented-Gram drift 1.421e-14.

The main run uses that better v2 pilot table as a frozen continuation seed. Its SHA256 is recorded in MAIN_SEED.json; the original s37 remains the overall comparison control. Report gains against both the continuation seed and original s37. The code is unchanged from reviewed v2. There are 256 starts per group, including an explicit Gaussian/SVD global cohort, 45 minutes maximum and fixed seed 20261110. The data-dependent choice of continuation seed is an optimization choice, not held-out verifier performance selection.

Independent review found and checked two corrections before the main run: add genuine global starts, and force final best-state projection/guarded saving. The v1 pilot is retained as executed; v2 is a separate immutable source file. Server queue reserved its physically idle GPU for a priority campaign. Under Fran's current explicit authorization to use one of all three available GPUs, the local free card is used through gpuq FIFO. The duplicate server pilot was confirmed cancelled before local execution; no other work was stopped.

The continuation seed exposed finite-difference truncation at the original h=1e-6 test step. Before training, a fixed central-difference grid was evaluated without relaxing the 1e-7 relative tolerance: h=3e-8 and 1e-8 gave errors 1.90e-8 and 1.03e-9. The converged check, objective and invariants pass in main-continuation-gate.json. The search implementation remains the reviewed v2 SHA a8cd23c65bb4af6a02554903cab71d1dbc30246b20d7dc02d5cd17cfb97c2105.
