# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Run stock full native verifiers; preserve input and verifier fingerprints."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('task',choices=['chem','invsqrt','dqi'])
    p.add_argument('input',type=Path)
    p.add_argument('receipt',type=Path)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--salt',default='replication-a')
    p.add_argument('--workers',type=int,default=3)
    a=p.parse_args()
    if a.receipt.exists():raise FileExistsError(a.receipt)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(key,'1')
    sys.path[:0]=[str(a.runtime.resolve()),str((a.data/'verifiers').resolve())]
    files=sorted(a.input.glob('*.kmb'))+[a.input/'submission.npz'] if a.task=='chem' else [a.input]
    inputs={f.name:sha(f) for f in files}
    start=time.perf_counter()
    if a.task=='chem':
        from dfthcsos import verify as v
        result=v.verify(a.input,shots_per_address=64,salt=a.salt)
        m=result['metrics']
        lam=math.sqrt(m['E_gap']*(2*m['Lambda']-m['E_gap']))
        assert math.isclose(lam,result['lambda_eff'],rel_tol=1e-12)
        assert math.isclose(lam*result['toffoli_count']*result['num_qubits'],result['score'],rel_tol=1e-12)
    else:
        import kickmix as km
        c=km.Circuit.from_file(str(a.input),format='kmb')
        if a.task=='invsqrt':
            from invsqrt import verify_submission_invsqrt as v
            spec=v.ProblemSpecInvSqrt.for_n_p(10)
        else:
            from dqi import verify_submission_dqi as v
            spec=v.ProblemSpecDQI.benchmark_instance()
        result=v.verify(c,spec,salt=a.salt,max_workers=a.workers)
        result.pop('shot_operation_counts',None)
    status=result.get('status')
    receipt={'task':a.task,'scope':'Full local native check; not a Kaggle submission','status':status,'salt':a.salt,'input_sha256':inputs,'verifier_sha256':sha(Path(v.__file__)),'wrapper_sha256':sha(Path(__file__)),'python':sys.version,'platform':platform.platform(),'seconds':time.perf_counter()-start,'official_result':result}
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({'status':status,'receipt':str(a.receipt),'seconds':receipt['seconds']}),flush=True)
    if status!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
