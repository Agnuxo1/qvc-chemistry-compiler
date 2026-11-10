# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Tail of the chain: refine, refit, compile and verify a rounded table.

Runs the public finish_rm.py (marculera, Apache-2.0) with our decoder module in place of the
one that needs the starter kit. Usage: cola.py ROUNDED.npz OUTDIR [finish_rm options]
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + "/entorno")
import quantize  # noqa: E402,F401  (cached, so later imports find this one)

PIPE = (_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/dfthc_refit/experiments/finish_rm.py")
if __name__ == "__main__":
    sys.argv[0] = PIPE
    runpy.run_path(PIPE, run_name="__main__")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
