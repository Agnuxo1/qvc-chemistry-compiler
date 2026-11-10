# A source-built DQI alternative

The recovered public source bank contains a complete 888-qubit decoder construction. This is a tested alternative to the selected, source-incomplete e9f54be3 public circuit. It is not a reconstruction of that selected file.

## Demonstrated construction

The unmodified Atakan Aldemir wrapper authenticates 92 text-source files, builds SomeJoint's 889-qubit architecture with the published repair policy, and emits the 888-qubit circuit without a KMB input. The exact emitted SHA256 is `736f3055850794c6beaedf8de5f7dafa1c270e2b57edd403ffa96abf6d207741`.

| Property | Measured value |
|---|---:|
| Qubits | 888 |
| Static Toffoli-like operations | 457,358 |
| Total circuit operations | 60,336,624 |
| Source build time in this Linux run | 106.09 s |
| Full check, independent salt a | PASS; 58.9945523685x; 0 value / 1 phase error |
| Full check, independent salt b | PASS; 59.2655314845x; 0 value / 0 phase errors |
| Shots per check | 102,400 |

The two local ratios use the archived DQI reference cost. Both salts are retained; they are not confidence bounds. The current selected e9f54be3 file has higher measured performance (64.9282–65.2264x on its recorded salts), so the source bank is not presented as a performance improvement over it.

## Reproduce

Use Python 3.13, the official native Kickmix runtime and the stock verifier dependencies described in REPRODUCIBILITY.md.

```bash
python tools/build_dqi_source.py build/dqi888 --runtime /path/to/native/runtime
python tools/verify_local.py dqi build/dqi888/dqi.kmb build/dqi888-a.json --data /path/to/official/data --runtime /path/to/native/runtime --salt source888-independent-20261110-a
```

vendor/dqi888 retains the source packet, LICENSE, CREDITS and upstream manifest. evidence/official/dqi888-source-a.json and -b.json bind exact generator, circuit and verifier hashes to the full results. No competition data, native runtime or compiled DQI input is included in this source package.

## Provenance

SomeJoint / Agniv Banerjee and the credited team authored the decoder architecture and source packet. Atakan Aldemir published the repaired node policy and rebuild wrapper under Apache-2.0. The project by Francisco Angulo de Lafuente recovered, independently rebuilt, verified and integrated that credited release; it does not claim the decoder as a new invention. See the [public source bank](https://www.kaggle.com/datasets/atakanaldemir/qcc-native-chemistry-and-888q-source-bank).

## Observations

Exact source generation and two full native sampled checks are demonstrated. They do not prove every possible decoder input or establish prize eligibility. The original performance portfolio still needs its exact invsqrt and e9f54be3 DQI sources; its I01 gate is not closed by this alternative alone.

Research author: Francisco Angulo de Lafuente · ORCID https://orcid.org/0009-0001-1634-7063. Own document/wrapper: MIT OR Apache-2.0; decoder source and upstream wrapper: Apache-2.0.
