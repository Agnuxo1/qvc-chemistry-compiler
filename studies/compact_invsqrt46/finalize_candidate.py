# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-13 | https://orcid.org/0009-0001-1634-7063
"""Bind full stock receipts to a source-generated18-file candidate and ZIP."""
import argparse,json,math,shutil,subprocess,sys
from pathlib import Path
from compact_invsqrt import validate_native_receipt,require,sha,OUTPUT_SHA,VERIFIER_SHA
from complete_portfolio import validate_snapshot
ROOT=Path(__file__).resolve().parent
def validate_run_binding(native_root,report_sha):
    report_path=native_root/'integration-report.json'
    require(sha(report_path)==report_sha,'Native execution report root mismatch')
    report=json.loads(report_path.read_text())
    require(report['status']=='PASS_SOURCE_BUILT_EXACT_PROOF_TWO_FULL_OFFICIAL_SALTS','Complete source/native run report required')
    runs=report['official_runs']
    require([(r['name'],r['salt']) for r in runs]==[('default',''),('independent','qvc-i01-source46-20261113-independent')],'Declared native names, order and salts required')
    require(report['output_sha256']==OUTPUT_SHA and report['verifier_sha256']==VERIFIER_SHA,'Native report identities mismatch')
    raw={}
    for run in runs:
        name=run['name'];path=native_root/('official-'+name+'.json');cmd=run['command']
        require(run['returncode']==0 and sha(path)==run['receipt_sha256'],'Receipt does not match its execution digest')
        require(len(cmd) in (6,8) and cmd[1]=='-B' and cmd[4]=='--max-workers','Native command structure mismatch')
        require(Path(cmd[2]).name=='verify_submission_invsqrt.py' and sha(cmd[2])==VERIFIER_SHA,'Native verifier command identity mismatch')
        require(Path(cmd[3]).resolve()==(native_root/'invsqrt.kmb').resolve() and sha(cmd[3])==OUTPUT_SHA,'Native command circuit mismatch')
        require((cmd[6:] if len(cmd)>6 else [])==(['--salt',run['salt']] if run['salt'] else []),'Native command salt mismatch')
        raw[name]=json.loads(path.read_text());validate_native_receipt(raw[name])
    require(runs[0]['receipt_sha256']!=runs[1]['receipt_sha256'],'Duplicate native receipts rejected')
    return raw
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['candidate','output','native-root','metric','runtime']:ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--source',type=Path,default=ROOT/'portfolio-source')
    ap.add_argument('--run-report-sha',required=True,help='Observed SHA256 of the completed execution report')
    a=ap.parse_args();validate_snapshot(a.source.resolve())
    require(sha(a.metric)=='62005ff476af2b22a57747882e9e53895ee2166bda417ede0d24fbfc29646cbf','Official metric source identity mismatch')
    raw=validate_run_binding(a.native_root.resolve(),a.run_report_sha)
    require(sha(a.candidate/'invsqrt.kmb')==OUTPUT_SHA,'Candidate inverse differs from verified output')
    receipt_dir=a.output.parent/(a.output.name+'-receipts');receipt_dir.mkdir(exist_ok=False,parents=True)
    for name,r in raw.items():
        wrapped={'task':'invsqrt','scope':'Full unmodified local native check, not Kaggle','status':'PASS','salt':'' if name=='default' else 'qvc-i01-source46-20261113-independent','input_sha256':{'invsqrt.kmb':OUTPUT_SHA},'official_result':r}
        (receipt_dir/('invsqrt-'+name+'.json')).write_text(json.dumps(wrapped,indent=2))
    evidence=a.source/'evidence/official'
    cmd=[sys.executable,'-B',str(a.source/'tools/package_portfolio.py'),str(a.candidate),str(a.output),'--invsqrt',str(receipt_dir/'invsqrt-default.json'),'--dqi-a',str(evidence/'dqi883-source-a.json'),'--dqi-b',str(evidence/'dqi883-source-b.json'),'--chem-a',str(evidence/'chemistry-h14-deep512-a.json'),'--chem-b',str(evidence/'chemistry-h14-deep512-b.json'),'--metric',str(a.metric),'--runtime',str(a.runtime)]
    subprocess.run(cmd,check=True,timeout=900)
    manifest=json.loads((a.output/'manifest.json').read_text())
    composite={}
    for inv_name,inv in raw.items():
        for pair in ['a','b']:
            dqi=json.loads((evidence/('dqi883-source-'+pair+'.json')).read_text())['official_result']['score']
            chem=json.loads((evidence/('chemistry-h14-deep512-'+pair+'.json')).read_text())['official_result']['score']
            composite[inv_name+'-'+pair]=(2076774.233715282/inv['score']*24439463583672.93/dqi*3355599588.3155365/chem)**(1/3)
    report={'status':'PASS_FULL_SOURCE_CANDIDATE_LOCALLY_VALIDATED','archive_sha256':manifest['archive_sha256'],'archive_bytes':manifest['archive_bytes'],'official_input_readers':len(manifest['official_readers']),'source_outputs':18,'inverse_full_shots_per_salt':200540928,'inverse_salts':2,'total_inverse_shots':401081856,'local_composite_indices':composite,'comparison_source_v03':21.498484409138246,'historical_exact_I01':'OPEN','submission':'NONE','publication':'NONE','scope':'Archived baselines and measured salts; not official score or confidence limits','native_execution_report_sha256':a.run_report_sha,'native_receipt_hashes':{name:sha(a.native_root/('official-'+name+'.json')) for name in raw}}
    (a.output/'readiness.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
