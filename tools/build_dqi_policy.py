# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Exactly construct the checked883Q source policy; no compiled circuit input."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys,time

EXPECTED='0b634cca809c90493b67ac8104c9a307c99556d9edae74e26b460f4283aececd'
PACKET_PIN='a6819e88d3dada84f158023c9ba22e7d2c06ee53ad9d0c691bdd2e701d88d8b8'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--runtime',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];packet=root/'vendor/dqi888/source-packet';source=packet/'blocks/dqi/team-1028-narrow240/source'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');sys.dont_write_bytecode=True
    assert sha(packet/'AUTHENTICATED_SOURCE_MANIFEST.json')==PACKET_PIN
    pins=json.loads((packet/'AUTHENTICATED_SOURCE_MANIFEST.json').read_text())
    assert all(sha(packet/name)==value for name,value in pins.items())
    sys.path[:0]=[str(a.runtime.resolve()),str(source/'playbook/kit/decoder'),str(source/'playbook/kit')]
    import kickmix as km
    native=Path(km.__file__).resolve();assert native.is_relative_to(a.runtime.resolve());sys.modules['circ']=km
    def audit(event,values):
        if event=='open' and isinstance(values[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(values[0])).resolve()
            if path.suffix.lower() in ('.kmb','.kmx') and not path.is_relative_to(out):raise RuntimeError('External compiled input forbidden')
    sys.addaudithook(audit)
    from final_decoder import decode as ref
    assert Path(ref.__file__).resolve().is_relative_to(source)
    policy=frozenset([14,15,16]);ref.EXTERNAL_HOMOGENEOUS=policy
    entry=source/'exp/r-main/narrow240/decode_retimed.py'
    spec=importlib.util.spec_from_file_location('source_policy_decoder',entry);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    assert module.ext_env['EXTERNAL_HOMOGENEOUS']==policy
    start=time.perf_counter();b=km.CircuitBuilder();syndromes=[b.alloc_qubits(12) for _ in range(70)];errors=[b.alloc_bits(12) for _ in range(4095)]
    module.decode(b,syndromes,errors)
    metadata=[]
    for i in range(70):
        metadata.append(f'REGISTER r{i} "S{i}"');metadata.extend(f'APPEND_TO_REGISTER q{12*i+k} r{i}' for k in range(12))
    for i in range(4095):
        metadata.append(f'REGISTER r{70+i} "E{i}"');metadata.extend(f'APPEND_TO_REGISTER b{12*i+k} r{70+i}' for k in range(12))
    c=km.Circuit('\n'.join(metadata))+b.finish_circuit();dest=out/'dqi.kmb';c.to_file(str(dest),format='kmb');digest=sha(dest);assert digest==EXPECTED
    modules={str(Path(m.__file__).resolve().relative_to(source)):sha(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(source)}
    report={'status':'EXACT883_SOURCE_OUTPUT_REBUILT','sha256':digest,'homogeneous_policy':sorted(policy),'qubits':c.num_qubits,'static_toffoli':c.operation_statistics().num_toffoli_like,'ops':len(c),'seconds':time.perf_counter()-start,'native_module_sha256':sha(native),'constructor_sha256':sha(Path(__file__)),'source_sha256':modules,'source_manifest_sha256':PACKET_PIN,'scope':'Genuine source-generated variant; original e9f54be3 identity and native full PASS are separate claims','attribution':'SomeJoint source architecture and Atakan retiming/repair lineage; this project profiles and selects the policy'}
    (out/'source-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}),flush=True)

if __name__=='__main__':main()
