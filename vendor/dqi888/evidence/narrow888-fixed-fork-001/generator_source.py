"""Probe each fixed logical DQI case under many measurement outcomes.

Each public input is replicated256times, twice with different simulator
seeds. This separates deterministic decoder/oracle failure from unresolved
measurement-dependent phase debt. It is a biased diagnostic, not accuracy
estimation. Candidate hashes may differ intentionally for controlled tests;
the source input hash and evaluated circuit hash are always recorded.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtimes/kickmix-manwithacat-0.3.0'))
sys.path.insert(0,str(ROOT/'reference/public-tools/manwithacat-kickmix-eb36f245'))
import dqi_failure_logger as helper
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',choices=['fork','stock'],default='fork')
    p.add_argument('--candidate',type=Path,default=ROOT/'artifacts/public-v12-plus-our-v2-001/submission/dqi.kmb')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(exist_ok=False);start=time.perf_counter()
    build=ROOT/'runtimes/kickmix-manwithacat-0.3.0'
    if a.runtime=='stock':
        sys.path[:]=[x for x in sys.path if Path(x).resolve()!=build.resolve()]
        import kickmix
        build=Path(kickmix.__file__).parent.parent
    helper.setup(build,ROOT/'reference/competition')
    circuit,problem,regs,tables,wp=helper.load(a.candidate)
    cases=[json.loads(x) for x in (ROOT/'datasets/qcc-public-dqi-counterexamples-v1/counterexamples.jsonl').read_text().splitlines()]
    rows=[]
    for c in cases:
        syn=np.tile(np.array(c['syndromes'],np.int64),(256,1));mask=np.tile(np.array(c['mbuc_masks'],np.int64),(256,1));phase=np.full(256,c['expected_phase_flip'],bool)
        runs=[]
        for seed in [2026102801,2026102802]:
            val,ph,flipped,diff,junk=helper.simulate(circuit,problem,regs,syn,mask,phase,seed,256)
            runs.append(dict(seed=seed,replicas=256,value_errors=int(val.sum()),phase_errors=int(ph.sum()),
                phase_flips=int(flipped.sum()),syndrome_changed_min=int(diff.sum(0).min()),syndrome_changed_max=int(diff.sum(0).max()),
                dirty_ancilla_min=int(junk.sum(0).min()),dirty_ancilla_max=int(junk.sum(0).max())))
        rows.append(dict(case_salt=c['salt'],source_kind=c['kind'],error_weight=c['error_weight'],runs=runs))
    report=dict(status='FIXED_INPUT_MEASUREMENT_TRANSCRIPT_DIAGNOSTIC',created_utc=datetime.now(timezone.utc).isoformat(),
        circuit_sha256=helper.M._circuit_sha256(circuit),candidate=str(a.candidate),runtime=a.runtime,kickmix_path=helper.km.__file__,source_input_circuit_sha256=cases[0]['circuit_sha256'],
        scope='Two targeted logical cases,256replicas each x2simulator seeds; not full task or unbiased error rate',
        rows=rows,seconds=time.perf_counter()-start,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(a.out/'generator_source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
