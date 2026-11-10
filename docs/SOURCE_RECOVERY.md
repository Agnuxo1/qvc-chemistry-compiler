# Exact-source recovery: I01

Acceptance: a real source algorithm must generate the selected optimized invsqrt and DQI outputs, with exact SHA256 matches, followed by full native verification. A downloader, circuit copier or encoded KMB replay does not meet this project's source gate. The gate remains open until demonstrated.

| Target | Required SHA256 | Current evidence |
|---|---|---|
| invsqrt | 26ebf39df3b13e5fd2d923d1b9988043b107b64f6e21efc5cc9bc76f5d56adec | Public gengsr file; 46-CSWAP shifter on maoxin123's 62-qubit circuit; full native PASS |
| DQI | e9f54be304cbdcda7306729c335b1a2314a45d0ca818e05cf60e45ddee969bc4 | Public Atakan terminal-readout circuit selected by gengsr; two full native checks |

The fetched gengsr and Syed notebooks copy compiled files with hash checks. Atakan's selected-performance notebook authenticates a compiled validation payload; it does not include that decoder's generator. The current maoxin notebook, `maoxin123/lb-25-227-combined-invsqrt-refit-chem`, was subsequently recovered: its inverse-square-root payload is an encoded compiled KMB, rather than a source algorithm. This corrects the earlier unsuccessful lookup of an older notebook slug.

The complete public mrmeows dataset was inventoried (2,704 files). Its inverse-square-root pipeline reported at 20.0565x starts from a frozen logical L6 circuit; the recovered L6 constructor in turn starts from frozen L5. A complete algorithmic origin for that chain was not established. Dmitrii Gluzdov's public factorization dataset was inventoried (833 files, including 117 Python modules). A dependency-closed sixteen-module inverse-square-root construction from that dataset has now been rebuilt and fully verified. A separate Atakan source bank provides the complete DQI888 construction, also rebuilt and fully verified. These are distinct source-generated artifacts, rather than reconstructions of the two target hashes above.

## Original invsqrt numerical function recovered

All 256 numeric coefficient triplets and the special low-L and high-H phase-readout rules have now been recovered. An independent mathematical implementation matches the original circuit's phase exactly on **all 3,133,452 legal inputs**, with one stochastic native measurement branch per input. Input restoration and clean scratch pass for every compared input. Its worst error/tolerance is 0.9993237694056958 at x=161, matching the archived official result.

This is a full-input semantic comparison, not an exact 62-qubit circuit generator or a proof for every measurement branch. A separate 88Q circuit built from the recovered coefficients and newly fitted global phase weights passes all 200,540,928 official shots. It costs 141,336.53747428907 and remains a research study because the selected c3 source circuit is cheaper. Its portable source wrapper exactly reproduces its own 29480dd3 output. [Mathematical model, construction and evidence](../studies/recovered_invsqrt/README.md).

## A verified source-generated alternative

| Task | Exact generated SHA256 | Full native evidence |
|---|---|---|
| Inverse square root | c3f3ac2575906e83de1ebfa91580ca4ad52655ac4ab34bcbde56c23b37d0d6de | 200,540,928 shots; PASS; 14.8152455897x |
| DQI883, selected |0b634cca809c90493b67ac8104c9a307c99556d9edae74e26b460f4283aececd | Two 102,400-shot salts; PASS; 59.6973029414x /59.6973071382x |
| DQI888 | 736f3055850794c6beaedf8de5f7dafa1c270e2b57edd403ffa96abf6d207741 | Two 102,400-shot salts; PASS; 58.9945523685x / 59.2655314845x |

The new [source portfolio](SOURCE_PORTFOLIO.md) builds both algorithms and the project's chemistry into eighteen outputs. The invsqrt audit rejects external KMB/KMX inputs; its numeric recipe, sixteen imported source modules and explicitly selected native runtime are fingerprinted. DQI preserves its ninety-two-source authenticated manifest and upstream notices. The integrated package passed CRC/extraction and all seventeen stock KMB input readers. [Invsqrt construction](SOURCE_INV.md) · [DQI construction](SOURCE_DQI.md).

This closes the algorithm-to-output chain for the alternative candidate. **It does not close original performance I01**: the alternative has a lower measured local composite than the binary portfolio. Both identities and results remain separately versioned.

The PC's QVC project and repository source scan is saved with its scope. A separate server inventory covered 179 QVC-related locations, including identified job workspaces: 122 source files were inspected for target-family markers. Its three matches were organizer-reference generators. The local QVC scan had nine source matches, including reference generators and audit/fetch tools. Neither scan established an exact optimized generator. A broader D-drive content scan exceeded its 120-second bound; it is not represented as exhaustive. See [recovery evidence](../evidence/source-recovery.json).

## Remaining acceptance experiment

Recover or develop the algorithms that generate the two original target hashes, or improve the distinct source-generated candidate while measuring its own performance. Ten exploratory arithmetic variants around the recovered invsqrt recipe were source-built; two nominated variants passed full native checks but both cost more than the pinned ancestor, so neither was promoted. The source-complete organizer-reference portfolio remains a useful independent control.

---
Research author: **Francisco Angulo de Lafuente** · [ORCID](https://orcid.org/0009-0001-1634-7063) · 2026-11-10.
Own text: MIT OR Apache-2.0; third-party materials retain their notices.
