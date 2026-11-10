# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Check tracked-source integrity, local links and pinned recipe/evidence math."""
from pathlib import Path
import ast
import hashlib
import json
import math
import re

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ignored={'.git','.venv','__pycache__','build','.cache','work','data'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts)&ignored)]
    errors=[]; checked_py=0; links=0
    for p in files:
        rel=p.relative_to(ROOT).as_posix()
        if p.suffix=='.py':
            try:ast.parse(p.read_text(encoding='utf-8-sig'),filename=rel);checked_py+=1
            except SyntaxError as e:errors.append(f'Python syntax: {rel}:{e.lineno}')
        if p.suffix in ('.py','.json','.md','.txt','.yml','.cff'):
            body=p.read_text(encoding='utf-8-sig',errors='replace')
            for label,pattern in [('private key',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),('GitHub credential',r'(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{40,})'),('HF credential',r'hf_[A-Za-z0-9]{30,}'),('credential URL',r'https?://[^\s/:@]+:[^\s/@]+@')]:
                if re.search(pattern,body):errors.append(f'Potential {label}: {rel}')
        if p.suffix=='.md' and not rel.startswith(('vendor/','evidence/prior-audit/')):
            for dest in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if re.match(r'^(https?://|#|mailto:)',dest):continue
                dest=dest.split('#')[0].strip('<>')
                if dest and not (p.parent/dest).exists():errors.append(f'Broken link: {rel} -> {dest}')
                links+=1
        if p.stat().st_size>95_000_000:errors.append(f'Oversize Git file: {rel}')
    recipes=sorted((ROOT/'recipes').glob('*/manifest.json'))
    for manifest_path in recipes:
        recipe=manifest_path.parent;m=json.loads(manifest_path.read_text())
        for key,name in (('table_sha256','table.npz'),('plan_sha256','plan.json')):
            if sha(recipe/name)!=m[key]:errors.append(f'Recipe drift: {recipe.name}/{name}')
        for name,value in m['source_sha256'].items():
            if sha(recipe/'src'/name)!=value:errors.append(f'Recipe source drift: {recipe.name}/{name}')
        assert len(m['expected_files'])==16
        if 'gauge_transform' in m:
            gauge=m['gauge_transform']
            assert sha(recipe/'gauge-initial.npz')==gauge['initial_table_sha256']
            assert sha(recipe/'rotation.npy')==gauge['rotation_sha256']
            assert gauge['augmented_gram_max_drift']<1e-10
    inv_build=json.loads((ROOT/'evidence/replication/invsqrt-runtime-bound-build.json').read_text())
    assert inv_build['status']=='EXACT_SOURCE_ANCESTOR_REBUILT'
    assert inv_build['constructor_sha256']==sha(ROOT/'tools/build_inv_source.py')
    for name,value in inv_build['source_sha256'].items():
        assert sha(ROOT/'vendor/invsqrt_source'/name)==value,name
    inv_check=json.loads((ROOT/'evidence/official/invsqrt-source-c3.json').read_text())
    assert inv_check['circuit_sha256']==inv_build['sha256']
    assert inv_check['official_result']['status']=='PASS'
    assert inv_check['official_result']['verified_shots']==200540928
    dqi_root=ROOT/'vendor/dqi888/source-packet'
    dqi_pins=json.loads((dqi_root/'AUTHENTICATED_SOURCE_MANIFEST.json').read_text())
    for name,value in dqi_pins.items():assert sha(dqi_root/name)==value,name
    for name in ('dqi888-source-a.json','dqi888-source-b.json'):
        result=json.loads((ROOT/'evidence/official'/name).read_text())['official_result']
        assert result['status']=='PASS' and result['verified_shots']==102400
    selection=json.loads((ROOT/'SELECTED_CANDIDATE.json').read_text())
    package=json.loads((ROOT/selection['package_evidence']).read_text())
    build=json.loads((ROOT/selection['source_build_evidence']).read_text())
    assert package['status']=='PASS' and len(package['members'])==18
    assert selection['archive_sha256']==package['archive_sha256']
    assert selection['local_composite_indices']==package['local_composite_indices']
    assert build['outputs']=={n:v['sha256'] for n,v in package['members'].items()}
    assert build['constructor_sha256']==sha(ROOT/'tools/build_source_portfolio.py')
    assert len(package['official_readers'])==17 and all(x['status']=='PASS' for x in package['official_readers'])
    receipt_names={'invsqrt':'invsqrt-source-c3.json','dqi_a':'dqi888-source-a.json','dqi_b':'dqi888-source-b.json','chem_a':'chemistry-h14-main-a.json','chem_b':'chemistry-h14-main-b.json'}
    for key,name in receipt_names.items():
        receipt=ROOT/'evidence/official'/name
        assert sha(receipt)==package['receipt_sha256'][key]
        assert json.loads(receipt.read_text())['official_result']['status']=='PASS'
    feature_source=(ROOT/'compiler/rasgos.py').read_text(encoding='utf-8')
    if 'SPDX-License-Identifier: Apache-2.0' not in feature_source or ':: MIT ::' in feature_source:
        errors.append('Derived feature compiler license scope drift')
    a=json.loads((ROOT/'evidence/official/quimica-s37-64-a.json').read_text())
    r=a['official_result'];assert r['status']=='PASS'
    assert math.isclose(a['improvement'],a['baseline']/r['score'],rel_tol=1e-12)
    assert r['toffoli_count']==14848 and r['num_qubits']==427
    assert r['metrics']['error_2']<=.020
    for name in ('dqi-gengsr-102400-a.json','dqi-gengsr-102400-b.json','invsqrt-gengsr-64-linux-a.json'):
        assert json.loads((ROOT/'evidence/official'/name).read_text())['official_result']['status']=='PASS'
    manifest=ROOT/'SOURCE_MANIFEST.json'
    if manifest.exists():
        for name,digest in json.loads(manifest.read_text())['files'].items():
            if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:errors.append(f'Publication manifest drift: {name}')
    report={'status':'PASS' if not errors else 'FAIL','python_sources':checked_py,'local_links':links,'files':len(files),'recipes':len(recipes),'invsqrt_source_modules':len(inv_build['source_sha256']),'dqi_source_pins':len(dqi_pins),'errors':errors,'performance_source_gate':'OPEN_I01','alternative_source_chain':'EXACT_OUTPUTS_AND_FULL_NATIVE_RECEIPTS'}
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
