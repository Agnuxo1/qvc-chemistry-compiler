# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | https://orcid.org/0009-0001-1634-7063 | 2026-11-13
"""Qualify every observed salt and bind the complete18-file source candidate."""
import argparse,itertools,json,subprocess,sys
from pathlib import Path
from construct_complete import sha,require
DQI='7cbe8ecf6f6e9743529b574f019504bb1712ce06fbb570c719ce9d9e2c914cd9'
VER='f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65'
def validate_dqi(root,digest):
    require(sha(root/'lab-report.json')==digest,'DQI execution report root mismatch')
    report=json.loads((root/'lab-report.json').read_text())
    require(report['status']=='PASS_TWO_SOURCE_BUILDS_FOUR_FULL_OFFICIAL_SALTS','Four completed official salts required')
    require(report['archive_sha256']=='49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763' and report['source_pins_checked']==430,'DQI source identity mismatch')
    require(report['verifier_sha256']==VER and report['engine_sha256']=='c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e','DQI host mismatch')
    require([r['name'] for r in report['builds']]==['a','b'],'Two source builds required')
    for build in report['builds']:
        name=build['name'];require(sha(root/('out-'+name)/'dqi.kmb')==build['sha256']==DQI,'Source-built DQI mismatch')
        require(build['source_guard_returncode']==0 and build['bytes']==455590024,'Source build completion mismatch')
        audit=root/('audit-'+name+'.jsonl');require(sha(audit)==build['audit_sha256'],'Audit log mismatch')
        rows=[json.loads(s) for s in audit.read_text().splitlines()]
        start=[x for x in rows if x.get('event')=='audit-start' and x['argv'] and str(x['argv'][0]).endswith('build_v7.py')]
        end=[x for x in rows if x.get('event')=='audit-end' and x['pid']==build['generator_pid'] and x['nonce']==build['nonce']]
        require(len(start)==len(end)==1 and start[0]['pid']==build['generator_pid'] and start[0]['nonce']==build['nonce'],'Generator audit binding mismatch')
    runs=report['official_runs'];expected=[('default',''),('a','qvc-syed889-20261113-a'),('b','qvc-syed889-20261113-b'),('c','qvc-syed889-20261113-c')]
    require([(r['name'],r['salt']) for r in runs]==expected,'DQI salt names/order mismatch')
    receipts={}
    for run in runs:
        path=root/('official-'+run['name']+'.json');cmd=run['command']
        require(run['returncode']==0 and sha(path)==run['receipt_sha256'],'Native DQI receipt digest mismatch')
        require(run['circuit_sha256']==DQI and run['verifier_sha256']==VER,'Native DQI identity mismatch')
        require(len(cmd) in (6,8) and cmd[1]=='-B' and cmd[4:] == ['--max-workers','1']+(['--salt',run['salt']] if run['salt'] else []),'DQI command/salt mismatch')
        require(sha(cmd[2])==VER and Path(cmd[3]).resolve()==(root/'out-a/dqi.kmb').resolve(),'DQI command paths mismatch')
        receipt=json.loads(path.read_text());require(receipt['status']=='PASS' and receipt['verified_shots']==102400 and receipt['num_qubits']==889 and receipt['circuit_sha256']==DQI,'Full DQI receipt mismatch')
        receipts[run['name']]=receipt
    return receipts
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['candidate','work','dqi-lab','inverse-root','metric','runtime','output']:ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--dqi-report-sha',required=True);ap.add_argument('--inverse-report-sha',required=True);a=ap.parse_args()
    dqi=validate_dqi(a.dqi_lab.resolve(),a.dqi_report_sha)
    inverse_source=a.work/'inverse-source';sys.path.insert(0,str(inverse_source))
    from finalize_candidate import validate_run_binding
    inv=validate_run_binding(a.inverse_root.resolve(),a.inverse_report_sha)
    require(sha(a.metric)=='62005ff476af2b22a57747882e9e53895ee2166bda417ede0d24fbfc29646cbf','Metric identity mismatch')
    build=json.loads((a.work/'portfolio-build.json').read_text());require(build['status']=='18_SOURCE_BUILT_OUTPUTS_FULL_QUALIFICATION_PENDING','Complete source build required')
    actual={p.relative_to(a.candidate).as_posix():sha(p) for p in a.candidate.rglob('*') if p.is_file()};require(actual==build['outputs'] and len(actual)==18,'Whole source-output binding mismatch')
    require(actual['dqi.kmb']==DQI and actual['invsqrt.kmb']=='321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177','Candidate inverse/DQI identity mismatch')
    receipt_dir=a.output.parent/(a.output.name+'-receipts');receipt_dir.mkdir(exist_ok=False)
    salt_maps={'invsqrt':{r['name']:r['salt'] for r in json.loads((a.inverse_root/'integration-report.json').read_text())['official_runs']},'dqi':{r['name']:r['salt'] for r in json.loads((a.dqi_lab/'lab-report.json').read_text())['official_runs']}}
    for kind,data in [('invsqrt',inv),('dqi',dqi)]:
        for name,r in data.items():(receipt_dir/(kind+'-'+name+'.json')).write_text(json.dumps({'task':kind,'scope':'Full unmodified local stock check, not Kaggle','run_name':name,'salt':salt_maps[kind][name],'input_sha256':{kind+'.kmb':r['circuit_sha256']},'official_result':r},indent=2))
    evidence=inverse_source/'portfolio-source/evidence/official'
    cmd=[sys.executable,'-B',str(inverse_source/'portfolio-source/tools/package_portfolio.py'),str(a.candidate),str(a.output),'--invsqrt',str(receipt_dir/'invsqrt-default.json'),'--dqi-a',str(receipt_dir/'dqi-default.json'),'--dqi-b',str(receipt_dir/'dqi-a.json'),'--chem-a',str(evidence/'chemistry-h14-deep512-a.json'),'--chem-b',str(evidence/'chemistry-h14-deep512-b.json'),'--metric',str(a.metric),'--runtime',str(a.runtime)]
    subprocess.run(cmd,check=True,timeout=900)
    costs={n:json.loads((evidence/('chemistry-h14-deep512-'+n+'.json')).read_text())['official_result']['score'] for n in ['a','b']}
    indices={i+'-'+d+'-'+c:(2076774.233715282/inv[i]['score']*24439463583672.93/dqi[d]['score']*3355599588.3155365/costs[c])**(1/3) for i,d,c in itertools.product(inv,dqi,costs)}
    package=json.loads((a.output/'manifest.json').read_text())
    record={'status':'PASS_FULL_SOURCE_46_889_DEEP512_LOCAL_CANDIDATE','source_outputs':18,'stock_circuit_readers':len(package['official_readers']),'dqi_salts':4,'dqi_total_shots':409600,'dqi_value_errors':{n:r['value_errors'] for n,r in dqi.items()},'dqi_phase_errors':{n:r['phase_errors'] for n,r in dqi.items()},'local_composite_indices':indices,'observed_composite_range':[min(indices.values()),max(indices.values())],'range_scope':'All16 combinations of fixed measured salts, not confidence bounds or official scores','archive_sha256':package['archive_sha256'],'archive_bytes':package['archive_bytes'],'dqi_report_sha256':a.dqi_report_sha,'inverse_report_sha256':a.inverse_report_sha,'constructor_sha256':build['constructor_sha256'],'qualifier_sha256':sha(__file__),'historical_exact_I01':'OPEN','promotion':'NONE','submission':'NONE'}
    (a.output/'readiness.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
