"""Freeze the independently rebuilt DQI repair and package the checked hybrid.

Local work only: no Kaggle mutation, entry or ACTIVE_BASELINE promotion.
Chemistry, inverse and DQI evidence are bound to the actual submitted bytes.
"""
import argparse
from datetime import datetime, timezone
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'artifacts/public-rising-review-001'
BANK = ROOT / 'datasets/qcc-narrow888-dqi-v1'
CHEM_BANK = ROOT / 'datasets/qcc-own-angle-compiler-v4'
DQI_HASH = '736f3055850794c6beaedf8de5f7dafa1c270e2b57edd403ffa96abf6d207741'
CONTROL_HASH = '6349d2bc82eb1ef3a4e8c52c71a312823d756532517463b5e18eb25cc81195a8'
INV_HASH = '9a8627c812833a6feca6eb82239f38d1a9a5e1eee299a9a7af9abd85e36339be'
SOURCE_HASH = 'a6819e88d3dada84f158023c9ba22e7d2c06ee53ad9d0c691bdd2e701d88d8b8'
FULLS = ['narrow888-full-stock-a-001', 'narrow888-full-fork-a-001', 'narrow888-full-fork-b-001']


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf8')


def now():
    return datetime.now(timezone.utc).isoformat()


def check_frozen(path):
    manifest = read(path / 'MANIFEST.json')
    assert manifest['state'] == 'FROZEN_ALL_REQUIRED_LOCAL_GATES_BOUND'
    assert all(sha(path / name) == digest for name, digest in manifest['files'].items())
    return manifest


def dqi_gates():
    verifier = ROOT / 'reference/competition/verifiers/dqi/verify_submission_dqi.py'
    full = [read(REVIEW / name / 'report.json') for name in FULLS]
    for r in full:
        assert r['status'] == 'COMPLETE' and r['returncode'] == 0
        assert r['circuit_sha256'] == DQI_HASH and r['verifier_sha256'] == sha(verifier)
        assert r['salt'] == 'notebook-verification' and r['scheduler'] == 'spawn'
        assert r['seeded_scheduler_sha256'] == sha(ROOT / 'tools/dqi_seeded_spawn.py')
        assert r['scheduler_source_sha256'] == sha(ROOT / 'reference/public-tools/manwithacat-kickmix-eb36f245/verify_parallel.py')
        z = r['result']
        assert z['status'] == 'PASS' and z['verified_shots'] == 102400
        assert z['value_errors'] == z['phase_errors'] == 0
        assert z['circuit_sha256'] == DQI_HASH and z['num_qubits'] == 888
    assert full[0]['runtime'] == 'stock' and full[0]['kickmix_version'] == '1.0.0'
    assert full[1]['runtime'] == full[2]['runtime'] == 'fork'
    assert full[0]['explicit_seed'] == full[1]['explicit_seed']
    assert full[0]['result'] == full[1]['result'], 'Full stock/fork parity failed'
    assert len({r['explicit_seed'] for r in full}) == 2
    for runtime in ['stock', 'fork']:
        fixed = read(REVIEW / f'narrow888-fixed-{runtime}-001/report.json')
        assert fixed['circuit_sha256'] == DQI_HASH and fixed['runtime'] == runtime
        assert len(fixed['rows']) == 2
        for row in fixed['rows']:
            assert len(row['runs']) == 2
            for run in row['runs']:
                assert run['replicas'] == 256
                assert all(run[k] == 0 for k in ['value_errors', 'phase_errors', 'syndrome_changed_max', 'dirty_ancilla_max'])
        negative = read(REVIEW / f'somejoint-fixed-{runtime}-001/report.json')
        assert negative['circuit_sha256'] == CONTROL_HASH
        phase = next(row for row in negative['rows'] if row['source_kind'] == 'phase')
        assert sum(r['phase_errors'] for r in phase['runs']) == 512
    grid = read(REVIEW / 'narrow888-weight-grid-001/report.json')['rows']
    assert len(grid) == 1 and grid[0]['circuit_sha256'] == DQI_HASH
    assert grid[0]['shots'] == 9216 and grid[0]['value_errors'] == grid[0]['phase_errors'] == 0
    assert {r['weight'] for r in grid[0]['rows']} == set(range(36))
    assert all(r['shots'] == 256 and r['value_errors'] == r['phase_errors'] == 0 for r in grid[0]['rows'])
    control = read(REVIEW / 'narrow889-control-001/report.json')
    assert control['sha256'] == CONTROL_HASH and control['exact_public_control_match'] and control['Q'] == 889
    portable = REVIEW / 'portable-dqi-stock-rebuilt-001'
    rebuilt = read(portable / 'report.json')
    assert rebuilt['sha256'] == sha(portable / 'dqi.kmb') == DQI_HASH
    assert rebuilt['Q'] == 888 and rebuilt['homogeneous_groups'] == [7, *range(10, 17)]
    stage = REVIEW / 'portable-dqi-stage-001'
    assert rebuilt['source_sha256'] == sha(stage / 'rebuild_dqi.py')
    packet = stage / 'source-packet'
    assert not list(stage.rglob('*.kmb')), 'Portable source input must contain no compiled teachers'
    assert sha(packet / 'AUTHENTICATED_SOURCE_MANIFEST.json') == SOURCE_HASH
    pins = read(packet / 'AUTHENTICATED_SOURCE_MANIFEST.json')
    assert len(pins) == 92 and all(sha(packet / name) == digest for name, digest in pins.items())
    assert sha(REVIEW / 'narrow889-repair-001/dqi.kmb') == DQI_HASH
    return full


