"""Audited stock/fork and serial/spawn DQI runtime comparison.

The competition verifier files and circuits stay unchanged. The fork is
isolated by sys.path in a fresh child. Spawn scheduling is manwithacat's
unmodified, reviewed verify_parallel.py at the recorded commit. A fork/spawn
result is parity/performance evidence, never a replacement for the stock
competition implementation or a new hosted score.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/'reference/public-tools/manwithacat-kickmix-eb36f245'
FORK=ROOT/'runtimes/kickmix-manwithacat-0.3.0'


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',choices=['stock','fork'],required=True)
    p.add_argument('--scheduler',choices=['serial','spawn'],default='serial')
    p.add_argument('--workers',type=int,default=1)
    p.add_argument('--circuit',type=Path,default=ROOT/'artifacts/public-v12-plus-our-v2-001/submission/dqi.kmb')
    p.add_argument('--salt',default='salt-check-3')
    p.add_argument('--seed',type=int,default=None,help='Official explicit seed; same inputs across circuit hashes')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.child:
        if args.runtime=='fork':sys.path.insert(0,str(FORK))
        sys.path[:0]=[str(UPSTREAM),str(ROOT/'reference/competition/verifiers')]
        import kickmix as km
        import importlib.metadata as metadata
        if args.scheduler=='spawn':
            import verify_parallel as vp
            load_args=(str(ROOT/'reference/competition/verifiers'),vp.TASKS['dqi'][0],'dqi',str(args.circuit.resolve()))
            if args.seed is None:result=vp.verify_spawned(load_args,args.salt,args.workers)
            else:
                from dqi_seeded_spawn import verify_seeded_spawned
                result=verify_seeded_spawned(load_args,args.salt,args.seed,args.workers)
        else:
            from dqi.verify_submission_dqi import ProblemSpecDQI,verify
            circuit=km.Circuit.from_file(args.circuit,format='kmb')
            result=verify(circuit,ProblemSpecDQI.benchmark_instance(),salt=args.salt,seed=args.seed,max_workers=1)
        print(json.dumps(dict(result=result,kickmix_path=km.__file__,kickmix_version=metadata.version('kickmix'))),flush=True)
        return
    import psutil
    args.out.mkdir(parents=True,exist_ok=False)
    record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),
        scope='Full default DQI shot domain; runtime/scheduler parity and performance experiment, not hosted score',
        runtime=args.runtime,scheduler=args.scheduler,workers=args.workers,salt=args.salt,explicit_seed=args.seed,
        seeded_scheduler_sha256=sha(ROOT/'tools/dqi_seeded_spawn.py') if args.seed is not None and args.scheduler=='spawn' else None,
        circuit_sha256=sha(args.circuit),verifier_sha256=sha(ROOT/'reference/competition/verifiers/dqi/verify_submission_dqi.py'),
        scheduler_source_sha256=sha(UPSTREAM/'verify_parallel.py'),scheduler_source_commit='eb36f245029140e70a5797b33dc8c373dccbc4a5',
        generator_sha256=sha(__file__))
    path=args.out/'report.json';path.write_text(json.dumps(record,indent=2)+'\n')
    command=[sys.executable,str(Path(__file__).resolve()),*sys.argv[1:],'--child']
    env=os.environ.copy()
    for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):env[key]='1'
    peak=0;max_processes=0;start=time.perf_counter()
    with (args.out/'stdout.json').open('w',encoding='utf-8') as stdout,(args.out/'stderr.log').open('w',encoding='utf-8') as stderr:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
        watch=psutil.Process(process.pid)
        while process.poll() is None:
            try:group=[watch]+watch.children(recursive=True)
            except psutil.NoSuchProcess:group=[]
            rss=0
            for proc in group:
                try:rss+=proc.memory_info().rss
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            peak=max(peak,rss);max_processes=max(max_processes,len(group));time.sleep(.15)
    record.update(returncode=process.returncode,wall_seconds=time.perf_counter()-start,
        peak_sum_rss_mb=peak/2**20,max_processes=max_processes,finished_utc=datetime.now(timezone.utc).isoformat())
    if process.returncode==0:
        result=json.loads((args.out/'stdout.json').read_text());record.update(status='COMPLETE',**result)
    else:record['status']='FAILED'
    path.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
    if process.returncode:raise SystemExit(process.returncode)


if __name__=='__main__':main()
