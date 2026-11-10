# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC H14 numerical gate | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Check the continuation seed with a converged finite-difference grid."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import torch
import gauge_search_v2 as m

ROOT=Path(__file__).resolve().parent
seed=ROOT/'main-seed.npz'
data,raw=m.load(seed)
a=torch.tensor(raw,dtype=torch.float64);r,b,c=a.shape
rng=np.random.default_rng(20261110)
rot=np.stack([np.linalg.qr(rng.normal(size=(c,c)))[0] for _ in range(r)])
after=raw@rot
gram=float(np.max(np.abs(after@after.transpose(0,2,1)-raw@raw.transpose(0,2,1))))
old_off=data['H2_I']-data['W'].sum(1);w=after[:,:-1];new_off=after[:,-1]-w.sum(1)
cross=float(np.max(np.abs(np.einsum('rc,rbc->rb',old_off,data['W'])-np.einsum('rc,rbc->rb',new_off,w))))
assert gram<1e-10 and cross<1e-10
eye=torch.eye(c,dtype=torch.float64).expand(r,c,c).clone()
value=float(m.objective(a,eye).sum())
official_formula=float(.25*np.sum((np.abs(data['W']).sum(1)+np.abs(data['H2_I']))**2))
assert math.isclose(value,official_formula,rel_tol=1e-13)
q=eye[:1].clone().requires_grad_(True);aa=a[:1];delta=1e-4
m.objective(aa,q,delta).sum().backward()
direction=torch.tensor(rng.normal(size=q.shape));analytic=float((q.grad*direction).sum())
rows=[]
for h in (1e-4,1e-5,1e-6,1e-7,3e-8,1e-8):
    finite=float((m.objective(aa,q.detach()+h*direction,delta)-m.objective(aa,q.detach()-h*direction,delta)).sum()/(2*h))
    rows.append({'step':h,'finite':finite,'analytic':analytic,'relative_error':abs(finite-analytic)/max(1.,abs(analytic))})
assert any(x['relative_error']<1e-7 and y['relative_error']<1e-7 for x,y in zip(rows,rows[1:])),rows
record={'status':'PASS','scope':'Main seed numerical gate; central-difference step-size convergence, no tolerance relaxation','lambda_h2':value,'augmented_gram_max_drift':gram,'offset_contraction_max_drift':cross,'finite_difference_grid':rows,'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'search_source_sha256':hashlib.sha256((ROOT/'gauge_search_v2.py').read_bytes()).hexdigest(),'gate_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(ROOT/'main-continuation-gate.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(ROOT/'MAIN_SEED.json').write_text(json.dumps({'source':'pilot-v2-64/best-table.npz','sha256':record['seed_sha256'],'lambda_h2':value,'original_s37_lambda_h2':272.44041078498174,'selection':'Lower projected exact normalization of the two preregistered pilots'},indent=2),encoding='utf-8')
print(json.dumps(record),flush=True)