def freeze():
    full = dqi_gates()
    assert not BANK.exists(), 'Frozen bank must never be overwritten'
    BANK.mkdir(parents=True)
    stage = REVIEW / 'portable-dqi-stage-001'
    shutil.copytree(stage / 'source-packet', BANK / 'source-packet')
    shutil.copyfile(stage / 'rebuild_dqi.py', BANK / 'rebuild_dqi.py')
    shutil.copyfile(REVIEW / 'portable-dqi-stock-rebuilt-001/dqi.kmb', BANK / 'dqi.kmb')
    shutil.copyfile(stage / 'source-packet/LICENSE', BANK / 'LICENSE')
    evidence = BANK / 'evidence'
    evidence.mkdir()
    names = [*FULLS, 'narrow888-fixed-stock-001', 'narrow888-fixed-fork-001',
             'somejoint-fixed-stock-001', 'somejoint-fixed-fork-001', 'narrow888-weight-grid-001',
             'narrow889-control-001', 'narrow889-repair-001', 'portable-dqi-stock-rebuilt-001']
    for name in names:
        dest = evidence / name
        dest.mkdir()
        for filename in ['report.json', 'generator_source.py', 'generated-failures.jsonl']:
            src = REVIEW / name / filename
            if src.is_file():
                shutil.copyfile(src, dest / filename)
    for rel in ['somejoint-source-static-review.json', 'somejoint-v21/ingest_audit.json']:
        shutil.copyfile(REVIEW / rel, evidence / Path(rel).name)
    shutil.copyfile(ROOT / 'datasets/qcc-public-dqi-counterexamples-v1/counterexamples.jsonl', evidence / 'known-counterexamples.jsonl')
    adapters = BANK / 'project-adapters'
    adapters.mkdir()
    for filename in ['benchmark_dqi_runtimes.py', 'dqi_seeded_spawn.py', 'check_dqi_weight_grid.py', 'finalize_rising888_portfolio.py']:
        shutil.copyfile(ROOT / 'tools' / filename, adapters / filename)
    upstream = ROOT / 'reference/public-tools/manwithacat-kickmix-eb36f245'
    for filename in ['verify_parallel.py', 'LICENSE']:
        shutil.copyfile(upstream / filename, adapters / ('manwithacat-' + filename))
    (BANK / 'CREDITS.md').write_text('''# Credits and modification notice

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
''', encoding='utf8')
    (BANK / 'README.md').write_text('''# Rebuildable 888-qubit DQI repair

Local derivative research bank; not an independent scientific dataset.
Run with Python3.12 and stock Kickmix1.0.0 (NumPy2.2.6/SciPy1.15.3 environment):

```console
python rebuild_dqi.py --policy repair --runtime stock --out rebuilt-dqi
```

The rebuild reads authenticated text sources only, no input KMB. An independent
stock rebuild already matched the selected bytes from our earlier fork build.
The control policy reproduces the public889-qubit source bytes exactly.

Three complete102400-shot checks passed: stock and fork at the same seed
2026102801 (entire result dictionaries identical), and fork at independent seed
20261029181. Two known value/phase cases pass2048 targeted replicas across both
runtimes. A fresh36-weight grid passes9216 diagnostic shots. Targeted checks are
biased diagnostics, not unbiased error estimates or a universal proof. The raw
public889 circuit fails512/512 phase replicas in each runtime and is not selected.
Official verifier SHA and exact source/circuit hashes are bound in the manifest.
The Windows spawn scheduler is an explicit adaptation, not an unmodified Linux
CLI invocation. No hosted Kaggle run or competition submission is claimed.
''', encoding='utf8')
    files = {p.relative_to(BANK).as_posix(): sha(p) for p in sorted(BANK.rglob('*')) if p.is_file()}
    manifest = dict(schema='qcc-narrow888-dqi/1.0', state='FROZEN_ALL_REQUIRED_LOCAL_GATES_BOUND',
        created_utc=now(), files=files, selected_circuit_sha256=DQI_HASH,
        source_packet_manifest_sha256=SOURCE_HASH, public_control_sha256=CONTROL_HASH,
        Q=888, static_T=457358, homogeneous_groups=[7, *range(10, 17)],
        full_verifier_sha256=full[0]['verifier_sha256'], full_shots=307200,
        unique_full_seeds=sorted({r['explicit_seed'] for r in full}),
        stock_fork_entire_result_parity=True, standalone_no_KMB_input_rebuild_byte_exact=True,
        known_case_replicas=2048, diagnostic_weight_grid_shots=9216,
        known_cases_pass=True, universal_correctness_proven=False,
        official_gated_input_exported=False, published=False,
        freezer_source_sha256=sha(Path(__file__)))
    dump(BANK / 'MANIFEST.json', manifest)
    print(json.dumps(dict(action='FROZEN', files=len(files), manifest_sha256=sha(BANK / 'MANIFEST.json'))), flush=True)


