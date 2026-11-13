"""Isolated launcher for the pinned official verifiers and reviewed local code.

SPDX-License-Identifier: Apache-2.0
Only authenticated competition directories are added; never input ZIP code.
"""
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path[:0] = [str(root / 'data/comp/kickmix'), str(root / 'data/comp/verifiers')]
target = Path(sys.argv[1]).resolve()
sys.argv = [str(target), *sys.argv[2:]]
runpy.run_path(str(target), run_name='__main__')
