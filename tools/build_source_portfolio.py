# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Build a source-backed alternative with 18 exact circuit/data outputs."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--data',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--recipe',type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.output.resolve();work=out.parent/(out.name+'-build-work')
    if out.exists() or work.exists():raise FileExistsError('Preserve prior builds; choose a fresh output name')
    work.mkdir(parents=True);out.mkdir()
    common=['--data',str(a.data.resolve()),'--runtime',str(a.runtime.resolve())]
    subprocess.run([sys.executable,str(root/'tools/build_inv_source.py'),str(work/'invsqrt'),*common],check=True)
    subprocess.run([sys.executable,str(root/'tools/build_dqi_source.py'),str(work/'dqi'),'--runtime',str(a.runtime.resolve())],check=True)
    shutil.copy2(work/'invsqrt/invsqrt.kmb',out/'invsqrt.kmb');shutil.copy2(work/'dqi/dqi.kmb',out/'dqi.kmb')
    recipe=(a.recipe or root/'recipes/s37').resolve()
    subprocess.run([sys.executable,str(root/'tools/build_chemistry.py'),str(out/'dfthcsos'),*common,'--recipe',str(recipe)],check=True)
    (out/'dfthcsos-reconstruction.json').rename(work/'chemistry-reconstruction.json')
    hashes={}
    for path in out.rglob('*'):
        if path.is_file():
            with path.open('rb') as f:hashes[path.relative_to(out).as_posix()]=hashlib.file_digest(f,'sha256').hexdigest()
    assert len(hashes)==18
    report={'status':'18_SOURCE_BUILT_OUTPUTS','scope':'Credited source-backed alternative, not the 26ebf39/e9f54be3 binary performance portfolio','constructor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'outputs':hashes,'native_full_checks':'See bound evidence; generation alone is not a verifier PASS'}
    (work/'portfolio-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
