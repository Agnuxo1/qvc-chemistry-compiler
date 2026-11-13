# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
import copy,json,shutil,sys,tempfile
from pathlib import Path
from finalize_candidate import validate_run_binding
from compact_invsqrt import sha
root=Path(__file__).resolve().parent
native=Path(sys.argv[1]).resolve()
checks=[]
validate_run_binding(native,sha(native/'integration-report.json'));checks.append('real_execution_binding_pass')
with tempfile.TemporaryDirectory(dir=root,prefix='binding-negative-') as temp:
    dest=Path(temp)
    for name in ['invsqrt.kmb','official-default.json','official-independent.json']:shutil.copy2(native/name,dest/name)
    report=json.loads((native/'integration-report.json').read_text())
    for r in report['official_runs']:r['command'][3]=str(dest/'invsqrt.kmb')
    def save(r):
        (dest/'integration-report.json').write_text(json.dumps(r,indent=2));return sha(dest/'integration-report.json')
    digest=save(report);validate_run_binding(dest,digest);checks.append('isolated_valid_copy_pass')
    original={n:(dest/('official-'+n+'.json')).read_bytes() for n in ['default','independent']}
    def reject(name,expected):
        try:validate_run_binding(dest,expected)
        except RuntimeError:checks.append(name)
        else:raise AssertionError('Invalid run binding accepted: '+name)
    (dest/'official-independent.json').write_bytes(original['default']);reject('duplicate_receipt_rejected',digest)
    (dest/'official-default.json').write_bytes(original['independent']);(dest/'official-independent.json').write_bytes(original['default']);reject('swapped_receipts_rejected',digest)
    for n,b in original.items():(dest/('official-'+n+'.json')).write_bytes(b)
    changed=copy.deepcopy(report);changed['official_runs'][1]['command'][-1]='wrong-salt';reject('command_salt_mismatch_rejected',save(changed))
    changed=copy.deepcopy(report);changed['official_runs'].reverse();reject('run_order_mismatch_rejected',save(changed))
    save(report);reject('execution_report_root_mismatch_rejected','0'*64)
result={'status':'PASS','checks':checks}
(root/'binding-controls.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
