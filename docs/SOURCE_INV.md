# Source-built inverse-square-root construction

The recovered sixteen-module source slice builds the published c3f3ac25 ancestor directly from numeric polynomial coefficients and phase angles. No compiled circuit input or encoded circuit payload is included in this slice.

The source build installs the published Davio lookup specialization, reconstructs the arithmetic, performs the domain/HMR compiler passes and matches SHA256 `c3f3ac2575906e83de1ebfa91580ca4ad52655ac4ab34bcbde56c23b37d0d6de`. The executed audit forbids external KMB/KMX inputs and records opened sources and imported-module hashes.

| Full stock result | Value |
|---|---:|
| Status | PASS |
| Verified shots | 200,540,928 = 3,133,452 inputs × 64 |
| Qubits | 87 |
| Cost | 140,178.1847720425 |
| Reference/cost | 14.8152455897x |
| Mean Toffoli-like count | 1,291.999829122163 |
| Rotations | 44 |
| Worst error/tolerance | 0.9999341616745385 |

This is a source-complete alternative. The original selected 26ebf39d public circuit has 62 qubits and higher measured performance; this reconstruction does not produce that file. The default three-task source-backed portfolio combines this ancestor, source-built DQI888 and frozen chemistry s37. Its local composite indices are 21.4126669035 and 21.4454017007, compared with 2.239566 for the organizer-reference control. These are local indices using archived baselines, not leaderboard scores or confidence limits.

## Reproduce

Use the Linux Python 3.13 environment and official native runtime described in REPRODUCIBILITY.md. The source coefficients and angles are frozen numeric inputs, and the credited calibration code is retained.

```bash
python tools/build_inv_source.py build/invsqrt-source --data /path/to/official/data --runtime /path/to/native/runtime
python tools/verify_local.py invsqrt build/invsqrt-source/invsqrt.kmb build/invsqrt-source-check.json --data /path/to/official/data --runtime /path/to/native/runtime --salt source-inv-independent-20261110
python tools/build_source_portfolio.py build/source-portfolio --data /path/to/official/data --runtime /path/to/native/runtime
```

The final command builds all 18 circuit/data outputs; it keeps build reports and intermediate circuits outside the submission directory. A full source build is not itself a verifier PASS: bind generated hashes to the retained full native receipts and run the official input readers before packaging. Architecture parameters exposed by build_inv_source.py require an explicit --experimental flag and new native verification; they do not inherit the ancestor's PASS.

## Recovered-coefficient study

The later [reconstruction study](../studies/recovered_invsqrt/README.md) recovers all 256 numerical coefficient triplets and the original 62Q phase function. It includes an exact all-input native phase comparison and a separately constructed 88Q circuit with a full 200,540,928-shot PASS. That circuit is retained as research; the c3 construction above remains the selected, cheaper source alternative. Exact reconstruction of the original 62Q circuit bytes remains open.

## Attribution and observations

Dmitrii Gluzdov published the source integration and numeric recipe, which credit Marsyas arithmetic, Phuc Thai's normalization idea and the public QROM/measurement lineage. All source headers, Apache-2.0 scope and attribution are preserved in vendor/invsqrt_source. Francisco Angulo de Lafuente's project recovered, rebuilt, independently verified and integrated the construction.

The first recovery attempt omitted the Davio specialization and produced a different unverified hash. That attempt was preserved and not promoted. Installing the source-declared specialization produced the exact published ancestor, which then received its own full native check. No ancestor's result is transferred to another file.

Research author: Francisco Angulo de Lafuente · ORCID https://orcid.org/0009-0001-1634-7063. Own wrapper/document: MIT OR Apache-2.0; preserved upstream sources: Apache-2.0.
