# Compact inverse-square-root integration

Francisco Angulo de Lafuente · https://orcid.org/0009-0001-1634-7063 · 2026-11-13.
Original integration and text: MIT OR Apache-2.0. Quantum source generator: Syed Asad Ali, Apache-2.0, with all upstream notices retained.

## Measured result

Two fresh Linux source builds reproduce `321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177`. Build A took78s, build B127s with audit enforcement enabled. Both run the upstream exact proof over all3,133,452 legal values and all1,297 HMR variables, preserving the input and clearing scratch. This is a complete46-qubit inverse-square-root circuit, not the earlier standalone coefficient primitive.

The unmodified official verifier passes200,540,928shots for each of two declared salts,401,081,856shots total. Default cost80,162.73214111096, mean1511.5700305625394Toffoli-like gates,1T,33rotations; independent salt `qvc-i01-source46-20261113-independent` cost80,162.69658589501. Both have worst error/tolerance0.973575996935943 atx54566. `native-default.json`, `native-independent.json` and `native-runs.json` retain raw outputs and execution metadata. A mathematical proof is not a replacement for the stock check.

## Source and data availability

The authenticated source archive is the12Nov2026 public release by Syed, downloaded by another local chat and read here without modifying its workspace. Archive SHA256 `7d9801ae20e942dba2211a656bba6014a0a16d57da534c0b60328d1c5d9d8254`;560 internal file hashes pass. This integration does not claim to have invented the46Q architecture.

The source normalizes the22-bit input, creates a12-bit root and10-bit residual with4flags, loads the first coefficient state, computes its seed/product, runs the phase divider, reloads the second coefficient state, and reverses the arithmetic with measurement-debt repayment. The first loader fits20mutable owners plus26outside owners. The second uses19mutable owners plus27outside, consuming four address coordinates and reconstructing them during cleanup. Both enforce46totalqubits.

The early retirement of root bit `a6=v[11]` is central: after its last initial coefficient reader, it is X-measured and freed across coefficient/seed/product work. It is reconstructed from the *current*13-bit derivative D with one CCX using `a6=D10 xor D11 xor D12 xor ((D10 xor a5) and (D11 xor a5))`; the conditional Z on the reconstructed owner repays its recorded sign. This source-level identity is used in the full program and is covered by its exact whole-domain proof. It does not substitute the mutated derivative high bits into our earlier C1-seed decoder, which failed on272,827inputs.

The upstream source explicitly contains small donor component IR plans T1/T2, interpreted by `block_replay.py`, plus mathematical loader certificates. These are readable component source descriptions, not a hidden full-circuit KMB payload; their presence and provenance are disclosed rather than described as newly synthesized by this project. Historical optimized research KMB/KMX fixtures and one executable are also bundled. Runtime tracing found481reads of those files at9source sites, all length/hash checks; `fixture-read-sites.json` identifies each statement. BuildB allows only those inspected sites, rejects compiled circuit loading through `Circuit.from_file` during generation, and reconstructs exactly the same output. This is a bounded runtime audit, not an OS sandbox or a proof about all future modifications to the source.

## Executable integration

`compact_invsqrt.py` authenticates the archive,560sourcefiles, native runtime and verifier; extracts to a fresh work directory; runs the upstream generator, finishing passes and exact proof; requires the output hash; and optionally runs both full official salts. Its default includes official verification. `--build-only` explicitly leaves the result unqualified. It requires Linux x86_64, CPython3.13, NumPy, bash and core utilities. Choose paths without whitespace or `@`; choose fresh output directories. Build timeout900s, each official salt3600s, default2workers. Failure preserves logs and work for diagnosis; choose a new output directory for a retry.

```bash
python compact_invsqrt.py --engine HOST/kickmix --verifiers HOST/verifiers \
  --out /mnt/datos/qvc46-out --work /mnt/datos/qvc46-work
```

