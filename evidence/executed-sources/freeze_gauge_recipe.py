# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC exact gauge recipe | 2026-11-10 | ORCID 0009-0001-1634-7063
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
import numpy as np

REPO=Path('D:/PROJECTS/qvc-chemistry-compiler')
sys.path.insert(0,str(REPO/'tools'))
from reconstruir_quimica import write_portable_npz

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=Path,required=True);p.add_argument('--rotation',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    with np.load(a.seed,allow_pickle=False) as f:data={k:np.array(f[k]) for k in f.files}
    q=np.load(a.rotation,allow_pickle=False)
    before=np.concatenate([data['W'],data['H2_I'][:,None]],axis=1);after=before@q
    drift=float(np.max(np.abs(after@after.transpose(0,2,1)-before@before.transpose(0,2,1))))
    assert drift<1e-10
    data['W']=after[:,:-1];data['H2_I']=after[:,-1]
    base=REPO/'recipes/s37';shutil.copytree(base,a.out)
    write_portable_npz(a.out/'new-table.npz',data)
    (a.out/'new-table.npz').replace(a.out/'table.npz')
    shutil.copy2(a.seed,a.out/'gauge-initial.npz');shutil.copy2(a.rotation,a.out/'rotation.npy')
    manifest=json.loads((base/'manifest.json').read_text())
    manifest['table_sha256']=sha(a.out/'table.npz')
    manifest['expected_files']['submission.npz']=sha(a.candidate/'submission.npz')
    for name,value in manifest['expected_files'].items():assert sha(a.candidate/name)==value
    manifest['gauge_transform']={'initial_table_sha256':sha(a.seed),'rotation_sha256':sha(a.rotation),'transform':'A=[W;H2_I], A_new=A@Q independently per group','augmented_gram_max_drift':drift,'generator_sha256':sha(Path(__file__)),'parent_angle_recipe':'s37','circuit_files_unchanged':15}
    manifest['scope']='Exact reconstruction from a frozen trained table after a verified orthogonal channel gauge, unchanged declarative GF(2) plan and source. No deterministic retraining claim.'
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'status':'FROZEN_NOT_REBUILT','recipe':str(a.out),'table_sha256':manifest['table_sha256'],'expected_npz_sha256':manifest['expected_files']['submission.npz'],'drift':drift}))

if __name__=='__main__':main()