def package():
    dm = check_frozen(BANK)
    cm = check_frozen(CHEM_BANK)
    full_dqi = dqi_gates()
    chem_dir = REVIEW / 'own-three-delta-native-001/dfthcsos'
    chem_hashes = {p.name: sha(p) for p in chem_dir.iterdir() if p.is_file()}
    assert set(chem_hashes) == {'submission.npz', *[f'angle_k_{i}.kmb' for i in range(15)]}
    assert chem_hashes['submission.npz'] == cm['selected_factor_sha256']
    assert {k: v for k, v in chem_hashes.items() if k.endswith('.kmb')} == cm['native_circuit_hashes']
    receipt_paths = [ROOT / f'runs/rising-three-own-{tag}-001/receipt.json' for tag in ['a', 'b']]
    receipts = [read(p) for p in receipt_paths]
    seeds = set()
    for r in receipts:
        assert r['candidate_files'] == chem_hashes and r['verification_status'] == 'PASS'
        assert r['verified_shots'] == 78080 and r['returncode'] == 0 and r['label'] == 'full'
        assert r['verifier_sha256'] == sha(ROOT / 'reference/competition/verifiers/dfthcsos/verify.py')
        seeds.add(r['command'][r['command'].index('--seed') + 1])
    assert len(seeds) == 2 and receipts[0]['score'] == receipts[1]['score']
    reused_path = ROOT / 'artifacts/top10-new-notebook-001/kaggle-v2/reproduction_audit.json'
    reused = read(reused_path)
    inv = reused['reused_task_results']['invsqrt']
    assert inv['status'] == 'PASS' and inv['verified_shots'] == 200540928
    base = ROOT / 'artifacts/public-morning-review-001/kaggle-v11'
    assert read(base / 'zip_audit.json')['members']['invsqrt.kmb'] == INV_HASH
    assert sha(base / 'submission/invsqrt.kmb') == INV_HASH
    out = REVIEW / 'portfolio-repair888-001'
    assert not out.exists()
    out.mkdir()
    sub = out / 'submission'
    shutil.copytree(chem_dir, sub / 'dfthcsos')
    shutil.copyfile(BANK / 'dqi.kmb', sub / 'dqi.kmb')
    shutil.copyfile(base / 'submission/invsqrt.kmb', sub / 'invsqrt.kmb')
    files = {p.relative_to(sub).as_posix(): sha(p) for p in sorted(sub.rglob('*')) if p.is_file()}
    assert len(files) == 18 and files['dqi.kmb'] == DQI_HASH and files['invsqrt.kmb'] == INV_HASH
    metric_path = ROOT / 'artifacts/current-code-leader-review-001/official_metric.py'
    spec = importlib.util.spec_from_file_location('official_metric', metric_path)
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    arrays = metric.read_npz(sub / 'dfthcsos/submission.npz', {
        'U': ('f', ('R', 'B', 76)), 'W': ('f', ('R', 'B', 'C')),
        'H2_I': ('f', ('R', 'C')), 'H1_I': ('f', ()), 'Hsym_lower': ('f', (2926,)),
        'tree_edges': ('iu', (75, 2)),
    })
    circuits = {}
    for name in files:
        if name.endswith('.kmb'):
            c = metric.read_circuit(sub / name, 1 if name == 'invsqrt.kmb' else 4165 if name == 'dqi.kmb' else 128)
            circuits[name] = dict(Q=c.num_qubits, static_T=int(c.operation_statistics().num_toffoli_like))
            del c
            gc.collect()
    archive = out / 'submission.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in sorted(files):
            z.write(sub / name, name)
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist()) == 18 and set(z.namelist()) == set(files)
        for name, digest in files.items():
            with z.open(name) as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == digest
    reference_path = ROOT / 'artifacts/public-b1/QCC_RELEASE_MANIFEST.json'
    ref = read(reference_path)['reference_costs']
    costs = dict(invsqrt=inv['score'], dqi=full_dqi[0]['result']['score'], dfthcsos=receipts[0]['score'])
    gm = (ref['invsqrt']/costs['invsqrt'] * ref['dqi']/costs['dqi'] * ref['dfthcsos']/costs['dfthcsos']) ** (1/3)
    fallback = read(REVIEW / 'portfolio-repair896-001/portfolio_comparison.json')
    assert sha(Path(fallback['zip'])) == fallback['zip_sha256']
    report = dict(status='LOCAL_FULL_CHEM_DQI_VERIFIED_KAGGLE_NOT_RUN_NOT_SUBMITTED', created_utc=now(),
        candidate_id='own-v4-three-credited-AND-repair888', policy='repair888', folder=str(sub), zip=str(archive),
        zip_sha256=sha(archive), expected_members=files, local_composite_estimate=gm, observed_new_public_score=None,
        task_costs=costs, reference_costs=ref, reference_cost_manifest_sha256=sha(reference_path),
        chemistry_T=16270, chemistry_Q=430, chemistry_AND_per_pass=4170,
        credited_AND_per_pass_savings=dict(Heliosli_V20=2, Dmitrii_V34=1),
        chemistry_source_bank=str(CHEM_BANK), chemistry_manifest_sha256=sha(CHEM_BANK / 'MANIFEST.json'),
        dqi_source_bank=str(BANK), dqi_manifest_sha256=sha(BANK / 'MANIFEST.json'),
        dqi_Q=888, dqi_static_T=457358, dqi_sha256=DQI_HASH,
        dqi_common_seed_cost_reduction_vs_repair896_percent=(1-costs['dqi']/413022456812.3662)*100,
        fresh_chemistry_receipts=[str(p.relative_to(ROOT)) for p in receipt_paths],
        fresh_chemistry_seeds=sorted(seeds), fresh_chemistry_shots=156160,
        fresh_dqi_reports=[str((REVIEW / name / 'report.json').relative_to(ROOT)) for name in FULLS],
        fresh_dqi_shots=307200, unique_dqi_full_seeds=dm['unique_full_seeds'],
        full_stock_fork_result_exact_parity=True, known_cases_pass=True,
        known_case_replicas=2048, diagnostic_weight_grid_shots=9216, universal_correctness_proven=False,
        fresh_all_tasks=False, all_tasks_have_full_pass_evidence=True,
        reused_inverse_evidence=str(reused_path.relative_to(ROOT)), reused_inverse_evidence_sha256=sha(reused_path),
        reused_inverse_hash=INV_HASH, reused_inverse_verified_shots=200540928,
        reader_preflight=dict(status='PASS', metric_source_sha256=sha(metric_path), circuits=circuits,
            npz_shapes={k: list(v.shape) for k, v in arrays.items()}), zip_18_member_readback='PASS',
        repair896_fallback=dict(zip=fallback['zip'], zip_sha256=fallback['zip_sha256'], local_estimate=fallback['local_composite_estimate']),
        hosted_execution_required_before_baseline_promotion=True, submitted=False, active_baseline_unchanged=True,
        packaging_source_sha256=sha(Path(__file__)))
    dump(out / 'portfolio_comparison.json', report)
    dump(ROOT / 'research/NEXT_LOCAL_CANDIDATE.json', report)
    print(json.dumps({k: report[k] for k in ['status', 'zip_sha256', 'local_composite_estimate', 'task_costs']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'package'])
    args = parser.parse_args()
    freeze() if args.action == 'freeze' else package()
