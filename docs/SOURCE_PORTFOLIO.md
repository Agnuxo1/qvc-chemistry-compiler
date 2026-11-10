# Three-task source-generated candidate

The public entry point builds inverse square root, DQI and chemistry from credited algorithm sources and frozen numeric recipes. It emits eighteen circuit/data files, keeping intermediates and reports outside the submission directory. The complete source-to-artifact chain is independently inspectable; compiled public performance inputs are not used by this constructor.

```bash
python tools/build_source_portfolio.py build/source-candidate --recipe recipes/h14-deep512 --dqi-variant 883 --data /path/to/official/data --runtime /path/to/native/runtime
```

The command above selects deep GPU chemistry and the checked883Q policy. Use `--dqi-variant 883` as two separate arguments. Omitting `--recipe` retains historical s37; omitting `--dqi-variant` retains historical DQI888. Use a fresh output name: existing builds are preserved. See [environment and runtime requirements](REPRODUCIBILITY.md), [invsqrt sources](SOURCE_INV.md) and [DQI sources](SOURCE_DQI.md).

## Selected v0.3 construction and package

All eighteen outputs were rebuilt from the current public source entry point and numeric recipes on Linux. The unchanged invsqrt file remains c3f3ac25; DQI is the new883Q policy and chemistry is the deep512 continuation. Exact hashes bind all five complete native receipts to the package. The package passes CRC/extraction, all seventeen stock KMB readers and the stock NPZ reader.

Selected ZIP: **29,978,848 bytes**, SHA256 `d4367b0962dc686f9dbb3588130ecc975faf092f80848134ab590c948e806b06`. The local composite indices are **21.4984844091 /21.4984849129**. [v0.3.0 scientific release](https://github.com/Agnuxo1/qvc-chemistry-compiler/releases/tag/v0.3.0). Source and package evidence: `source-portfolio-deep883-linux.json` and `source-deep883.json` in the corresponding evidence directories. The binary performance portfolio's missing original generators remain a separate I01 gate.

## Earlier v0.2 integration and package

The selected H14 integration was subsequently executed from the current public entry points on Linux. All eighteen outputs match the already native-verified artifacts, including the numerical archive rebuilt on Windows. `evidence/replication/source-portfolio-h14-linux.json` records the exact hashes. The final package in `evidence/packages/source-h14.json` passes the same full receipt bindings, CRC/extraction, seventeen stock KMB readers and stock NPZ reader.

Selected archive: **28,251,303 bytes**, SHA256 `8a59a667018c7b29581a05bb4bde8362285e982d9fb976f7247561afcbf62cb5`. Its local composite indices are **21.4136245740 / 21.4463608353**. Download it from the [v0.2.0 scientific release](https://github.com/Agnuxo1/qvc-chemistry-compiler/releases/tag/v0.2.0). The following s37 record is retained as the earlier integration control.

The Linux integration receipt in `evidence/replication/source-portfolio-build-linux.json` records all eighteen output hashes. The inverse-square-root runtime-precedence fix was separately reexecuted and produced the same exact circuit; `invsqrt-runtime-bound-build.json` binds that current wrapper and native module. Full native receipts cover 200,540,928 invsqrt shots, two 102,400-shot DQI salts and two 78,080-shot chemistry salts. Exact unchanged file hashes bind those receipts to the package.

The first integrated package is recorded in `evidence/packages/source-v1.json`: 18 files, 28,251,463 ZIP bytes, SHA256 `47c913ffc544ce715f85a6d54b0afa50b263f935142406108b76ad996f166983`. CRC and extracted hashes pass, as do the seventeen unmodified official KMB input readers and the official NPZ reader. This is a locally validated artifact; no Kaggle submission or acceptance is asserted.

| Versioned portfolio | Local composite, salt a | Local composite, salt b |
|---|---:|---:|
| **Source-generated deep GPU / DQI883, selected** | **21.4984844091** | **21.4984849129** |
| Source-generated H14 / DQI888, prior |21.4136245740 |21.4463608353 |
| Source-generated s37, prior control | 21.4126669035 | 21.4454017007 |
| Public binary performance portfolio with s37 | 25.2098282614 | 25.2483617580 |
| Organizer-reference source control | approximately 2.239566 | approximately 2.239566 |

Indices use archived baselines and are not leaderboard scores or confidence intervals. The alternative's complete source chain and the performance portfolio's higher measured index are separate properties. Original performance I01 remains open; changing the candidate label does not recover its missing generators.

## Packaging a newly verified build

Run all full checks for changed artifacts. `tools/package_portfolio.py` requires the exact candidate and five PASS receipts: invsqrt, two DQI salts and two chemistry salts. It checks full shot counts, distinct salts, every input hash, ZIP CRC and stock input-reader limits before recording a package. Supply the unmodified official metric source via `--metric`; it is obtained with the competition materials and is not redistributed here. Consult `python tools/package_portfolio.py --help` for its explicit paths.

Generation is not a verifier PASS. A previous circuit's receipt cannot be applied to a changed file. The chemistry rotation experiments are promoted only after separate complete checks and exact reconstruction.

## Authorship and observations

Francisco Angulo de Lafuente recovered, integrated, audited and tested this portfolio and developed the project chemistry compiler. The inverse-square-root and DQI algorithms are credited to their upstream researchers; their source files, manifests and Apache-2.0 notices are retained. [Attribution](ATTRIBUTION.md).

Research author: Francisco Angulo de Lafuente · ORCID https://orcid.org/0009-0001-1634-7063 · 2026-11-10. Own wrapper and text: MIT OR Apache-2.0; upstream sources retain their original licenses.
