# Credits and modification notice

The 889-qubit decoder architecture and the complete authenticated source packet
come from SomeJoint / Agniv Banerjee and the contributors credited within that
packet, notebook V21/run363462588:
https://www.kaggle.com/code/somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi
Apache-2.0 source and notices are retained byte for byte. The same compiled
public decoder also appears in Ahmed Berat Özer V12/run363485081.

Our change transfers our previously tested node policy: group7 uses the
homogeneous path; groups8/9 use the ordinary path; groups10..16 are homogeneous.
It is applied before the upstream source-cloning entry is imported. This changes
the compiled circuit from889 to888 qubits and repairs the two recorded cases.
We do not claim to have invented the decoder architecture or proved correctness
for every possible input. The source packet is unmodified; rebuild_dqi.py is our
wrapper. Original and portable wrapper snapshots are retained in the evidence.

Parallel scheduling is credited to manwithacat, reviewed commit
eb36f245029140e70a5797b33dc8c373dccbc4a5, Apache-2.0. Our Windows spawn/explicit
seed adapter changes scheduling only. Official sampling and scoring code remain
unchanged. Project diagnostic adapters require the documented project layout;
the standalone stock rebuild needs only source-packet/ and Kickmix dependencies.
