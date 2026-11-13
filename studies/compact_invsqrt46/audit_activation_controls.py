# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
import json,os,tempfile,uuid
from pathlib import Path
from compact_invsqrt import audit_preflight,validate_audit_shim,validate_audit_log
root=Path(__file__).resolve().parent
checks=[]
with tempfile.TemporaryDirectory(dir=root,prefix='audit-activation-') as temp:
    work=Path(temp);nonce=uuid.uuid4().hex;log=work/'events.jsonl'
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'auditshim'),QVC_AUDIT_LOG=str(log),QVC_ENFORCE='1',QVC_AUDIT_NONCE=nonce)
    validate_audit_shim(root/'auditshim');audit_preflight(env);checks.append('real_pinned_hook_active')
    missing=work/'missing';missing.mkdir()
    for name,path in [('missing',missing),('corrupt',work)]:
        if name=='corrupt': (work/'sitecustomize.py').write_text('# no audit hook')
        try:validate_audit_shim(path)
        except RuntimeError: checks.append(name+'_shim_rejected')
        else:raise AssertionError('Bad audit shim accepted')
    env['PYTHONPATH']=str(missing)
    try:audit_preflight(env)
    except RuntimeError:checks.append('real_launch_without_hook_rejected')
    else:raise AssertionError('Launch without hook accepted')
    fake=work/'incomplete.jsonl';fake.write_text(json.dumps({'event':'audit-start','pid':1,'nonce':nonce,'enforced':True,'argv':['build_variant.py']})+'\n')
    try:validate_audit_log(fake,nonce)
    except RuntimeError:checks.append('missing_generator_close_rejected')
    else:raise AssertionError('Incomplete audit accepted')
    fake.write_text('')
    try:validate_audit_log(fake,nonce)
    except RuntimeError:checks.append('missing_generator_start_rejected')
    else:raise AssertionError('Missing generator audit accepted')
report={'status':'PASS','checks':checks}
(root/'audit-activation-controls.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
