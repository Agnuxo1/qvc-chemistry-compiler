# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Generate the source-complete reference control; not the optimized portfolio."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
from reconstruir_quimica import rebuild

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    root=Path(__file__).resolve().parents[1]
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(key,'1')
    sys.path[:0]=[str(a.runtime.resolve()),str((a.data/'verifiers').resolve())]
    from invsqrt import nr_reference_circuit as inv
    from dqi import dqi_reference_circuit as dqi
    pins=json.loads((root/'recipes/reference-pins.json').read_text())
    a.output.mkdir(parents=True)
    results={}
    for task,module in (('invsqrt',inv),('dqi',dqi)):
        start=time.perf_counter()
        c=module.build_nr_circuit(10) if task=='invsqrt' else module.build_reference_circuit(4095,70,12)
        path=a.output/(task+'.kmb');c.to_file(str(path),format='kmb')
        assert digest(path)==pins[task],f'{task}: exact reference hash changed'
        results[task]={'sha256':digest(path),'qubits':c.num_qubits,'static_toffoli':c.operation_statistics().num_toffoli_like,'generator_sha256':digest(Path(module.__file__)),'seconds':time.perf_counter()-start}
        print(json.dumps({'task':task,**results[task]}),flush=True)
        del c
    rebuild(root/'recipes/s37',(a.output/'dfthcsos').resolve(),a.data.resolve(),a.runtime.resolve())
    (a.output/'dfthcsos-reconstruction.json').rename(a.output.parent/(a.output.name+'-chemistry-reconstruction.json'))
    results['scope']='Reference invsqrt/DQI plus optimized frozen chemistry; not the performance portfolio.'
    results['build_tool_sha256']=digest(Path(__file__))
    results['output_sha256']={p.relative_to(a.output).as_posix():digest(p) for p in a.output.rglob('*') if p.is_file()}
    assert len(results['output_sha256'])==18
    (a.output.parent/(a.output.name+'-source-build.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')

if __name__=='__main__':main()
