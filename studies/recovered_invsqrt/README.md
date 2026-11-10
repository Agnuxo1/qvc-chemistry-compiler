# Recovered inverse-square-root numerical semantics

All256 numerical coefficient triplets and the two special phase-readout rules of the public62-qubit26ebf39d circuit have been recovered. An independent mathematical implementation matches its native phase **exactly for all 3,133,452 legal inputs**, using **one stochastic measurement branch per input**. Every input is restored and scratch is clean. The numerical worst error/tolerance is **0.9993237694056958 at x=161**, equal to the archived official result.

This recovers the numerical function. Rebuilding the original62-qubit circuit bytes and its complete memory schedule remains open. The comparison is not a proof for every coherent state or every possible measurement branch.

## Mathematical model

Let `b` be the14-bit normalized within-segment integer and `s` the denormalization shift. Each normalized address selects a recovered triplet `(C0,C1,C2)` and an integer high seed `H` from `recipe.json`. The high seed is held fixed for that address; `L=Y-H*2^20` is the low residual. The recovered global formulas are:

```python
def rd(v, e):
    return (v >> e) + ((v >> (e-1)) &1) if e>0 else v <<(-e)

T = C1 - sum((2*((b>>i)&1)-1)*rd(C2,12-i) for i in range(6,14))
Y = C0 - sum((2*((b>>i)&1)-1)*rd(T,13-i) for i in range(14))
L = Y - (H<<20)
```

The original reader replaces the standard contribution of bit 1 of L by a phase at position1 controlled by the XOR of the two low shift flags. For `s>=8`, it folds the omitted high L positions27–29 into H; these legal inputs have `b=0`. The exact integer equations and unchanged phase weights are executable in `check_original_semantics.py`, `recipe.json` and `angles.json`. The diagnostic code reads a separate reference circuit only to compare outputs; it does not generate a circuit from that input.

```bash
python studies/recovered_invsqrt/check_original_semantics.py --root studies/recovered_invsqrt --data /path/to/official/data --runtime /path/to/native/runtime --circuit /path/to/original/invsqrt.kmb --out build/original-semantic-check
```

The original circuit must hash to26ebf39df3b13e5fd2d923d1b9988043b107b64f6e21efc5cc9bc76f5d56adec. It is not bundled in this study. The receipt is [invsqrt-original-semantic-all-inputs.json](../../evidence/replication/invsqrt-original-semantic-all-inputs.json).

## Independently constructed source circuit

A separate construction uses the recovered coefficients, the credited Marsyas/Gluzdov algorithm and newly fitted global phase weights. Its frozen numeric recipe and phase fit are `numeric-recipe.json` and `phase-fit.json`; its source entry point forbids external compiled circuit inputs.

```bash
python tools/build_inv_recovered.py build/recovered-study --data /path/to/official/data --runtime /path/to/native/runtime
python tools/verify_local.py invsqrt build/recovered-study/invsqrt.kmb build/recovered-native.json --data /path/to/official/data --runtime /path/to/native/runtime --salt independent-a
```

| Measured property | Result |
|---|---:|
| Exact generated SHA256 |29480dd3285825e2718bca69843803d57337e7ac7626a1adf043be5801a8a7ca |
| Qubits / static Toffoli-like operations |88 /1,299 |
| Full official native shots |200,540,928; PASS |
| Native cost |141,336.53747428907 |
| Worst error/tolerance |0.9999250919950656 |

The portable public wrapper was executed and reproduced this exact output from the frozen numeric inputs. Its source-bound receipt is [invsqrt-recovered256-portable-build.json](../../evidence/replication/invsqrt-recovered256-portable-build.json); the complete native result is [invsqrt-recovered256-full.json](../../evidence/official/invsqrt-recovered256-full.json).

## Observations and attribution

The88Q study costs more than the selected87Q c3 source circuit (140,178.1847720425). It is retained as a verified reconstruction experiment and is not selected for the submission package. Neither this construction nor the recovered mathematical function closes the exact-source gate for the original 62Q26ebf39d circuit or the original e9f54be3 DQI file.

The polynomial family and source architecture are credited to their upstream researchers, including Marsyas/Houssem Alayet and Dmitrii Gluzdov. Numeric semantics were recovered from the public performance circuit credited in [attribution](../../docs/ATTRIBUTION.md). Francisco Angulo de Lafuente developed and checked the recovery, independent mathematical comparison, global phase fit and source integration. Upstream source and notices remain unchanged.

Research author: Francisco Angulo de Lafuente · ORCID https://orcid.org/0009-0001-1634-7063 ·2026-11-10. Own text and wrapper: MIT OR Apache-2.0; upstream source retains Apache-2.0 and its notices.
