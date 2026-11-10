# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC recovered mathematical phase | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Compare a recovered numerical formula with the original circuit, never generate one."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
import numpy as np

MASK=(1<<64)-1
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def rd(v,e):return (v>>e)+((v>>(e-1))&1) if e>0 else v<<(-e)

def phases(xs,tables,high,angles):
    xs=np.asarray(xs,dtype=np.int64);t=21-np.floor(np.log2(xs)).astype(np.int64);xn=xs<<t;s=t>>1;a=((t&1)<<7)|((xn>>14)&127);delta=xn&16383
    C0,C1,C2=(tables[a,i] for i in range(3));T=C1.copy()
    for i in range(6,14):T-=(2*((delta>>i)&1)-1)*rd(C2,12-i)
    Y=C0.copy()
    for i in range(14):Y-=(2*((delta>>i)&1)-1)*rd(T,13-i)
    H=high[a];L=Y-(H<<20);VH=(H+128)<<s
    large=s>=8;assert np.all(delta[large]==0)
    VH+=np.where(large,(L>>np.maximum(0,28-s))<<8,0)
    VL=(L>>1)<<s;result=np.zeros(len(xs),dtype=np.uint64)
    for j,ang in enumerate(angles[0]):
        if j>=19 and ang:result+=((VH>>(j-19))&1).astype(np.uint64)*np.uint64(ang&MASK)
    for j,ang in enumerate(angles[1][:27]):
        if ang:result+=((VL>>j)&1).astype(np.uint64)*np.uint64(ang&MASK)
    bit=((L>>1)&1).astype(np.uint64);gray=((s^(s>>1))&1).astype(np.uint64)
    result+=bit*gray*np.uint64(angles[1][1]);result-=bit*np.array(angles[1],dtype=np.uint64)[s]
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True);ap.add_argument('--circuit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');sys.dont_write_bytecode=True
    a.out.mkdir(exist_ok=False,parents=True);sys.path[:0]=[str(a.runtime.resolve()),str(a.data/'verifiers')]
    import kickmix as km
    from invsqrt import verify_submission_invsqrt as v
    numeric=a.root/'recipe.json';angle_path=a.root/'angles.json';raw=json.loads(numeric.read_text());tables=np.array(raw['recipe']['tables'],dtype=np.int64)
    high=np.zeros(256,dtype=np.int64)
    for row in raw['observed_layout']:high[row['address']]=row['H']
    angles=json.loads(angle_path.read_text())['angles'];xs=np.arange(1,3133453,dtype=np.int64);start=time.perf_counter();expected=phases(xs,tables,high,angles)
    target,tol=v.reference_values(v.ProblemSpecInvSqrt.for_n_p(10),xs.astype(np.uint64));error=(expected-target).view(np.int64);ratio=np.abs(error).astype(np.float64)/tol;worst_idx=int(np.argmax(ratio))
    report={'scope':'Full numerical tolerance check plus one stochastic native branch per legal input against recovered phase; not a generator or coherent-all-branches proof','numeric_formula_sha256':sha(Path(__file__)),'recipe_sha256':sha(numeric),'angles_sha256':sha(angle_path),'circuit_sha256':sha(a.circuit),'numeric_status':'PASS' if ratio.max()<1 else 'FAIL','worst_error_over_tolerance':float(ratio[worst_idx]),'worst_x':worst_idx+1,'numeric_seconds':time.perf_counter()-start}
    (a.out/'numeric.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    assert report['numeric_status']=='PASS'
    assert report['circuit_sha256']=='26ebf39df3b13e5fd2d923d1b9988043b107b64f6e21efc5cc9bc76f5d56adec'
    circuit=km.Circuit.from_file(str(a.circuit),format='kmb');xr=km.array(list(circuit.register_data['x']));qset=set(xr);scratch=km.array([km.q(i) for i in range(circuit.num_qubits) if km.q(i) not in qset]);sim=km.Simulator(batch_size=256,seed=261110,debug_print=False,counting_operations=False)
    def units(h):
        n,d=h.as_integer_ratio();return (((n<<64)//d+1)>>1)&MASK
    total=0;mismatch=0;dirty=0;changed=0;first=[];native_start=time.perf_counter()
    for offset in range(0,len(xs),256):
        values=xs[offset:offset+256].astype(np.uint64);valid=len(values)
        if valid<256:values=np.r_[values,np.ones(256-valid,dtype=np.uint64)]
        sim.clear_for_shot();sim.write_across_shots(xr,((values[None,:]>>np.arange(22,dtype=np.uint64)[:,None])&1)==1);sim.do(circuit)
        actual=np.array([units(sim.read_shot_phase(i)) for i in range(valid)],dtype=np.uint64);bad=np.flatnonzero(actual!=expected[offset:offset+valid]);mismatch+=len(bad)
        if len(first)<10:first.extend((offset+bad[:10]+1).tolist());first=first[:10]
        restored=(sim.read_across_shots(xr).astype(np.uint64)<<np.arange(22,dtype=np.uint64)[:,None]).sum(axis=0);changed+=int(np.count_nonzero(restored[:valid]!=values[:valid]));dirty+=int(np.count_nonzero(sim.read_across_shots(scratch)[:,:valid].any(axis=0)));total+=valid
        if offset%262144==0:print(json.dumps({'inputs_compared':total,'exact_phase_mismatches':mismatch,'input_changes':changed,'dirty_scratch_shots':dirty,'native_seconds':time.perf_counter()-native_start}),flush=True)
    report.update(status='PASS' if not(mismatch or dirty or changed) else 'FAIL',inputs_compared=total,exact_phase_mismatches=mismatch,input_changes=changed,dirty_scratch_shots=dirty,first_mismatches=first,native_seconds=time.perf_counter()-native_start)
    (a.out/'native-model-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    if report['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
