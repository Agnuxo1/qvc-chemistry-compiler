# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Packed channels with an analytic backward pass.

Indexing u[:, :, i] * u[:, :, j] makes autograd scatter 3 million entries per evaluation. Here
L_rc = sum_b w_rbc u_b u_b^T comes from batched products and only the small packed copy is
gathered; the backward pass unpacks that copy and uses du_rb = 2 sum_c w_rbc Y_rc u_rb.
"""
import numpy as np
import torch

N = 76
_ii, _jj = np.triu_indices(N)
_w = np.where(_ii == _jj, 1.0, np.sqrt(2.0))
_cache = {}


def pack(device, dtype):
    k = (str(device), dtype)
    if k not in _cache:
        _cache[k] = (torch.tensor(_ii, device=device), torch.tensor(_jj, device=device),
                     torch.tensor(_w, device=device, dtype=dtype))
    return _cache[k]


class Canales(torch.autograd.Function):
    """X (P, R*C) from unit vectors u (R, B, N) and weights W (R, B, C)."""

    @staticmethod
    def forward(ctx, u, W):
        R, B, C = W.shape
        i, j, wg = pack(u.device, u.dtype)
        Wt = W.transpose(1, 2)
        A = Wt[:, :, :, None] * u[:, None, :, :]                       # (R, C, B, N)
        L = torch.matmul(A.transpose(2, 3), u[:, None])                # (R, C, N, N)
        ctx.save_for_backward(u, W)
        return (L.reshape(R * C, N, N)[:, i, j] * wg).T.contiguous()

    @staticmethod
    def backward(ctx, g):
        u, W = ctx.saved_tensors
        R, B, C = W.shape
        i, j, wg = pack(u.device, u.dtype)
        gw = g.T * wg
        Y = torch.zeros(R * C, N, N, device=u.device, dtype=u.dtype)
        Y[:, i, j] = gw
        Y = 0.5 * (Y + Y.transpose(1, 2))                              # diagonal: gw, off-diagonal: gw / 2 each side
        T = torch.matmul(u[:, None], Y.reshape(R, C, N, N))            # (R, C, B, N)
        dW = (T * u[:, None]).sum(-1).transpose(1, 2)
        dU = 2.0 * (W.transpose(1, 2)[:, :, :, None] * T).sum(1)
        return dU, dW


class Gram(torch.autograd.Function):
    """|X X^T - G| for a fixed target."""

    @staticmethod
    def forward(ctx, X, G):
        E = X @ X.T
        E -= G
        n = torch.linalg.vector_norm(E, dtype=torch.float64)
        ctx.save_for_backward(E, X)
        ctx.n = n
        return n

    @staticmethod
    def backward(ctx, g):
        E, X = ctx.saved_tensors
        return ((2.0 * g / ctx.n).to(X.dtype)) * (E @ X), None

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
