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
    recipe=ROOT/'recipes/s37';m=json.loads((recipe/'manifest.json').read_text())
    for key,name in (('table_sha256','table.npz'),('plan_sha256','plan.json')):
        if sha(recipe/name)!=m[key]:errors.append(f'Recipe drift: {name}')
    for name,value in m['source_sha256'].items():
        if sha(recipe/'src'/name)!=value:errors.append(f'Recipe source drift: {name}')
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
    report={'status':'PASS' if not errors else 'FAIL','python_sources':checked_py,'local_links':links,'files':len(files),'errors':errors,'performance_source_gate':'OPEN_I01'}
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
