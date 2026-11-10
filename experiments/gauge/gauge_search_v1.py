# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler — H14 scale experiment | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Batched smoothed Riemannian channel-gauge search, with physical invariants.

Orthogonal gauge optimization is credited to the public marculera/refine
pipeline and the project's prior CPU study. This is a scale experiment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import numpy as np
import torch

def objective(a,q,delta=0.):
    y=a@q
    return .25*(torch.sqrt(y*y+delta*delta).sum(-2)**2).sum(-1)

def polar(q,steps=4):
    for _ in range(steps):q=1.5*q-.5*(q@(q.transpose(-1,-2)@q))
    return q

def gradient_step(a,q,scale,lr,delta):
    y=a@q;s=torch.sqrt(y*y+delta*delta);n=s.sum(-2,keepdim=True)
    g=.5*(a.transpose(-1,-2)@((y/s)*n))/scale[...,None,None]
    qt=q.transpose(-1,-2)@g
    tangent=g-.5*(q@(qt+qt.transpose(-1,-2)))
    return polar(q-lr*tangent)

def load(seed):
    with np.load(seed,allow_pickle=False) as f:data={k:np.array(f[k]) for k in f.files}
    a=np.concatenate([data['W'],data['H2_I'][:,None,:]],axis=1).astype(np.float64)
    return data,a

