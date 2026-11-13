# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Record upstream compiled fixture reads and their Python caller stack."""
import atexit,json,os,sys,traceback
_log=os.environ.get('QVC_AUDIT_LOG')
_busy=False
_enforce=os.environ.get('QVC_ENFORCE')=='1'
_nonce=os.environ.get('QVC_AUDIT_NONCE','')
def _receipt(event):
    with open(_log,'a') as f:f.write(json.dumps({'event':event,'pid':os.getpid(),'nonce':_nonce,'argv':sys.argv.copy(),'enforced':_enforce})+'\n')
_hash_sites={
('arithmetic_round2/native/candidate10/arithmetic_variant.py',26),
('arithmetic_round2/research/divider/native_ar004/adapter.py',18),
('arithmetic_round2/research/root_normalization/native_rn2df/normalization9475.py',19),
('arithmetic_round2/research/root_normalization/native_rn3/root192.py',12),
('native/candidate04/variant.py',16),('native/candidate04/variant.py',55),
('native/candidate05/variant.py',14),('native/candidate06/variant.py',26),('native/candidate07/variant.py',26)}
def _audit(event,args):
    global _busy
    if _busy or event!='open' or not _log: return
    path=str(args[0])
    if not path.endswith(('.kmb','.kmx','.bin','.npy','.npz')): return
    mode=args[1]
    if isinstance(mode,str) and any(c in mode for c in 'wax'): return
    _busy=True
    try:
        row={'pid':os.getpid(),'path':path,'mode':mode,'stack':[{'file':s.filename,'line':s.lineno,'name':s.name} for s in traceback.extract_stack(limit=14)[:-1]]}
        if _enforce and '/tree/work/c10/' in path:
            caller=[s for s in row['stack'] if '/tree/' in s['file']][-1]
            key=(caller['file'].split('/narrow/',1)[1],caller['line'])
            if key not in _hash_sites: raise RuntimeError('Forbidden compiled fixture consumption: '+path)
        with open(_log,'a') as f: f.write(json.dumps(row)+'\n')
    finally: _busy=False
sys.addaudithook(_audit)
def _profile(frame,event,arg):
    if event=='c_call' and getattr(arg,'__name__','')=='from_file' and any(str(a).endswith('build_variant.py') for a in sys.argv):
        raise RuntimeError('Generator may not load a compiled circuit')
if _enforce:
    sys.setprofile(_profile)
    sys._qvc_audit_active=_nonce
    _receipt('audit-start')
    atexit.register(_receipt,'audit-end')
