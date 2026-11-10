# Independent publication review

Date: 2026-11-10. Method: one fresh-context Goldfish-style reviewer, critical and drift lenses, with focused correction checks. This is a bounded adaptation of Google's Elephant–Goldfish Model, not a full multi-stage convergence certificate.

The reviewer executed the repository integrity checker, recalculated the reported ratios, error margin, shot coverage and composite indices, checked all six GIFs and their data hashes, and checked the frozen source and output bindings. The contact sheet was visually inspected.

Findings and corrections:

| Finding | Correction | Evidence |
|---|---|---|
| MIT scope incorrectly offered for an Apache-derived feature compiler | Apache-2.0 header and footer; upstream attribution retained; frozen recipe source given a sidecar without changing its bytes | Reviewer executed header/footer searches and source comparisons |
| s2 ratio transcribed incorrectly in README | 11.2298650x, recalculated from original baseline/cost | Reviewer independently repeated the division |
| Source-control output counter included a reconstruction report | Move report outside the submission directory before binding the 18 circuit/data hashes | New Linux execution, current constructor SHA256 and all 18 output hashes independently matched |

Final focused reviewer result: no remaining findings in the assigned checks; repository checker PASS, 151 Python sources and 22 local links at that point. Later additions to documentation, release metadata and the publication manifest are checked by the publication integrity gate.

Review limits: the reviewer did not rerun native circuit simulations, reconstruct circuits, use GPU or network access, or verify current external competition eligibility. Native checks and source reconstruction were executed separately and retained under replication and official. Not every historical research script was inspected line by line. I01 remains open for the optimized invsqrt/DQI sources.

Research author: Francisco Angulo de Lafuente · ORCID https://orcid.org/0009-0001-1634-7063. Own report: MIT OR Apache-2.0.
