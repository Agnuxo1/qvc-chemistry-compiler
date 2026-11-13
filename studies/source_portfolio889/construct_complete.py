# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | https://orcid.org/0009-0001-1634-7063 | 2026-11-13
"""Construct the separately identified46Q/889Q/deep512 portfolio from sources."""
import argparse,hashlib,json,os,shutil,subprocess,sys,uuid,zipfile
from pathlib import Path
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def unpack(archive,digest,target):
    require(sha(archive)==digest,'Source archive mismatch')
    target.mkdir()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            require((target/item.filename).resolve().is_relative_to(target),'Unsafe source archive path')
            require((item.external_attr>>16)&0o170000!=0o120000,'Source symlink rejected')
        z.extractall(target)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['inverse-bundle','dqi-archive','data','runtime','output','work']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();work=a.work.resolve();out=a.output.resolve()
    require(not out.exists() and not work.exists(),'Use fresh output and work directories')
    work.mkdir(parents=True);out.mkdir(parents=True)
    unpack(a.inverse_bundle,'0ddbc852ddf36233248da558d1a99b308f1b630ddce5fe210926cde405b2e852',work/'inverse-source')
    unpack(a.dqi_archive,'49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763',work/'dqi-source')
    inv=work/'inverse-source';dqi=work/'dqi-source/dqi_source'
    sys.path.insert(0,str(inv));from complete_portfolio import validate_snapshot
    validate_snapshot(inv/'portfolio-source')
    for line in (dqi/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split(maxsplit=1);p=(dqi/name.lstrip('*')).resolve()
        require(p.is_relative_to(dqi) and sha(p)==digest,'DQI source pin mismatch')
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    def run(cmd,label,env_override=None):
        with (work/(label+'.log')).open('w') as log:subprocess.run(list(map(str,cmd)),env=env_override or env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1000)
    run([sys.executable,'-B',inv/'compact_invsqrt.py','--engine',a.runtime.resolve(),'--verifiers',a.data.resolve()/'verifiers','--out',work/'inverse-out','--work',work/'inverse-work','--build-only'],'inverse')
    shutil.copy2(work/'inverse-out/invsqrt.kmb',out/'invsqrt.kmb')
    shim=Path(__file__).with_name('auditshim');require(sha(shim/'sitecustomize.py')=='e93b17929601d081608901e04d1d7e68ea21d604d151520535c30b9189da4abb','DQI audit shim mismatch')
    nonce=uuid.uuid4().hex
    dqi_env=dict(env,PY=sys.executable,KEEP_WORK='1',WORK=str(work/'dqi-work'),PYTHONPATH=str(shim),DQI_AUDIT_LOG=str(work/'dqi-audit.jsonl'),DQI_AUDIT_NONCE=nonce,DQI_OUTPUT_ROOT=str(work/'dqi-work'))
    run([sys.executable,'-B','-c',"import os,sys;assert getattr(sys,'_qvc_dqi_audit',None)==os.environ['DQI_AUDIT_NONCE']"],'audit-preflight',dqi_env)
    run(['timeout','900','bash',dqi/'build.sh',a.runtime.resolve(),a.data.resolve()/'verifiers',work/'dqi-out'],'dqi',dqi_env)
    events=[json.loads(s) for s in (work/'dqi-audit.jsonl').read_text().splitlines()]
    starts=[r for r in events if r.get('event')=='audit-start' and r['argv'] and str(r['argv'][0]).endswith('build_v7.py') and r['nonce']==nonce]
    require(len(starts)==1,'DQI generator audit start required')
    require(len([r for r in events if r.get('event')=='audit-end' and r['pid']==starts[0]['pid'] and r['nonce']==nonce])==1,'DQI audit close required')
    shutil.copy2(work/'dqi-out/dqi.kmb',out/'dqi.kmb')
    source=inv/'portfolio-source';recipe=source/'recipes/h14-deep512'
    run([sys.executable,'-B',source/'tools/build_chemistry.py',out/'dfthcsos','--data',a.data.resolve(),'--runtime',a.runtime.resolve(),'--recipe',recipe],'chemistry')
    (out/'dfthcsos-reconstruction.json').rename(work/'chemistry-build.json')
    expected={'invsqrt.kmb':'321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177','dqi.kmb':'7cbe8ecf6f6e9743529b574f019504bb1712ce06fbb570c719ce9d9e2c914cd9',**{'dfthcsos/'+n:v for n,v in json.loads((recipe/'manifest.json').read_text())['expected_files'].items()}}
    actual={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
    require(actual==expected and len(actual)==18,'Complete output identity mismatch')
    report={'status':'18_SOURCE_BUILT_OUTPUTS_FULL_QUALIFICATION_PENDING','outputs':actual,'constructor_sha256':sha(__file__),'inverse_bundle_sha256':sha(a.inverse_bundle),'dqi_archive_sha256':sha(a.dqi_archive),'dqi_audit_sha256':sha(work/'dqi-audit.jsonl'),'historical_exact_I01':'OPEN','promotion':'NONE','submission':'NONE'}
    (work/'portfolio-build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
