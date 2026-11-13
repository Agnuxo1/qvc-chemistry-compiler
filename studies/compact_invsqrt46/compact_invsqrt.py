# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-13
# Author: Francisco Angulo de Lafuente | https://orcid.org/0009-0001-1634-7063
"""Authenticated integration of Syed Asad Ali's Apache-2.0 compact source.

This wrapper is original integration work. The quantum generator, synthesis
certificates and proofs are upstream work, with LICENSE/NOTICE preserved.
An exact historical 26ebf39/e9f54be reconstruction is a separate claim.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,time,uuid,zipfile
from pathlib import Path
ARCHIVE_SHA='7d9801ae20e942dba2211a656bba6014a0a16d57da534c0b60328d1c5d9d8254'
OUTPUT_SHA='321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177'
ENGINE_SHA='c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e'
VERIFIER_SHA='ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a'
PASS='PASS_EXACT_NATIVE_TEXT_ALL_REQUESTED_INPUTS_ALL_HMR_TRANSCRIPTS'
AUDIT_SHIM_SHA='19d5e8b6f42099797cfd1ae45110fc1ae4f25f53997bfeedb709423ecf6cfc61'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(condition,message):
    if not condition: raise RuntimeError(message)
def validate_native_receipt(receipt):
    require(receipt.get('status')=='PASS','Official verification failed')
    require(receipt.get('circuit_sha256')==OUTPUT_SHA,'Official receipt belongs to a different circuit')
    require(receipt.get('verified_shots')==200540928,'Full official shot coverage required')
    require(receipt.get('num_qubits')==46,'Official width mismatch')
def audit_preflight(env):
    code="import os,sys;assert getattr(sys,'_qvc_audit_active',None)==os.environ['QVC_AUDIT_NONCE'],'Audit hook not active'"
    p=subprocess.run([sys.executable,'-B','-c',code],env=env,capture_output=True,timeout=20)
    require(p.returncode==0,'Audit preflight rejected: hook not active')
def validate_audit_shim(shim):
    require((shim/'sitecustomize.py').is_file() and sha(shim/'sitecustomize.py')==AUDIT_SHIM_SHA,'Audit shim missing or identity mismatch')
def validate_audit_log(path,nonce):
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    starts=[r for r in rows if r.get('event')=='audit-start' and any(str(a).endswith('build_variant.py') for a in r['argv'])]
    require(len(starts)==1,'Exactly one audited generator process required')
    start=starts[0]
    require(start['enforced'] and start['nonce']==nonce,'Generator audit activation mismatch')
    ends=[r for r in rows if r.get('event')=='audit-end' and r['pid']==start['pid'] and r['nonce']==nonce and r['enforced']]
    require(len(ends)==1,'Generator audit closing receipt required')
    return {'generator_pid':start['pid'],'nonce':nonce,'starts':1,'ends':1,'log_sha256':sha(path)}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',type=Path,default=Path(__file__).with_name('invsqrt_source.zip'))
    ap.add_argument('--engine',type=Path,required=True)
    ap.add_argument('--verifiers',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--max-workers',type=int,default=2)
    ap.add_argument('--build-only',action='store_true',help='Skip official checks; result remains unqualified.')
    args=ap.parse_args();start=time.monotonic()
    require(sys.version_info[:2]==(3,13),'CPython 3.13 required by the pinned host runtime')
    require(sys.platform=='linux','This reproducible build entry point requires Linux x86_64')
    require(sha(args.archive)==ARCHIVE_SHA,'Source archive identity mismatch')
    engine=args.engine.resolve();verifiers=args.verifiers.resolve()
    verifier=verifiers/'invsqrt/verify_submission_invsqrt.py'
    require(sha(engine/'kickmix.so')==ENGINE_SHA,'Native runtime identity mismatch')
    require(sha(verifier)==VERIFIER_SHA,'Official verifier identity mismatch')
    require(args.max_workers>0,'Positive worker count required')
    out=args.out.resolve();require(not out.exists(),'Output must be a fresh directory')
    args.work.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='compact46-',dir=args.work.resolve()))
    require(not any(c.isspace() or c=='@' for c in str(work)),'Work path must not contain whitespace or @')
    with zipfile.ZipFile(args.archive) as z:
        for item in z.infolist():
            require((work/item.filename).resolve().is_relative_to(work),'Unsafe archive path')
            require((item.external_attr>>16)&0o170000!=0o120000,'Archive symlink rejected')
        z.extractall(work)
    source=work/'invsqrt_source';pins=[]
    for line in (source/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split(maxsplit=1);path=(source/name.lstrip('*')).resolve()
        require(path.is_relative_to(source),'Unsafe manifest path')
        require(sha(path)==digest,'Source pin mismatch: '+name);pins.append(name)
    shim=Path(__file__).with_name('auditshim')
    validate_audit_shim(shim)
    nonce=uuid.uuid4().hex
    env=dict(os.environ,PY=sys.executable,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',WORK=str(work),PYTHONPATH=str(shim),QVC_AUDIT_LOG=str(work/'binary-reads.jsonl'),QVC_ENFORCE='1',QVC_AUDIT_NONCE=nonce)
    audit_preflight(env)
    out.mkdir(parents=True)
    report={'status':'BUILD_STARTED_NOT_QUALIFIED','upstream_author':'Syed Asad Ali','upstream_license':'Apache-2.0','integration_author':'Francisco Angulo de Lafuente','orcid':'https://orcid.org/0009-0001-1634-7063','source_archive_sha256':ARCHIVE_SHA,'source_pins_checked':len(pins),'engine_sha256':ENGINE_SHA,'verifier_sha256':VERIFIER_SHA,'work':str(work),'official_runs':[],'historical_exact_I01':'OPEN'}
    def save(): (out/'integration-report.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    with (out/'build.log').open('w') as log:
        result=subprocess.run(['bash',str(source/'build.sh'),str(engine),str(verifiers),str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    require(result.returncode==0,'Source build failed; inspect build.log')
    report['audit']=validate_audit_log(work/'binary-reads.jsonl',nonce)
    require(sha(out/'invsqrt.kmb')==OUTPUT_SHA,'Generated output identity mismatch')
    candidates=list(work.glob('invsqrt_build.*/tree/final/s15k7a.proof.json'))
    require(len(candidates)==1,'Unique exact proof required')
    proof=json.loads(candidates[0].read_text())
    require(proof['status']==PASS and proof['circuit_sha256']==OUTPUT_SHA and proof['proved_inputs']==3133452,'Exact proof identity or coverage mismatch')
    shutil.copy2(candidates[0],out/'exact-proof.json')
    shutil.copy2(candidates[0].with_name('s15k7a.build.json'),out/'resource-model.json')
    report.update(status='SOURCE_BUILT_EXACT_PROOF_OFFICIAL_CHECKS_PENDING',output_sha256=OUTPUT_SHA)
    save()
    if not args.build_only:
        env['PYTHONPATH']=str(engine)
        for name,salt in [('default',''),('independent','qvc-i01-source46-20261113-independent')]:
            cmd=[sys.executable,'-B',str(verifier),str(out/'invsqrt.kmb'),'--max-workers',str(args.max_workers)]
            if salt: cmd+=['--salt',salt]
            began=time.monotonic()
            with (out/('official-'+name+'.json')).open('w') as log,(out/('official-'+name+'.stderr')).open('w') as err:
                completed=subprocess.run(cmd,env=env,stdout=log,stderr=err,timeout=3600)
            receipt=json.loads((out/('official-'+name+'.json')).read_text())
            require(completed.returncode==0,'Official verifier process failed')
            validate_native_receipt(receipt)
            report['official_runs'].append({'name':name,'salt':salt,'command':cmd,'seconds':time.monotonic()-began,'returncode':completed.returncode,'receipt_sha256':sha(out/('official-'+name+'.json'))});save()
        report['status']='PASS_SOURCE_BUILT_EXACT_PROOF_TWO_FULL_OFFICIAL_SALTS'
    report['seconds']=time.monotonic()-start;save()
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
