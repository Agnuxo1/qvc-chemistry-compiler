# v0.4.0 — complete compact source portfolio selected

On **2026-11-14**, Francisco Angulo de Lafuente authorized promoting the superior complete source candidate and retaining the earlier byte-exact reconstruction as a separate historical research item. This release selects the already reconstructed and locally qualified **46Q inverse / 889Q DQI / deep512 chemistry** portfolio. It changes selection and documentation; it does not alter the circuit or ZIP bytes, invent new simulations or claim an official competition score.

## Measured result

The local composite is **26.975162261465695–27.016402925509315**, **25.47–25.67% above source v0.3**. The range enumerates all sixteen combinations of two measured inverse costs, four DQI costs and two chemistry costs against archived baselines; it is not sixteen independent whole-portfolio trials or a confidence interval. All declared salts and the one observed DQI value-error penalty remain included.

| Component | Qubits | Verified coverage |
|---|---:|---|
| Inverse square root |46| Exact proof over all 3,133,452 legal inputs and HMR branches; two full 200,540,928-shot receipts |
| DQI |889| Four full 102,400-shot checks, all PASS; one value error in salt A, zero observed phase errors |
| Chemistry |427| Two full 78,080-shot checks, frozen deep512 reconstruction |

All eighteen freshly reconstructed files match the receipt-bound identities. Inverse and chemistry native results are reused only because exact output hashes match. DQI has four new full native checks. The archive passes seventeen stock circuit readers, the NPZ reader, CRC/extraction and exact input/receipt bindings. [Detailed measurements and source instructions](../studies/source_portfolio889/README.md).

## Source gate and historical record

**I01 is CLOSED for selected v0.4.0**: its actual source algorithms and mathematical inputs generate the selected exact outputs and have full local verification. This closure follows the explicit scope decision; it does not assert recovery of any different circuit's generator.

**I01-HIST remains OPEN** for the original inverse `26ebf39df3b13e5fd2d923d1b9988043b107b64f6e21efc5cc9bc76f5d56adec` and DQI `e9f54be304cbdcda7306729c335b1a2314a45d0ca818e05cf60e45ddee969bc4` generators. [Historical recovery record](SOURCE_RECOVERY.md). The previous [v0.3 selection](../evidence/selection/v0.3.0.json) and all native/build records remain preserved. Pre-promotion experimental records saying promotion NONE or historical I01 OPEN describe their execution-time state; the current authority is [SELECTED_CANDIDATE.json](../SELECTED_CANDIDATE.json).

## Exact artifacts and reproduction

- Submission ZIP: **49,338,223 bytes**, SHA256 `0059f20ad2b9822318c208d28093714ca0e9440271262387c5b1df0109d3b30e`.
- Inverse: `321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177`.
- DQI: `7cbe8ecf6f6e9743529b574f019504bb1712ce06fbb570c719ce9d9e2c914cd9`.
- Chemistry NPZ: `33393e0b34a1357ab3964954316f35560894d64492136d2475f0f279f276ebaa`.

Use the Linux [complete construction command](SOURCE_PORTFOLIO.md). The pinned source archives, numerical inputs, constructor and audit shim are included; the original competition data/verifiers and CPython-3.13 native runtime are obtained separately. No GPU or online download is needed during construction. The source bundle distributed with this release is byte-identical to the reviewed source46/DQI889 study bundle; current selection metadata and these release notes are in the tagged repository. Construction and full native qualification are distinct steps.

Run `python tools/check_repository.py` for source manifest, selection, receipt and all sixteen cost-combination integrity checks. `tools/render_selected_figure.py` renders the selected-resource diagram from those same receipts. Neither command reruns the native simulations.

## Authorship and limits

Francisco Angulo de Lafuente, [ORCID](https://orcid.org/0009-0001-1634-7063), 2026-11-14: project chemistry optimization, integration, measurements and documentation, **MIT OR Apache-2.0**. The inverse and DQI generator packages are **Syed Asad Ali's Apache-2.0 work**, retaining their notices. Preserve all upstream attribution.

The underlying study's Goldfish/EGM review converged after three rounds with two consecutive clean final rounds. Promotion metadata, current guidance and selection checks receive a separate fresh-context review recorded in [promotion review](PROMOTION_REVIEW.md). Reviewers do not replace native measurements. No Kaggle submission, official score, acceptance, eligibility certification, prize or quantum-hardware result is asserted. Chemistry reconstruction begins at the frozen recipe; bitwise deterministic retraining is not established.
