# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | Francisco Angulo de Lafuente | 2026-11-13
# https://orcid.org/0009-0001-1634-7063
"""Construct the complete credited 46Q/883Q/deep512 source candidate."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE_MANIFEST_SHA='61bf36bfabc8c3c47840553709f9f8637d583016e97b93eb8f43bafcfbce0249'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_snapshot(source):
    manifest=source/'STAGED_SOURCE_MANIFEST.json'
    if sha(manifest)!=SOURCE_MANIFEST_SHA: raise RuntimeError('Staged manifest root identity mismatch')
    pins=json.loads(manifest.read_text())
    if len(pins)!=123: raise RuntimeError('Expected123 authenticated staged inputs')
    for name,digest in pins.items():
        path=(source/name).resolve()
        if not path.is_relative_to(source) or sha(path)!=digest: raise RuntimeError('Staged source identity mismatch: '+name)
    return pins
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['output','work','data','runtime']:ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--source',type=Path,default=HERE/'portfolio-source')
    a=ap.parse_args();out=a.output.resolve();work=a.work.resolve();source=a.source.resolve()
    if out.exists() or work.exists(): raise FileExistsError('Preserve builds: output and work must be fresh')
    pins=validate_snapshot(source)
    work.mkdir(parents=True);out.mkdir(parents=True)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    def run(argv,log):
        with (work/log).open('w') as f:subprocess.run([sys.executable,'-B',*map(str,argv)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=1200)
    run([HERE/'compact_invsqrt.py','--engine',a.runtime.resolve(),'--verifiers',a.data.resolve()/'verifiers','--out',work/'inverse','--work',work/'inverse-work','--build-only'],'inverse.log')
    run([source/'tools/build_dqi_policy.py',work/'dqi','--runtime',a.runtime.resolve()],'dqi.log')
    shutil.copy2(work/'inverse/invsqrt.kmb',out/'invsqrt.kmb');shutil.copy2(work/'dqi/dqi.kmb',out/'dqi.kmb')
    run([source/'tools/build_chemistry.py',out/'dfthcsos','--data',a.data.resolve(),'--runtime',a.runtime.resolve(),'--recipe',source/'recipes/h14-deep512'],'chemistry.log')
    (out/'dfthcsos-reconstruction.json').rename(work/'chemistry-build.json')
    hashes={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
    if len(hashes)!=18: raise RuntimeError('Expected exactly18 circuit/dataoutputs')
    legacy=json.loads((source/'recipes/h14-deep512/manifest.json').read_text())['expected_files']
    expected={'invsqrt.kmb':'321aff83636214196daa9cbc9dcc9c5e12a155bcff8d9989e98b8cee40935177','dqi.kmb':'0b634cca809c90493b67ac8104c9a307c99556d9edae74e26b460f4283aececd',**{'dfthcsos/'+k:v for k,v in legacy.items()}}
    if hashes!=expected: raise RuntimeError('Complete portfolio identity mismatch')
    report={'status':'18_SOURCE_BUILT_OUTPUTS_FULL_RECEIPT_BINDING_REQUIRED','invsqrt_author':'Syed Asad Ali, Apache-2.0','integration_author':'Francisco Angulo de Lafuente','dqi_attribution':'SomeJoint architecture; Atakan retiming; existing project883policy','chemistry_recipe':'h14-deep512, originalprojectoptimization on credited publicrecipe','outputs':hashes,'historical_exact_I01':'OPEN','submission':'NONE','source_manifest_sha256':sha(source/'STAGED_SOURCE_MANIFEST.json')}
    (work/'portfolio-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__': main()
