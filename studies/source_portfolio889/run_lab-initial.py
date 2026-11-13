# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Two source reconstructions and four predeclared full official DQI salts."""
import hashlib,json,os,subprocess,sys,time,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=Path('/mnt/datos/proyectos/qvc-i01-dqi889-20261113')
ENGINE=Path('/home/ai/pc/d/PROJECTS/.cognition/qvc-proyecto/invsqrt-dqi/srv')
VER=Path('/home/ai/pc/d/PROJECTS/.cognition/qvc-proyecto/auditoria-codex-20261110/servidor-src/data/verifiers')
ARCHIVE_SHA='49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763'
OUTPUT_SHA='7cbe8ecf6f6e9743529b574f019504bb1712ce06fbb570c719ce9d9e2c914cd9'
VER_SHA='f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def main():
    started=time.time();BASE.mkdir(parents=True,exist_ok=False)
    require(sha(ROOT/'dqi_source_zip')==ARCHIVE_SHA,'Source archive mismatch')
    require(sha(ENGINE/'kickmix.so')=='c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e','Engine mismatch')
    require(sha(VER/'dqi/verify_submission_dqi.py')==VER_SHA,'Verifier mismatch')
    with zipfile.ZipFile(ROOT/'dqi_source_zip') as z:
        for item in z.infolist():
            require((BASE/item.filename).resolve().is_relative_to(BASE),'Unsafe archive path')
            require((item.external_attr>>16)&0o170000!=0o120000,'Archive symlink')
        z.extractall(BASE)
    source=BASE/'dqi_source';pins=[]
    for line in (source/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split(maxsplit=1);p=(source/name.lstrip('*')).resolve()
        require(p.is_relative_to(source) and sha(p)==digest,'Source pin mismatch: '+name);pins.append(name)
    report={'status':'RUNNING_NOT_QUALIFIED','archive_sha256':ARCHIVE_SHA,'source_pins_checked':len(pins),'runner_sha256':sha(__file__),'shim_sha256':sha(ROOT/'auditshim/sitecustomize.py'),'engine_sha256':sha(ENGINE/'kickmix.so'),'verifier_sha256':VER_SHA,'builds':[],'official_runs':[],'historical_exact_e9':'OPEN'}
    def save():
        (BASE/'lab-report.json').write_text(json.dumps(report,indent=2));(ROOT/'lab-status.json').write_text(json.dumps(report,indent=2))
    save()
    for name in ['a','b']:
        work=BASE/('work-'+name);out=BASE/('out-'+name);work.mkdir();nonce=uuid.uuid4().hex;log=BASE/('audit-'+name+'.jsonl')
        env=dict(os.environ,PY=sys.executable,WORK=str(work),KEEP_WORK='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'auditshim'),DQI_AUDIT_LOG=str(log),DQI_AUDIT_NONCE=nonce,DQI_OUTPUT_ROOT=str(work),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1')
        test=subprocess.run([sys.executable,'-B','-c',"import os,sys;assert getattr(sys,'_qvc_dqi_audit',None)==os.environ['DQI_AUDIT_NONCE']"],env=env,capture_output=True,timeout=20)
        require(test.returncode==0,'Audit hook preflight failed')
        start=time.time()
        with (BASE/('build-'+name+'.log')).open('w') as f:p=subprocess.run(['timeout','900','bash',str(source/'build.sh'),str(ENGINE),str(VER),str(out)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=960)
        require(p.returncode==0,'Source build failed: '+name)
        require(sha(out/'dqi.kmb')==OUTPUT_SHA,'Source output mismatch: '+name)
        events=[json.loads(s) for s in log.read_text().splitlines()]
        begins=[x for x in events if x.get('event')=='audit-start' and any(str(a).endswith('build_v7.py') for a in x['argv'])]
        require(len(begins)==1 and begins[0]['nonce']==nonce,'Generator audit start missing')
        ends=[x for x in events if x.get('event')=='audit-end' and x['pid']==begins[0]['pid'] and x['nonce']==nonce]
        require(len(ends)==1,'Generator audit end missing')
        report['builds'].append({'name':name,'sha256':OUTPUT_SHA,'bytes':(out/'dqi.kmb').stat().st_size,'seconds':time.time()-start,'nonce':nonce,'generator_pid':begins[0]['pid'],'audit_sha256':sha(log),'returncode':p.returncode});save()
    env=dict(os.environ,PYTHONPATH=str(ENGINE),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1')
    for name,salt in [('default',''),('a','qvc-syed889-20261113-a'),('b','qvc-syed889-20261113-b'),('c','qvc-syed889-20261113-c')]:
        circuit=BASE/'out-a/dqi.kmb';cmd=[sys.executable,'-B',str(VER/'dqi/verify_submission_dqi.py'),str(circuit),'--max-workers','1']
        if salt:cmd+=['--salt',salt]
        start=time.time();dest=BASE/('official-'+name+'.json')
        with dest.open('w') as f,(BASE/('official-'+name+'.stderr')).open('w') as err:p=subprocess.run(cmd,env=env,stdout=f,stderr=err,timeout=1200)
        record={'name':name,'salt':salt,'command':cmd,'returncode':p.returncode,'seconds':time.time()-start,'receipt_sha256':sha(dest),'circuit_sha256':sha(circuit),'verifier_sha256':VER_SHA}
        report['official_runs'].append(record);save()
        require(p.returncode==0,'Official verifier process failed')
        result=json.loads(dest.read_text());require(result.get('status')=='PASS' and result.get('circuit_sha256')==OUTPUT_SHA and result.get('verified_shots')==102400 and result.get('num_qubits')==889,'Full official receipt binding failed')
    report.update(status='PASS_TWO_SOURCE_BUILDS_FOUR_FULL_OFFICIAL_SALTS',seconds=time.time()-started);save();print(json.dumps(report,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as error:
        (ROOT/'lab-failure.json').write_text(json.dumps({'status':'NOT_QUALIFIED','error_type':type(error).__name__,'reason':str(error)}));raise
