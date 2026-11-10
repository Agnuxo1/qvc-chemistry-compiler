# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Create an 18-file receipt-bound ZIP and check stock metric input readers."""
from pathlib import Path
import argparse,gc,hashlib,importlib.util,json,math,shutil,stat,sys,zipfile

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load(path):return json.loads(path.read_text(encoding='utf-8'))

def file_hashes(receipt,task):
    if isinstance(receipt.get('input_sha256'),dict):return receipt['input_sha256']
    if 'inputs' in receipt:return {str(p).replace(chr(92),'/').rsplit('/',1)[-1]:x['sha256'] for p,x in receipt['inputs'].items()}
    value=receipt.get('circuit_sha256',receipt['official_result'].get('circuit_sha256'))
    if value:return {task+'.kmb':value}
    raise ValueError('Receipt lacks input hashes')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--invsqrt',type=Path,required=True)
    p.add_argument('--dqi-a',type=Path,required=True);p.add_argument('--dqi-b',type=Path,required=True)
    p.add_argument('--chem-a',type=Path,required=True);p.add_argument('--chem-b',type=Path,required=True)
    p.add_argument('--metric',type=Path,required=True,help='Unmodified official metric source obtained from Kaggle')
    p.add_argument('--runtime',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    receipt_paths={'invsqrt':a.invsqrt,'dqi_a':a.dqi_a,'dqi_b':a.dqi_b,'chem_a':a.chem_a,'chem_b':a.chem_b}
    records={k:load(v) for k,v in receipt_paths.items()}
    for key,r in records.items():
        assert r['official_result']['status']=='PASS',key
        required=200540928 if key=='invsqrt' else 102400 if key.startswith('dqi') else 78080
        assert r['official_result']['verified_shots']==required,(key,'full-shot gate')
    assert records['dqi_a']['salt']!=records['dqi_b']['salt']
    assert records['chem_a']['salt']!=records['chem_b']['salt']
    files={'invsqrt.kmb':a.input/'invsqrt.kmb','dqi.kmb':a.input/'dqi.kmb'}
    for path in (a.input/'dfthcsos').glob('angle_k_*.kmb'):files['dfthcsos/'+path.name]=path
    files['dfthcsos/submission.npz']=a.input/'dfthcsos/submission.npz'
    assert len(files)==18
    for key,r in records.items():
        task='invsqrt' if key=='invsqrt' else 'dqi' if key.startswith('dqi') else 'chem'
        expected=file_hashes(r,task)
        for name,path in files.items():
            relevant=name.startswith('dfthcsos/') if task=='chem' else name==task+'.kmb'
            if relevant:assert sha(path)==expected[path.name],(key,name)
    a.output.mkdir(parents=True);archive=a.output/'submission.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,path in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.create_system=0;info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(stat.S_IFREG|0o644)<<16
            with path.open('rb') as src,z.open(info,'w',force_zip64=True) as dst:shutil.copyfileobj(src,dst,4*1024**2)
    unpacked=a.output/'reader-check';unpacked.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.namelist()==sorted(files) and z.testzip() is None
        for info in z.infolist():
            assert (unpacked/info.filename).resolve().is_relative_to(unpacked.resolve())
            z.extract(info,unpacked);assert sha(unpacked/info.filename)==sha(files[info.filename])
    sys.path.insert(0,str(a.runtime.resolve()))
    spec=importlib.util.spec_from_file_location('official_qvc_metric',a.metric);metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
    readers=[]
    for name in sorted(files):
        if not name.endswith('.kmb'):continue
        limit=1 if name=='invsqrt.kmb' else 4165 if name=='dqi.kmb' else 128
        c=metric.read_circuit(unpacked/name,limit)
        readers.append({'file':name,'qubits':c.num_qubits,'registers':c.num_registers,'status':'PASS'});del c;gc.collect()
    n=76
    arrays=metric.read_npz(unpacked/'dfthcsos/submission.npz',{'U':('f',('R','B',n)),'W':('f',('R','B','C')),'H2_I':('f',('R','C')),'H1_I':('f',()),'Hsym_lower':('f',(n*(n+1)//2,)),'tree_edges':('iu',(n-1,2))})
    baselines={'invsqrt':2076774.233715282,'dqi':24439463583672.93,'chem':3355599588.3155365}
    composites={salt:math.prod(baselines[task]/records[key]['official_result']['score'] for task,key in [('invsqrt','invsqrt'),('dqi','dqi_'+salt),('chem','chem_'+salt)])**(1/3) for salt in ('a','b')}
    report={'status':'PASS','scope':'18 exact files, full receipt-bound native checks and stock metric input readers; no Kaggle submission or eligibility certification','author':'Francisco Angulo de Lafuente','orcid':'https://orcid.org/0009-0001-1634-7063','archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'official_metric_sha256':sha(a.metric),'source_sha256':sha(Path(__file__)),'members':{name:{'sha256':sha(path),'bytes':path.stat().st_size} for name,path in files.items()},'official_readers':readers,'npz_shapes':{k:list(v.shape) for k,v in arrays.items()},'receipt_sha256':{k:sha(v) for k,v in receipt_paths.items()},'local_composite_indices':composites,'composite_scope':'Archived reference costs and recorded salts; not official scores or confidence bounds'}
    (a.output/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','archive_sha256','archive_bytes','local_composite_indices')}),flush=True)

if __name__=='__main__':main()
