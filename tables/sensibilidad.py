# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""How many word bits of a finished table actually matter?

Harm of moving word i by d steps, from the diagonal Gauss-Newton curvature: h_i d^2 in error_2^2.
Bits with negligible harm are don't-cares for the loaders, whose Toffolis follow the table's
GF(2) rank. Usage: sensibilidad.py <refit.npz>
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import sys

import numpy as np
import torch

torch.set_num_threads(8)
N = 76
ROOT = (_HOME + "/work/")
with np.load(sys.argv[1]) as d:
    words = d["angle_words"].astype(np.int64)
    W = d["W"].astype(float)
    brot = int(d["brot"])
    tree = d["tree_edges"].astype(int)
R, B, C = W.shape
n1 = len(words) - R * B
print("filas", len(words), "uno", n1, "brot", brot)
step = np.pi / 2 ** (brot - 1)
s = np.where(words >= 2 ** (brot - 1), words - 2 ** brot, words)
th = torch.tensor(s[n1:] * step, dtype=torch.float32)
w = torch.tensor(W, dtype=torch.float32)
ii, jj = np.triu_indices(N)
wgt = torch.tensor(np.where(ii == jj, 1.0, np.sqrt(2.0)), dtype=torch.float32)
G = torch.tensor(np.load(ROOT + "Gp.npy"), dtype=torch.float32)


def decode(t):
    v = [torch.zeros(t.shape[0]) for _ in range(N)]
    v[0] = torch.ones(t.shape[0])
    c, si = torch.cos(t), torch.sin(t)
    for e, (p, q) in enumerate(tree):
        a, b = v[p], v[q]
        v[p], v[q] = c[:, e] * a - si[:, e] * b, si[:, e] * a + c[:, e] * b
    return torch.stack(v, 1)


def chan(t):
    u = decode(t).reshape(R, B, N)
    S = u[:, :, ii] * u[:, :, jj] * wgt
    return torch.einsum("rbp,rbc->prc", S, w).reshape(-1, R * C)


t = th.clone().requires_grad_(True)
X = chan(t)
E = X.detach() @ X.detach().T - G
print("error_2", float(torch.linalg.vector_norm(E.double())))
Xd = X.detach()
c = torch.zeros_like(th)
P = 24
for k in range(P):
    V = torch.randn_like(G)
    V = V + V.T
    (g,) = torch.autograd.grad((X * (V @ Xd)).sum(), t, retain_graph=k < P - 1)
    c += g ** 2
c = (c / P / 2.0).numpy() * step ** 2      # symmetric V doubles the off-diagonal variance
u = decode(th).numpy()
h = c
print("h (mHa^2 por paso^2): mediana", np.median(h) * 1e6, "p90", np.quantile(h, .9) * 1e6, "p99", np.quantile(h, .99) * 1e6, "max", h.max() * 1e6)
print("presupuesto: error_2^2 =", 0.02 ** 2 * 1e6, "mHa^2")
o = np.sort(h.ravel())
cum = np.cumsum(o)
for tol in (1, 4, 10, 25, 50, 100):
    # random +-1 on the cheapest words adds tol mHa^2 to error_2^2
    n = np.searchsorted(cum, tol * 1e-6)
    print(f"bit bajo libre con +{tol} mHa2: {n/o.size:.3f} de las palabras (h hasta {o[min(n,o.size-1)]*1e6:.4f})")
for k in range(7):
    # zeroing the bits below bit k: mean square offset (4^k - 1) / 12 on those words
    f = (4 ** k - 1) / 12 if k else 0
    print("bits", k, "ofs2", f)
zero = (s[n1:] == 0)
print("palabras a cero", zero.mean(), "|palabra|<=1", (np.abs(s[n1:]) <= 1).mean(), "<=3", (np.abs(s[n1:]) <= 3).mean())
# harm of zeroing each word outright
hz = h * s[n1:].astype(float) ** 2
oz = np.sort(hz.ravel())
cz = np.cumsum(oz)
for tol in (1, 4, 10, 25, 50, 100):
    n = np.searchsorted(cz, tol * 1e-6)
    print(f"poner a cero con +{tol} mHa2: {n/oz.size:.3f} de las palabras")
# by column and by group: share of total sensitivity
hg = h.reshape(R, B, -1)
print("por grupo", np.round(hg.sum((1, 2)) / h.sum(), 3))
col = h.sum(0) / h.sum()
print("aristas con 50 % de la sensibilidad", int(np.searchsorted(np.cumsum(np.sort(col)[::-1]), .5)), "de", len(col))
blk = hg.reshape(R, -1) if False else None
pad = (-B) % 16
print("amplitudes: participacion media por fila", float((1 / (u ** 4).sum(1)).mean()))
np.savez("sens_845.npz", h=h, s=s[n1:])

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
