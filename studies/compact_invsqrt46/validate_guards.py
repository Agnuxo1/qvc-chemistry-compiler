# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
import copy,json,tempfile
from pathlib import Path
import compact_invsqrt as inv
import complete_portfolio as portfolio
root=Path(__file__).resolve().parent
receipts=[json.loads((root/('native-'+name+'.json')).read_text()) for name in ['default','independent']]
for receipt in receipts: inv.validate_native_receipt(receipt)
portfolio.validate_snapshot(root/'portfolio-source')
rejections=[]
for field,value in [('circuit_sha256','0'*64),('verified_shots',1),('num_qubits',62),('status','FAIL')]:
    changed=copy.deepcopy(receipts[0]);changed[field]=value
    try: inv.validate_native_receipt(changed)
    except RuntimeError: rejections.append(field)
    else: raise AssertionError('Invalid native receipt accepted: '+field)
with tempfile.TemporaryDirectory(dir=root,prefix='guard-negative-') as tmp:
    dest=Path(tmp);(dest/'STAGED_SOURCE_MANIFEST.json').write_text(json.dumps({'changed.py':'0'*64}))
    try: portfolio.validate_snapshot(dest)
    except RuntimeError: rejections.append('manifest_root')
    else: raise AssertionError('Substituted manifest accepted')
report={'status':'PASS','real_receipts_accepted':2,'real_snapshot_accepted':123,'negative_controls_rejected':rejections}
(root/'guard-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
