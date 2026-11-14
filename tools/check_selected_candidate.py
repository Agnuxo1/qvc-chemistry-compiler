# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-14 | https://orcid.org/0009-0001-1634-7063
"""Verify selection, exact source identities and all measured cost combinations."""
import hashlib,itertools,json,math
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,selection=None):
    root=Path(root).resolve()
    def read(name):
        p=(root/name).resolve();assert p.is_relative_to(root),name
        return json.loads(p.read_text(encoding='utf-8'))
    s=selection if selection is not None else read('SELECTED_CANDIDATE.json')
    assert s['version']=='0.4.0'
    assert s['source_gate']['id']=='I01' and s['source_gate']['status']=='CLOSED'
    assert s['historical_recovery']['id']=='I01-HIST' and s['historical_recovery']['status']=='OPEN'
    assert s['original_performance_I01']=='OPEN'
    if s['kaggle_submission']!='NONE':
        assert s['kaggle_submission'] in ['SUBMITTED','COMPLETE','ERROR']
        record=read(s['submission_evidence'])
        assert sha(root/s['submission_evidence'])==s['submission_evidence_sha256']
        assert record['archive_sha256']==s['archive_sha256'] and record['archive_bytes']==s['archive_bytes']
        assert type(record['submission']['ref']) is int and record['submission']['ref']==58344264 and record['submission']['account']=='franciscoangulo'
        assert record['submission']['file_name']=='submission.zip' and record['submission']['platform_bytes']==s['archive_bytes']
        assert record['repository_submission_state']==s['kaggle_submission']
        if s['kaggle_submission']=='COMPLETE':
            assert record['submission']['api_status']=='COMPLETE'
            assert type(record['submission']['public_score']) in [int,float] and math.isfinite(record['submission']['public_score']) and record['submission']['public_score']>=0
            assert float(record['submission']['public_score_text'])==record['submission']['public_score']
        elif s['kaggle_submission']=='SUBMITTED':
            assert record['submission']['api_status'] in [None,'PENDING','RUNNING','SUBMITTED','QUEUED']
            assert record['submission']['public_score'] is None
            assert record['submission']['public_score_text'] is None
        else:
            assert record['submission']['api_status'] in ['ERROR','FAILED','INVALID','CANCELLED']
            assert record['submission']['public_score'] is None
            assert record['submission']['public_score_text'] is None
    assert s['historical_recovery']['invsqrt_sha256']=='26ebf39df3b13e5fd2d923d1b9988043b107b64f6e21efc5cc9bc76f5d56adec'
    assert s['historical_recovery']['dqi_sha256']=='e9f54be304cbdcda7306729c335b1a2314a45d0ca818e05cf60e45ddee969bc4'
    for name,digest in s['evidence_sha256'].items():assert sha(root/name)==digest,name
    build=read(s['source_build_evidence']);pkg=read(s['package_evidence']);ready=read(s['readiness_evidence'])
    assert pkg['status']=='PASS' and len(pkg['members'])==18
    assert build['constructor_sha256']==sha(root/s['generator'])==ready['constructor_sha256']
    assert ready['qualifier_sha256']==sha(root/'studies/source_portfolio889/qualify_complete.py')
    assert build['outputs']=={n:v['sha256'] for n,v in pkg['members'].items()}
    assert s['archive_sha256']==pkg['archive_sha256']==ready['archive_sha256']=='0059f20ad2b9822318c208d28093714ca0e9440271262387c5b1df0109d3b30e'
    assert s['archive_bytes']==pkg['archive_bytes']==ready['archive_bytes']==49338223
    for name,key in [('invsqrt.kmb','invsqrt_sha256'),('dqi.kmb','dqi_sha256'),('dfthcsos/submission.npz','chemistry_npz_sha256')]:assert build['outputs'][name]==s[key]
    assert build['inverse_bundle_sha256']==sha(root/'studies/source_portfolio889/upstream/inverse46-source.zip')
    assert build['dqi_archive_sha256']==sha(root/'studies/source_portfolio889/upstream/dqi_source.zip')
    readers=pkg['official_readers'];assert len(readers)==17 and all(x['status']=='PASS' for x in readers)
    assert {x['file'] for x in readers}==set(pkg['members'])-{'dfthcsos/submission.npz'}
    assert next(x for x in readers if x['file']=='invsqrt.kmb')['qubits']==46
    assert next(x for x in readers if x['file']=='dqi.kmb')['qubits']==889
    for key,path in s['receipt_files'].items():assert sha(root/path)==pkg['receipt_sha256'][key]
    full={k:read(p) for k,p in s['full_receipt_files'].items()}
    inv={n:full['invsqrt_'+n]['official_result'] for n in ['default','independent']}
    dqi={n:full['dqi_'+n]['official_result'] for n in ['default','a','b','c']}
    chem={n:full['chem_'+n]['official_result'] for n in ['a','b']}
    for kind,rows,shots,qubits in [('invsqrt',inv,200540928,46),('dqi',dqi,102400,889),('chem',chem,78080,427)]:
        salts=[]
        for name,result in rows.items():
            receipt=full[kind+'_'+name];assert result['status']=='PASS' and result['verified_shots']==shots and result['num_qubits']==qubits
            salts.append(receipt['salt'])
            for file,digest in receipt['input_sha256'].items():
                member='dfthcsos/'+file if kind=='chem' else file
                assert pkg['members'][member]['sha256']==digest
        assert len(salts)==len(set(salts))
    report=read('studies/source_portfolio889/lab-report.json')
    assert sha(root/'studies/source_portfolio889/lab-report.json')==ready['dqi_report_sha256']
    for run in report['official_runs']:
        n=run['name'];path='studies/source_portfolio889/official-'+n+'.json'
        assert sha(root/path)==run['receipt_sha256'] and read(path)==dqi[n]
        assert full['dqi_'+n]['salt']==run['salt']
    assert {n:r['value_errors'] for n,r in dqi.items()}==ready['dqi_value_errors']=={'default':0,'a':1,'b':0,'c':0}
    assert {n:r['phase_errors'] for n,r in dqi.items()}==ready['dqi_phase_errors']==dict.fromkeys(dqi,0)
    indices={i+'-'+d+'-'+c:(2076774.233715282/inv[i]['score']*24439463583672.93/dqi[d]['score']*3355599588.3155365/chem[c]['score'])**(1/3) for i,d,c in itertools.product(inv,dqi,chem)}
    assert len(indices)==16 and set(indices)==set(ready['local_composite_indices'])==set(s['all_component_cost_combinations'])
    for name,value in indices.items():assert math.isclose(value,ready['local_composite_indices'][name],rel_tol=1e-14) and math.isclose(value,s['all_component_cost_combinations'][name],rel_tol=1e-14)
    assert s['local_composite_indices']==pkg['local_composite_indices']
    assert s['observed_composite_range']==ready['observed_composite_range']==[min(indices.values()),max(indices.values())]
    return {'status':'PASS','version':s['version'],'source_outputs':18,'cost_combinations':16,'source_gate':'CLOSED_SELECTED_I01','historical_gate':'OPEN_I01_HIST','kaggle_submission_state':s['kaggle_submission']}

if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parents[1]),indent=2))
