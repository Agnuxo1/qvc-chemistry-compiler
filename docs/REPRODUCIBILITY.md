# Reproduce the frozen result

## Environment

Use Python 3.13 and the native Kickmix build supplied by the competition for your operating system. Install requirements.txt in an isolated environment. Full verifiers use their stock competition dependencies; install those from the official package. Obtain and unpack the official competition data yourself; keep it outside the repository. FeMoCo integral data and native runtime are not redistributed here.

The two paths below must point to the unpacked data root (containing verifiers/) and the directory containing kickmix.so on Linux or the matching Python-3.13 .pyd on Windows.

```bash
python -m pip install -r requirements.txt
python tools/build_chemistry.py build/chemistry --recipe recipes/h14-main --data /path/to/official/data --runtime /path/to/native/runtime
python tools/verify_local.py chem build/chemistry build/chemistry-receipt.json --data /path/to/official/data --runtime /path/to/native/runtime --salt replication-a
python tools/check_repository.py
```

Expected build: 15 KMB circuits plus submission.npz, all 16 hashes equal recipes/h14-main/manifest.json; 14,848 total Toffolis, 427 total qubits and chemistry ratio approximately 11.2343975 in the stock full check. Use a new output directory for each run; tools preserve existing evidence.

## Three-task control

```bash
python tools/build_reference_portfolio.py build/reference --data /path/to/official/data --runtime /path/to/native/runtime
```

This builds the two organizer reference algorithms plus frozen s37 chemistry from source. It must match all 18 expected hashes. It is the source-complete control, with local composite approximately 2.239566; it is not the optimized 25.21–25.25 performance portfolio.

## Performance components

For the complete source-generated alternative, use:

```bash
python tools/build_source_portfolio.py build/source-candidate --recipe recipes/h14-main --data /path/to/official/data --runtime /path/to/native/runtime
```

This builds the source-generated invsqrt c3f3ac25 and DQI888 plus the selected chemistry recipe. The constructor was executed on Linux and its eighteen output hashes were bound to full native checks. The curated source modules, numeric coefficients, authenticated DQI manifest and upstream licenses are included. See [source portfolio and packaging](SOURCE_PORTFOLIO.md).

The higher-index binary performance components can separately be fetched with:

```bash
python -m pip install kaggle
python tools/fetch_performance_inputs.py build/public-inputs
```

This downloads public compiled inputs and checks their published SHA256 and license files. It does not claim to generate invsqrt or DQI from their original algorithms. Rebuild chemistry separately. The exact-source gate in docs/SOURCE_RECOVERY.md must pass before calling that combined performance candidate complete.

## What was executed

The evidence/official JSON files bind original input hashes, verifier source hashes, parameters and native results. Linux and Windows both reconstructed the frozen chemistry outputs exactly. The Windows invsqrt run was interrupted after the full Linux PASS; it is not reported as a Windows PASS. The initial cross-platform NPZ difference was traced to the ZIP creator-system byte and corrected by deterministic metadata; the diagnosis is preserved.

The public entry points were also executed: evidence/replication contains a fresh full chemistry PASS, a repeated ancilla experiment and an 18-file Linux source-control build bound to the current constructor hash. The first integration attempt included the chemistry reconstruction report among the 18 submission files; the corrected constructor moves that report outside the artifact directory before counting and hashing. The corrected entry point was rerun successfully.

```bash
python tools/check_ancillas.py build/ancillas.json --runtime /path/to/native/runtime
```

This repeats the 3,344 cases per variant using the original attributed primitive source. It does not run a full QVC task.

## Figures

```bash
python -m pip install -r requirements-figures.txt
python tools/render_figures.py
```

Figures use evidence/official as numeric input. Animations illustrate reported results or a labelled schematic; they are not experiment videos. The renderer writes assets/figure-data.json and a contact sheet for inspection. Authorship appears in the figures and GIF metadata.

Font selection uses Segoe UI when installed, otherwise DejaVu Sans. Image bytes may differ between font or Pillow versions; the measured numerical data and released image hashes are recorded separately.

---
Research author: **Francisco Angulo de Lafuente** · [ORCID](https://orcid.org/0009-0001-1634-7063) · 2026-11-10.
Own text: MIT OR Apache-2.0; third-party materials retain their notices.
