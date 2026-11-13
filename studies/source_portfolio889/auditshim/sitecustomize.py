# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fail closed on compiled circuit input; acknowledge each audited source process."""
import atexit,json,os,sys
from pathlib import Path
log=os.environ.get('DQI_AUDIT_LOG');nonce=os.environ.get('DQI_AUDIT_NONCE');busy=False
def receipt(event):
    with open(log,'a') as f:f.write(json.dumps({'event':event,'pid':os.getpid(),'nonce':nonce,'argv':sys.argv.copy()})+'\n')
def audit(event,args):
    global busy
    if busy or event!='open':return
    path=str(args[0]);mode=args[1]
    if not path.endswith(('.kmb','.kmx')):return
    if isinstance(mode,str) and any(c in mode for c in 'wax'):return
    resolved=Path(path).resolve();allowed=Path(os.environ['DQI_OUTPUT_ROOT']).resolve()
    if not resolved.is_relative_to(allowed) or '/out/' not in resolved.as_posix():raise RuntimeError('Compiled circuit input forbidden')
    busy=True
    try:
        with open(log,'a') as f:f.write(json.dumps({'event':'generated-output-hash-read','path':path,'pid':os.getpid(),'nonce':nonce})+'\n')
    finally:busy=False
def profile(frame,event,arg):
    if event=='c_call' and getattr(arg,'__name__','')=='from_file':raise RuntimeError('Circuit.from_file forbidden in source construction')
if log and nonce:
    sys.addaudithook(audit);sys.setprofile(profile);sys._qvc_dqi_audit=nonce
    receipt('audit-start');atexit.register(receipt,'audit-end')
