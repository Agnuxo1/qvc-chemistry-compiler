# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Fetch pinned public binaries with notices; this is NOT a circuit generator."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--archive',type=Path,help='Optional previously downloaded public dataset ZIP')
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'vendor/notices/gengsr/GENGSR_MANIFEST.json').read_text())
    a.output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='public-input-',dir=a.output) as temp:
        t=Path(temp)
        if a.archive is None:
            import kaggle
            kaggle.api.dataset_download_files('gengsr/vqcc-25-2268-portfolio',path=str(t),quiet=True,unzip=False)
        archive_path=a.archive or t/'vqcc-25-2268-portfolio.zip'
        with zipfile.ZipFile(archive_path) as outer:
            target_names={task+'.kmb' for task in ('invsqrt','dqi')}
            nested=next((n for n in outer.namelist() if Path(n).name==manifest['archive']['file']),None)
            if nested is not None:
                archive=t/'portfolio.zip'
                with outer.open(nested) as source,archive.open('wb') as target:shutil.copyfileobj(source,target)
                assert sha(archive)==manifest['archive']['sha256']
                chosen=zipfile.ZipFile(archive)
            else:chosen=outer
            try:
                for name in target_names:
                    member=next(n for n in chosen.namelist() if n==name or n.endswith('/'+name))
                    target=a.output/name
                    with chosen.open(member) as source,target.open('xb') as dest:shutil.copyfileobj(source,dest)
                    assert sha(target)==manifest['files'][name],f'Upstream target changed: {name}'
            finally:
                if chosen is not outer:chosen.close()
    for source in (root/'vendor/notices/gengsr').iterdir():shutil.copy2(source,a.output/source.name)
    print(json.dumps({'status':'PINNED_BINARIES_FETCHED','source_generators':False,'output':str(a.output)}))

if __name__=='__main__':main()
