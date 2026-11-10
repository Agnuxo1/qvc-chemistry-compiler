# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Minimum or saddle? Lanczos on the FP64 Hessian at each stalled point.

Rotating the channels of a group changes nothing, so zero modes are expected; only a
clearly negative eigenvalue means a way out. Also a line search along -g, to see how much
the stall could still give. Usage: diag_hess.py <file.npz> [...]
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import os
import sys
import time

J1 = _os.environ.get("QVC_RUNS", _HOME + "/work/")
sys.path.insert(0, J1)
os.environ["QVC_ROOT"] = J1
os.environ["QVC_DEV"] = "cpu"
from gpu_lib import *  # noqa: E402
from scipy.sparse.linalg import LinearOperator, eigsh  # noqa: E402

torch.set_num_threads(int(os.environ.get("HILOS", "8")))
m = Model()
m.fast = False

for path in sys.argv[1:]:
    with np.load(path) as d:
        th0 = torch.tensor(d["th"], dtype=DT)
        w0 = torch.tensor(d["w"], dtype=DT)
    nt, nw = th0.numel(), w0.numel()
    p0 = torch.cat([th0.flatten(), w0.flatten()])

    def f(p):
        return m.loss(p[:nt].reshape(th0.shape), p[nt:].reshape(w0.shape))

    p = p0.clone().requires_grad_(True)
    t0 = time.time()
    val = f(p)
    (g,) = torch.autograd.grad(val, p, create_graph=True)
    gd = g.detach().clone()
    n = [0]

    def hv(v):
        n[0] += 1
        vt = torch.tensor(np.asarray(v).ravel(), dtype=DT)
        (h,) = torch.autograd.grad(g @ vt, p, retain_graph=True)
        return h.detach().numpy()

    print(os.path.basename(path), "f", float(val), "error_2", float(val) ** 0.5, "|g|", float(gd.norm()),
          "max|g|", float(gd.abs().max()), "n", p0.numel(), flush=True)
    top = gd.abs().topk(5)
    print("   mayores: indices", top.indices.tolist(), "(th hasta", nt, ")", flush=True)
    H = LinearOperator((p0.numel(), p0.numel()), matvec=hv, dtype=np.float64)
    hi = eigsh(H, k=1, which="LA", tol=1e-2, ncv=20, maxiter=40, return_eigenvectors=False)
    print("   mayor autovalor", hi, "mv", n[0], f"t={time.time()-t0:.0f}s", flush=True)
    sigma = float(hi[0]) * 1.01

    S = LinearOperator((p0.numel(), p0.numel()), matvec=lambda v: sigma * np.asarray(v).ravel() - hv(v), dtype=np.float64)
    try:
        lo, vec = eigsh(S, k=4, which="LA", tol=1e-3, ncv=120, maxiter=8)
    except Exception as e:                  # ArpackNoConvergence still returns the Ritz pairs found
        lo, vec = getattr(e, "eigenvalues", np.array([])), getattr(e, "eigenvectors", None)
        print("   sin convergencia completa", type(e).__name__, flush=True)
    print("   menores autovalores", sorted((sigma - lo).tolist()), "mv", n[0], f"t={time.time()-t0:.0f}s", flush=True)

    with torch.no_grad():
        best = (float(val), 0.0, "-g")
        for t in (1e-3, 1e-2, 1e-1, 1, 10, 100, 1e3, 1e4):
            v = float(f(p0 - t * gd))
            if v < best[0]:
                best = (v, t, "-g")
        if vec is not None and len(lo):
            d0 = torch.tensor(vec[:, int(np.argmax(lo))], dtype=DT)
            for t in (1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0):
                for s in (1, -1):
                    v = float(f(p0 + s * t * d0))
                    if v < best[0]:
                        best = (v, s * t, "curvatura")
    print("   mejor paso", best, "error_2", best[0] ** 0.5, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
