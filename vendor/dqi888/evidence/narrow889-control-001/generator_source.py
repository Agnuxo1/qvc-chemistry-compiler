"""Rebuild reviewed SomeJointV21 and transfer our checked node policy.

The889Q architecture belongs to SomeJoint's team. We change only its existing
EXTERNAL_HOMOGENEOUS configuration before the reviewed cloning code runs.
No notebook launcher, network or installation is executed. The unmodified
control must exactly match the UI-downloaded public KMB before adoption.
"""
import argparse,ast,hashlib,importlib.util,json,shutil,sys,time
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--policy',choices=['control','repair'],required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out=a.out.resolve();assert a.out.is_relative_to(ROOT)
    a.out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    packet=ROOT/'artifacts/public-rising-review-001/somejoint-v21/embedded-source'
    source=packet/'blocks/dqi/team-1028-narrow240/source'
    pins=json.loads((packet/'AUTHENTICATED_SOURCE_MANIFEST.json').read_text())
    assert all(sha(packet/name)==digest for name,digest in pins.items())
    reviewed_dynamic={'exp/r-main/narrow240/decode_retimed.py','exp/r-main/narrow240/synth_stream.py'}
    banned_imports={'requests','urllib','httpx','socket','subprocess','ctypes'}
    for path in source.rglob('*.py'):
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):assert not any(x.name.split('.')[0] in banned_imports for x in node.names)
            if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in banned_imports
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ['exec','eval','__import__']:
                assert node.func.id=='exec' and path.relative_to(source).as_posix() in reviewed_dynamic
    sys.dont_write_bytecode=True
    sys.path[:0]=[str(ROOT/'runtimes/kickmix-manwithacat-0.3.0'),str(source/'playbook/kit/decoder'),str(source/'playbook/kit')]
    import kickmix as km
    sys.modules['circ']=km
    from final_decoder import decode as ref
    assert Path(ref.__file__).resolve().is_relative_to(source)
    original_policy=sorted(ref.EXTERNAL_HOMOGENEOUS)
    policy=frozenset(range(8,17)) if a.policy=='control' else frozenset([7,*range(10,17)])
    ref.EXTERNAL_HOMOGENEOUS=policy
    entry=source/'exp/r-main/narrow240/decode_retimed.py'
    spec=importlib.util.spec_from_file_location('reviewed_narrow889',entry)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    assert module.ext_env['EXTERNAL_HOMOGENEOUS']==policy
    b=km.CircuitBuilder();syndromes=[b.alloc_qubits(12) for _ in range(70)];errors=[b.alloc_bits(12) for _ in range(4095)]
    module.decode(b,syndromes,errors)
    metadata=[]
    for i in range(70):
        metadata.append(f'REGISTER r{i} "S{i}"');metadata.extend(f'APPEND_TO_REGISTER q{12*i+k} r{i}' for k in range(12))
    for i in range(4095):
        metadata.append(f'REGISTER r{70+i} "E{i}"');metadata.extend(f'APPEND_TO_REGISTER b{12*i+k} r{70+i}' for k in range(12))
    circuit=km.Circuit('\n'.join(metadata))+b.finish_circuit();dest=a.out/'dqi.kmb';circuit.to_file(dest,format='kmb')
    expected='6349d2bc82eb1ef3a4e8c52c71a312823d756532517463b5e18eb25cc81195a8'
    digest=sha(dest)
    report=dict(status='SOURCE_BUILT_NOT_VERIFIED',policy=a.policy,homogeneous_groups=sorted(policy),
        original_policy=original_policy,sha256=digest,Q=circuit.num_qubits,T_static=int(circuit.operation_statistics().num_toffoli_like),
        num_ops=len(circuit),source_packet_manifest_sha256=sha(packet/'AUTHENTICATED_SOURCE_MANIFEST.json'),
        decoder_entry_sha256=sha(entry),runtime=str(km.__file__),source_notebook_run=363462588,
        source_attribution='SomeJointV21 team889Q architecture; our existing node7 homogeneous /ordinary8,9 policy transfer only',
        exact_public_control_match=digest==expected,native_full_check_performed=False,
        source_sha256=sha(Path(__file__)),seconds=time.perf_counter()-start,created_utc=datetime.now(timezone.utc).isoformat())
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(__file__,a.out/'generator_source.py')
    print(json.dumps(report),flush=True)
    if a.policy=='control':assert digest==expected,'Control rebuild differs; do not treat this as byte-reproduced architecture'


if __name__=='__main__':main()