def cpu_gate(seed,out):
    data,raw=load(seed);a=torch.tensor(raw,dtype=torch.float64)
    r,b,c=a.shape;eye=torch.eye(c,dtype=torch.float64).expand(r,c,c).clone()
    rng=np.random.default_rng(20261110)
    q=np.stack([np.linalg.qr(rng.normal(size=(c,c)))[0] for _ in range(r)])
    changed=raw@q;drift=np.max(np.abs(changed@changed.transpose(0,2,1)-raw@raw.transpose(0,2,1)))
    offsets=data['H2_I']-data['W'].sum(1)
    w=changed[:,:-1];off=changed[:,-1]-w.sum(1)
    cross=np.max(np.abs(np.einsum('rc,rbc->rb',off,w)-np.einsum('rc,rbc->rb',offsets,data['W'])))
    original=.25*np.sum((np.abs(data['W']).sum(1)+np.abs(data['H2_I']))**2)
    torch_value=float(objective(a,eye).sum());assert math.isclose(original,torch_value,rel_tol=1e-13)
    # Independent directional derivative of the smooth objective on one group.
    aa=a[:1];qq=eye[:1].clone().requires_grad_(True);delta=1e-4
    loss=objective(aa,qq,delta).sum();loss.backward();direction=torch.tensor(rng.normal(size=qq.shape),dtype=torch.float64)
    eps=1e-6
    finite=float((objective(aa,qq.detach()+eps*direction,delta)-objective(aa,qq.detach()-eps*direction,delta)).sum()/(2*eps))
    analytic=float((qq.grad*direction).sum());assert math.isclose(finite,analytic,rel_tol=1e-7,abs_tol=1e-8)
    perturb=eye+.001*torch.tensor(rng.normal(size=eye.shape),dtype=torch.float64)
    projected=polar(perturb);orth=float(torch.max(torch.abs(projected.transpose(-1,-2)@projected-eye)))
    assert drift<1e-10 and cross<1e-10 and orth<1e-10
    scale=objective(a,eye).clamp_min(1e-12)
    trial=torch.tensor(q,dtype=torch.float64);start=float(objective(a,trial,1e-4).sum())
    for _ in range(40):trial=gradient_step(a,trial,scale,.03,1e-4)
    end=float(objective(a,trial,1e-4).sum());assert end<start
    report={'status':'PASS','lambda_h2':original,'augmented_gram_max_drift':float(drift),'offset_contraction_max_drift':float(cross),'polar_orthogonality_max_error':orth,'directional_derivative_finite':finite,'directional_derivative_autograd':analytic,'smoke_start_smooth':start,'smoke_end_smooth':end,'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.mkdir(exist_ok=False,parents=True);(out/'cpu-gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

def search(seed,out,wall,batch,device):
    if device!='cuda':raise ValueError('GPU experiment requires an explicitly allocated CUDA device')
    torch.set_num_threads(2);torch.manual_seed(20261110)
    data,raw=load(seed);out.mkdir(exist_ok=False,parents=True)
    a=torch.tensor(raw,device=device,dtype=torch.float64)
    r,b,c=a.shape;identity=torch.eye(c,device=device,dtype=torch.float64).expand(r,c,c).clone()
    baseline=objective(a,identity);scale=baseline.clamp_min(1e-12)
    best=baseline.clone();best_q=identity.clone()
    magnitudes=torch.tensor([0.,.001,.003,.01,.03,.1],device=device,dtype=torch.float64)
    noise=torch.randn(batch,r,c,c,device=device,dtype=torch.float64)
    noise=noise-noise.transpose(-1,-2)
    sizes=magnitudes[torch.arange(batch,device=device)%len(magnitudes)]
    q=identity[None]+sizes[:,None,None,None]*noise
    # Independent SVD polar projection is valid for all perturbation sizes.
    u,_,v=torch.linalg.svd(q);q=u@v
    q[0]=identity
    start=time.monotonic();last_save=-1.;step=0;best_overall=float(best.sum());records=[]
    while time.monotonic()-start<wall:
        elapsed=time.monotonic()-start
        cycle=(step%2000)/1999
        delta=10**(-3-5*cycle)
        lr=.03*(.1+.9*.5*(1+math.cos(math.pi*cycle)))
        q=gradient_step(a[None],q,scale[None],lr,delta)
        if step%10==0:
            values=objective(a[None],q)
            candidate,indices=values.min(0)
            improved=candidate<best
            chosen=q[indices,torch.arange(r,device=device)]
            best_q=torch.where(improved[:,None,None],chosen,best_q)
            best=torch.minimum(best,candidate)
        if elapsed-last_save>=30 or step==0:
            candidate_q=best_q.detach().cpu().numpy()
            u,_,v=np.linalg.svd(candidate_q);candidate_q=u@v
            augmented=raw@candidate_q
            gram_drift=float(np.max(np.abs(augmented@augmented.transpose(0,2,1)-raw@raw.transpose(0,2,1))))
            value=float(.25*np.sum(np.abs(augmented).sum(1)**2))
            assert gram_drift<1e-10
            if value<=best_overall:
                best_overall=value
                candidate={**data,'W':augmented[:,:-1],'H2_I':augmented[:,-1]}
                np.savez(out/'best-table.tmp.npz',**candidate)
                os.replace(out/'best-table.tmp.npz',out/'best-table.npz')
                np.save(out/'best-Q.npy',candidate_q)
            record={'seconds':elapsed,'step':step,'batch_per_group':batch,'baseline_lambda_h2':float(baseline.sum()),'best_projected_lambda_h2':best_overall,'relative_lambda_h2_gain':1-best_overall/float(baseline.sum()),'gram_max_drift':gram_drift,'cuda_peak_MiB':torch.cuda.max_memory_allocated()/1024**2}
            records.append(record);print(json.dumps(record),flush=True)
            (out/'progress.json').write_text(json.dumps({'records':records,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'device':torch.cuda.get_device_name()},indent=2))
            last_save=elapsed
        if step and step%2000==0:
            noise=torch.randn_like(q);noise=noise-noise.transpose(-1,-2)
            q=best_q[None]+sizes[:,None,None,None]*noise
            u,_,v=torch.linalg.svd(q);q=u@v;q[0]=best_q
        step+=1
    final={'status':'COMPLETE','steps':step,'seconds':time.monotonic()-start,'baseline_lambda_h2':float(baseline.sum()),'best_projected_lambda_h2':best_overall,'native_verification_performed':False}
    (out/'summary.json').write_text(json.dumps(final,indent=2));print(json.dumps(final),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed',type=Path,default=Path(__file__).parent/'seed.npz');p.add_argument('--out',type=Path,required=True);p.add_argument('--cpu-gate',action='store_true');p.add_argument('--wall-s',type=int,default=60);p.add_argument('--batch',type=int,default=32);a=p.parse_args()
    if a.cpu_gate:cpu_gate(a.seed,a.out)
    else:search(a.seed,a.out,a.wall_s,a.batch,'cuda')

if __name__=='__main__':main()
