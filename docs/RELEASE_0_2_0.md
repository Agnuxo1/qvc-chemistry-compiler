# v0.2.0 — source-generated portfolio and H14 chemistry

This release contains an executed three-task source construction, a validated eighteen-file candidate archive and the H14 GPU chemistry experiment. Chemistry reaches **11.2343975372x** in the unchanged full local verifier, with **14,848 Toffolis and 427 qubits**. Two chemistry salts pass. A 45-minute, 2,048-state GPU search reduced actual chemistry cost by **0.0134161%** against s37.

The credited source-generated inverse-square-root circuit passes **200,540,928 shots** at **14.8152455897x**. Source-generated DQI888 passes two **102,400-shot** salts at **58.9945523685x / 59.2655314845x**. All eighteen final artifacts were built from the current public entry points on Linux; chemistry also matches the Windows reconstruction byte for byte. The package passed exact receipt bindings, CRC/extraction, all seventeen stock KMB readers and the stock NPZ reader.

The source-generated portfolio's local composite indices are **21.4136245740 / 21.4463608353** using archived baselines. These are not leaderboard scores or confidence intervals.

| Asset | Identity |
|---|---|
| qvc-source-h14-submission.zip | 28,251,303 bytes; eighteen files |
| Archive SHA256 | 8a59a667018c7b29581a05bb4bde8362285e982d9fb976f7247561afcbf62cb5 |
| Invsqrt SHA256 | c3f3ac2575906e83de1ebfa91580ca4ad52655ac4ab34bcbde56c23b37d0d6de |
| DQI SHA256 | 736f3055850794c6beaedf8de5f7dafa1c270e2b57edd403ffa96abf6d207741 |
| Chemistry NPZ SHA256 | cfc6a3084b3c65bc3b74f57efda8da07776fa9ea5a1a4a8bc1b594f302233bc9 |

Use `SELECTED_CANDIDATE.json` and [source portfolio instructions](SOURCE_PORTFOLIO.md). The recommended build includes `--recipe recipes/h14-main`; omitting that flag retains the historical s37 default. Official data and the platform-specific native runtime are obtained separately. The DQI circuit is approximately 547 MB uncompressed.

The repository includes eight scientific GIFs, versioned numerical evidence, negative arithmetic variants, the preregistered GPU protocol, portable constructors and source-integrity checks. Francisco Angulo de Lafuente is the research author, ORCID https://orcid.org/0009-0001-1634-7063. Original separable work is MIT OR Apache-2.0. The credited upstream algorithms and sources retain Apache-2.0 and their original notices.

## Observations

The original higher-index public binary performance portfolio remains a distinct artifact: its exact invsqrt/DQI generators are still missing, so **original I01 remains OPEN**. This alternative's complete source chain does not close that original gate. No final Kaggle submission, host acceptance or prize eligibility is asserted. GPU retraining is not claimed to be bitwise deterministic; the released frozen recipes and output hashes define exact reproducibility.
