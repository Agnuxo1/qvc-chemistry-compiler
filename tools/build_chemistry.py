# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Rebuild all 16 frozen chemistry files, asserting exact source/output hashes."""
from pathlib import Path
import argparse
from reconstruir_quimica import rebuild

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--recipe',type=Path,default=Path(__file__).resolve().parents[1]/'recipes/s37')
    a=p.parse_args()
    rebuild(a.recipe.resolve(),a.output.resolve(),a.data.resolve(),a.runtime.resolve())

if __name__=='__main__': main()