`complete_portfolio.py` authenticates a123-file source/recipe/receipt snapshot against the fixed manifest root SHA256 `61bf36bfabc8c3c47840553709f9f8637d583016e97b93eb8f43bafcfbce0249` and constructs the inverse plus the existing SomeJoint/Atakan-derived883Q DQI policy and the project's frozen deep512 chemistry recipe. It requires exactly18outputs with expected hashes. It preserves all third-party notices. The third fresh inverse build and the complete18-output portfolio have finished; see `wrapper-build-report.json`, `dqi-rebuild.json` and `portfolio-build.json`. Goldfish's first round found missing root-manifest and native-receipt hash controls; both were repaired and exercised with positive and tampered-input cases in `guard-validation.json`. The guard changes do not alter quantum emission; they were tested separately after the complete build.

```bash
python complete_portfolio.py --output /mnt/datos/qvc-candidate --work /mnt/datos/qvc-build \
  --data HOST/data --runtime HOST/kickmix
```

GPU status was checked; compatible tasks use the managed server first. This implementation and its full native simulator are CPU work. No GPU job or foreign job was started or stopped.

## Acceptance boundaries

`finalize_candidate.py` binds both complete inverse receipts to the generated circuit, requires full shot counts and width46, checks native-run identities and declared salts, and verifies the unmodified official metric's hash. It packages the18 source-built files using the existing receipt-bound packager. All17 stock circuit readers, numerical NPZ reader, ZIP CRC, extraction and exact input/receipt bindings pass. DQI and chemistry reuse their earlier two full receipts only because all freshly generated files match their authenticated hashes; these tests were not rerun or claimed new. See `package/manifest.json` and `package/readiness.json`.

Goldfish round2 identified two further provenance guards. The wrapper now pins `sitecustomize.py` SHA256 `19d5e8b6f42099797cfd1ae45110fc1ae4f25f53997bfeedb709423ecf6cfc61`, requires a real launch preflight, and checks a unique generator start/end acknowledgement using a per-build nonce. Six activation controls reject missing/corrupt hooks and missing start/close events. The complete wrapper was rerun from fresh source with these controls and both full official salts, finishing in465.671s; its execution report SHA256 is `1408e206c0ddeea0fb1973523ec3efbdff80f19a710cf329883846707bdb2d7f`. It records each receipt SHA256 immediately on completion, before qualification. The finalizer requires this report's observed root hash, exact names/order, actual command salt arguments, pinned verifier/circuit and receipt digests; duplicated/swapped receipts, wrong salts/order and altered report roots are rejected. See `confirmed-v2/integration-report.json`, `confirmed-v2/audit-events.jsonl`, `audit-activation-controls.json` and `binding-controls.json`. The confirmed raw receipts are byte-identical to the initial measurements. Final package-v2 passes the same full receipt/reader/ZIP gates. The audit log itself matches the SHA256 recorded in the execution report; this is an integrity chain, not an external digital signature or OS sandbox.

The complete ZIP has29,996,340bytes and SHA256 `5b5164307220b5b74266e4cbc942eeb4d28c270cc175d11e432710a76d5bb2f5`. Its four combinations of declared inverse salts and archived paired DQI/chemistry salts yield local composite25.900639352901063–25.900643789154685, using the archived reference costs. This is20.4766% above sourcev0.3's21.498484409138246 and exceeds the older approximate25.238 binary portfolio. These are local indices, not leaderboard scores or confidence limits. The complete compact alternative is locally validated; EGM review must converge before release promotion.

Historical exact I01 remains OPEN for `26ebf39d…` invsqrt and `e9f54be3…` DQI. This is a separately identified source candidate; it cannot silently satisfy a different exact-hash acceptance gate. No Kaggle submission, publication, official score, prize eligibility or hardware execution is asserted. JEV consultations04–06 are connected with `provenance=jev`; advice is guidance, not experimental evidence.
