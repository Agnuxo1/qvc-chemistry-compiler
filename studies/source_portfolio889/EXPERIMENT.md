# Complete-source DQI889 laboratory

Francisco Angulo de Lafuente, https://orcid.org/0009-0001-1634-7063, 2026-11-13. Original integration and report: MIT OR Apache-2.0. Quantum generator: Syed Asad Ali, Apache-2.0; its notices and acknowledgements remain intact.

## Current state

The newly public DQI archive has SHA256 `49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763`,8,486,126 bytes and430 authenticated files. It contains source, mathematical certificates and reports; no KMB/KMX or compiled executable is included. The archive search found no historical `e9f54be3` target hash or Atakan/SomeJoint marker. This is a distinct source family, not recovered authorship or an exact reconstruction of that older circuit.

Both source constructions completed with output `7cbe8ecf6f6e9743529b574f019504bb1712ce06fbb570c719ce9d9e2c914cd9`,455,590,024 bytes, matching the public source's declared output. Its own build asserts889qubits and384,003static Toffoli-like gates. Their memory guards recorded successful163.351s and163.989s child executions, about1.04GB peak RSS. Both actual generator processes have matching nonce/PID activation/closure records. All four full native checks now pass,409,600shots total; this is sampled stock verification, not a universal decoder proof.

## Source and execution controls

`fetch.py` downloads the public archive and requires its known public-manifest digest. `run_lab.py` checks that archive and all430internal pins, safely extracts paths/symlinks, and authenticates the Linux native runtime and unmodified stock DQI verifier. Host SHA256 values are `c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e` and `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`.

The source is built twice in fresh work/output directories, with CPython3.13, NumPy, one BLAS/OMP thread, a900s bound and the upstream4GB reserve/soft memory guard. The inspected guard only terminates the process group it creates for its own child. A shared lock serializes other builds using that guard. `KEEP_WORK=1` preserves the source tree and logs; no foreign job is stopped.

The pinned audit shim `e93b17929601d081608901e04d1d7e68ea21d604d151520535c30b9189da4abb` requires a real launch preflight. It rejects `Circuit.from_file` throughout source construction and any Python-level compiled-file read except a generated output under the work tree's out directory. Its nonce/PID start and close acknowledgements identify the actual `build_v7.py` process by `argv[0]`. This bounded audit is not an OS sandbox or an independent proof about arbitrary future source changes.

The initial parent validator mistakenly counted the guard's child-command argument as a second generator. The quantum build itself succeeded. The initial runner and failure receipt are preserved; JEV recommended correcting the process selector and revalidating that successful build. The resumed workflow records buildA as reused validation, checks its original guard/build records and output hash, and launches buildB fresh. It does not represent buildA as rerun or omit the parent validation failure.

## Preregistered full checks

After both source builds match, the runner executes the unmodified stock verifier on102,400shots for each predeclared salt: default empty salt, `qvc-syed889-20261113-a`, `qvc-syed889-20261113-b`, `qvc-syed889-20261113-c`. It uses one worker because of the verifier's memory footprint. It retains every result, including value/phase errors, full costs and repetition penalties. A stock PASS is not a zero-error claim or proof over every decoder input.

Every run records the actual command, salt/name, circuit/verifier identities, process exit code and raw-receipt hash immediately at completion. The workflow only qualifies if all four receipts are PASS and bound to the expected circuit,889qubits and102,400shots. Source output equality alone is insufficient. Benchmark salts are separate observations, not confidence intervals; no best-salt selection is permitted. All runs are CPU work on servidor-ia; no GPU job was launched.

| Salt name | Native cost | Mean Toffoli-like count | Value errors | Phase errors |
|---|---:|---:|---:|---:|
| default |360733280431.94055|383156.2908886719|0|0|
| a |362390008931.8864|383156.30064453126|1|0|
| b |360733130907.9235|383156.1320703125|0|0|
| c |360733156109.01373|383156.1588378906|0|0|

All four cost values include the stock repetition/error penalty. The one value error in saltA is retained and is not presented as a zero-error experiment. The source model's uniform-mask expectations are not substituted for these measured benchmark values. `lab-report.json` SHA256 is `5a132e425c9b3a823edcaaa12b66815bc4d61f0c387449cadc9053d08ec66a4c`; it binds source builds, actual commands and receipt hashes.

## Complete source portfolio

`construct_complete.py` constructs the inverse from the previously published source bundle SHA256 `0ddbc852ddf36233248da558d1a99b308f1b630ddce5fe210926cde405b2e852`, constructs this DQI from its source archive, and reconstructs the frozen deep512 chemistry. It verifies the two source archives,123-input legacy snapshot root,430DQI source pins, native host identities and audit preflight/start/closure. All18newly emitted hashes match their declared outputs. The constructor SHA256 is `dd6dbe2fc80690a0607732f2902ca31b7feed91936988efda4f1a804cc8674e2`.

`qualify_complete.py` requires the observed DQI and inverse execution-report root hashes, checks both source-built DQI outputs and audit logs, exact native command/salt/name/order/receipt links and full shot counts, and requires a full18-output constructor report. It then checks every member against the receipts and executes the stock17circuit readers, numerical NPZ reader, ZIP CRC, extraction and hash checks. Receipt wrappers store actual command salt strings; run labels are separate. The initial private package-label draft was corrected and packaging repeated; no quantum compiler or native simulation was rerun for that metadata repair.

All package checks pass. The archive has49,338,223bytes and SHA256 `0059f20ad2b9822318c208d28093714ca0e9440271262387c5b1df0109d3b30e`. The local composite range26.975162261465695–27.016402925509315 covers all16combinations of the two confirmed inverse salts, four new DQI salts and two archived chemistry salts. These are combinations of measured component costs with archived baselines2076774.233715282,24439463583672.93,3355599588.3155365, not16independent end-to-end metric trials, confidence bounds or official scores. The chemistry receipts and inverse receipts are reused only because their newly emitted files match exactly; no extra simulations are implied. Relative to sourcev0.3's21.498484409138246, the gain is25.4747160–25.6665466%. Package manifest/readiness and all16values are retained in `package/`.

## Delivery boundaries

The currently published46Q/883Q/deep512 portfolio remains unchanged at local25.90064. The separately identified46Q/889Q/deep512 candidate is now locally validated, with publication still gated on EGM convergence. The pending user choice concerned promoting the already published46Q/883Q/deep512 portfolio versus retaining the exact historical I01 requirement; no selected release or historical acceptance criterion has been changed. Historical `26ebf39d`/`e9f54be3` source recovery remains OPEN. No Kaggle submission, prize eligibility, official score or hardware result is claimed.
