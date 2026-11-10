"""Same generated valid inputs at each Hamming weight, across candidates.

This is a diagnostic stress grid, not the official weighted error estimate.
The unchanged official sampler generates256shots for each k=0..35. The
generated seed schedule is fixed before candidates are evaluated.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'runtimes/kickmix-manwithacat-0.3.0'),str(ROOT/'reference/public-tools/manwithacat-kickmix-eb36f245')]
import dqi_failure_logger as helper


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',action='append',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--rng-seed-base',type=int,default=202610281300)
    p.add_argument('--sim-seed-base',type=int,default=202610281400)
    a=p.parse_args();a.out.mkdir(exist_ok=False);start=time.perf_counter()
    helper.setup(ROOT/'runtimes/kickmix-manwithacat-0.3.0',ROOT/'reference/competition')
    rows=[];bank=[]
    for item in a.candidate:
        label,path=item.split('=',1);c,problem,regs,tables,wp=helper.load(Path(path));digest=helper.M._circuit_sha256(c);grid=[]
        for weight in range(36):
            one=np.zeros_like(wp);one[weight]=1;rng_seed=a.rng_seed_base+weight;sim_seed=a.sim_seed_base+weight
            syn,mask,ph,weights,words=helper.batch_inputs(problem,tables,one,rng_seed,256)
            val,phase,flipped,diff,junk=helper.simulate(c,problem,regs,syn,mask,ph,sim_seed,256)
            grid.append(dict(weight=weight,shots=256,value_errors=int(val.sum()),phase_errors=int(phase.sum()),rng_seed=rng_seed,sim_seed=sim_seed))
            for slot in np.flatnonzero(val|phase)[:2]:
                slot=int(slot);pos,vals=words.get(slot,([],[]))
                bank.append(dict(circuit=label,circuit_sha256=digest,salt=f'local-weight-grid-{weight}',kind='value' if val[slot] else 'phase',
                     error_weight=weight,batch=weight,slot=slot,shot_index=256*weight+slot,rng_seed=str(rng_seed),sim_seed=str(sim_seed),
                     error_positions=pos,error_values=vals,syndromes=syn[slot].tolist(),mbuc_masks=mask[slot].tolist(),
                     expected_phase_flip=bool(ph[slot]),observed_phase_flip=bool(flipped[slot]),
                     syndrome_bits_changed=np.flatnonzero(diff[:,slot]).tolist(),ancilla_bits_dirty=np.flatnonzero(junk[:,slot]).tolist(),
                     sampling='One-hot weight distribution, NOT the competition weight mixture'))
        row=dict(label=label,circuit_sha256=digest,rows=grid,shots=9216,
                 value_errors=sum(r['value_errors'] for r in grid),phase_errors=sum(r['phase_errors'] for r in grid))
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='rows'}),flush=True)
        del c
    report=dict(status='DIAGNOSTIC_WEIGHT_GRID_COMPLETE',created_utc=datetime.now(timezone.utc).isoformat(),
                scope=__doc__,rows=rows,seconds=time.perf_counter()-start,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'generated-failures.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in bank));(a.out/'generator_source.py').write_bytes(Path(__file__).read_bytes())


if __name__=='__main__':main()
