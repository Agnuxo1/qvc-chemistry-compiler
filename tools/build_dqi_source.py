# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Build the credited source-complete 888Q alternative; not selected e9f54be3."""
from pathlib import Path
import argparse
import hashlib
import os
import subprocess
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--runtime',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    root=Path(__file__).resolve().parents[1]
    generator=root/'vendor/dqi888/rebuild_dqi.py'
    env=dict(os.environ,PYTHONPATH=str(a.runtime.resolve()),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    subprocess.run([sys.executable,str(generator),'--policy','repair','--runtime','stock','--out',str(a.output.resolve())],env=env,check=True)
    with (a.output/'dqi.kmb').open('rb') as f:value=hashlib.file_digest(f,'sha256').hexdigest()
    assert value=='736f3055850794c6beaedf8de5f7dafa1c270e2b57edd403ffa96abf6d207741'
    print('Exact source-built 888Q alternative; full native receipts are recorded separately.')

if __name__=='__main__':main()
