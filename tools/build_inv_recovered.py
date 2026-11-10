# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Exactly rebuild the88Q recovered-coefficient study; not the original62Q file."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,time

EXPECTED='29480dd3285825e2718bca69843803d57337e7ac7626a1adf043be5801a8a7ca'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];source=root/'vendor/invsqrt_source';numeric=root/'studies/recovered_invsqrt';out=a.output.resolve();out.mkdir(exist_ok=False,parents=True)
    os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');sys.dont_write_bytecode=True
    sys.path[:0]=[str(a.runtime.resolve()),str(source)];import kickmix as km
    native=Path(km.__file__).resolve();assert native.is_relative_to(a.runtime.resolve())
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(args[0])).resolve()
            if path.suffix.lower() in ('.kmb','.kmx') and not path.is_relative_to(out):raise RuntimeError('External compiled input forbidden')
    sys.addaudithook(audit)
    import round10_inv as gen
    gen.setup(a.data.resolve());sys.path.insert(0,str(a.runtime.resolve()))
    import round10_lookup as unary
    from round11_lookup import lookup
    unary.lookup=lookup
    recipe=json.loads((numeric/'numeric-recipe.json').read_text())['recipe'];start=time.perf_counter()
    model=gen.build_model(out/'model',fit_file=numeric/'phase-fit.json',recipe=recipe)
    options=json.loads((source/'selected_invsqrt.json').read_text())['options']
    circuit,probe=gen.build_variant(out/'build',model,**options);del circuit
    target=gen.optimize(out/'build');dest=out/'invsqrt.kmb';shutil.copy2(target,dest);assert sha(dest)==EXPECTED
    c=km.Circuit.from_file(str(dest),format='kmb')
    modules={str(Path(m.__file__).resolve().relative_to(source)):sha(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(source)}
    report={'status':'EXACT_RECOVERED256_STUDY_SOURCE_REBUILT','sha256':sha(dest),'qubits':c.num_qubits,'static_toffoli':c.operation_statistics().num_toffoli_like,'ops':len(c),'seconds':time.perf_counter()-start,'numeric_recipe_sha256':sha(numeric/'numeric-recipe.json'),'frozen_phase_fit_sha256':sha(numeric/'phase-fit.json'),'source_sha256':modules,'constructor_sha256':sha(Path(__file__)),'native_module_sha256':sha(native),'probe':probe,'scope':'Source construction from recovered coefficients and newly fitted global phase weights; full native receipt separate; distinct from original26eb62Q and selectedc3 study'}
    (out/'source-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','probe')}),flush=True)

if __name__=='__main__':main()
