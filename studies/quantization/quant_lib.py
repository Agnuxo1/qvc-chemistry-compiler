# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Hessian-weighted word quantization for the dfthcsos angle table.

The two-body model is M = sum_l x_l x_l^T with x_l = vec X^(l). Moving row i of
group rho by du changes M by v g^T + g v^T, with v = vec(du u^T + u du^T) and
g = vec(Gamma_i), Gamma_i = sum_c w[rho,i,c] X^(rho c). Hence, for two moves,

    <dM_i, dM_j> = 2 (v_i . v_j)(g_i . g_j) + 2 (v_i . g_j)(g_i . v_j),

which gives the Gauss-Newton Hessian of error_2^2 in word units without ever
forming an N^2 x N^2 Jacobian.
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import os

import numpy as np

N = 76
ROOT = os.environ.get("QVC_ROOT", (_HOME + "/work/"))


def load():
    d = np.load(ROOT + "chem_state.npz")
    tei = np.load(ROOT + "tei.npy")
    return dict(words=d["words"], tree=d["tree"], w=d["w"], W=d["W"], S=d["S"],
                brot=int(d["brot"])), tei


def decode(theta, tree):
    """Unit vectors from angles in radians, shape (rows, N-1) -> (rows, N)."""
    v = np.zeros((theta.shape[0], N))
    v[:, 0] = 1.0
    for t, (p, c) in enumerate(tree):
        a, b = v[:, p].copy(), v[:, c].copy()
        co, si = np.cos(theta[:, t]), np.sin(theta[:, t])
        v[:, p] = co * a - si * b
        v[:, c] = si * a + co * b
    return v


def decode_jac(theta, tree):
    """Vectors and their angle Jacobian, shapes (rows, N) and (rows, N-1, N)."""
    rows, E = theta.shape
    v = np.zeros((rows, N))
    v[:, 0] = 1.0
    D = np.zeros((rows, E, N))
    for t, (p, c) in enumerate(tree):
        co, si = np.cos(theta[:, t]), np.sin(theta[:, t])
        a, b = v[:, p].copy(), v[:, c].copy()
        da, db = D[:, :, p].copy(), D[:, :, c].copy()
        D[:, :, p] = co[:, None] * da - si[:, None] * db
        D[:, :, c] = si[:, None] * da + co[:, None] * db
        D[:, t, p] = -si * a - co * b
        D[:, t, c] = co * a - si * b
        v[:, p] = co * a - si * b
        v[:, c] = si * a + co * b
    return v, D


def target(tei, S):
    """G with M - G the two-body residual, as an N^2 x N^2 matrix."""
    G = tei.copy()
    d = np.arange(N)
    G[:, :, d, d] += 0.5 * S[:, :, None]
    G[d, d, :, :] += 0.5 * S[None, :, :]
    return G.reshape(N * N, N * N)


def channels(u, w):
    """X^(rho c) as an (N^2, R*C) matrix; u is (R, B, N), w is (R, B, C)."""
    X = np.einsum("rbp,rbq,rbc->rcpq", u, u, w, optimize=True)
    return X.reshape(-1, N * N).T.copy()


def error2(u, w, G):
    Xm = channels(u, w)
    E = Xm @ Xm.T
    E -= G
    return float(np.linalg.norm(E)), E, Xm


def group_hessian(u, D, w_g, X_g, step):
    """Gauss-Newton Hessian of ||dM||^2 for one group, in word units.

    u (B, N), D (B, E, N), w_g (B, C), X_g (N^2, C). Returns H (B*E, B*E).
    """
    B, E, _ = D.shape
    Gam = (X_g @ w_g.T).T.reshape(B, N, N)          # Gamma_i
    P = np.einsum("ipq,jpq->ij", Gam, Gam, optimize=True)
    Dm = (D * step).reshape(B * E, N)
    UU = u @ u.T
    Du = Dm @ u.T                                    # (B*E, B): D_ik . u_j
    T = np.einsum("jpq,iq->ijp", Gam, u, optimize=True)   # Gamma_j u_i
    K = 2.0 * np.einsum("ikp,ijp->ikj", D * step, T, optimize=True).reshape(B * E, B)
    H = np.empty((B * E, B * E))
    for i in range(B):                               # row blocks keep the peak near one H
        a = slice(i * E, (i + 1) * E)
        for j in range(B):
            c = slice(j * E, (j + 1) * E)
            blk = (Dm[a] @ Dm[c].T) * UU[i, j]
            blk += np.outer(Du[a, j], Du[c, i])
            blk *= 4.0 * P[i, j]
            blk += 2.0 * np.outer(K[a, j], K[c, i])
            H[a, c] = blk
    return H


def group_hessian_free(u, D, w_g, X_g, step, free):
    """group_hessian restricted to the free words, sorted by ascending diagonal.

    Only the sorted free block is allocated, so the peak falls as words freeze.
    Returns the block, the sorted natural indices and their diagonal.
    """
    B, E, _ = D.shape
    Gam = (X_g @ w_g.T).T.reshape(B, N, N)
    P = np.einsum("ipq,jpq->ij", Gam, Gam, optimize=True)
    Dm = (D * step).reshape(B * E, N)
    UU = u @ u.T
    Du = Dm @ u.T
    T = np.einsum("jpq,iq->ijp", Gam, u, optimize=True)
    K = 2.0 * np.einsum("ikp,ijp->ikj", D * step, T, optimize=True).reshape(B * E, B)
    row = np.repeat(np.arange(B), E)
    n = np.arange(B * E)
    d = 4.0 * ((Dm * Dm).sum(1) * UU[row, row] + Du[n, row] ** 2) * P[row, row] + 2.0 * K[n, row] ** 2
    o = free[np.argsort(d[free])]
    rank = np.full(B * E, -1)
    rank[o] = np.arange(o.size)
    H = np.empty((o.size, o.size))
    sel = [np.flatnonzero(rank[i * E:(i + 1) * E] >= 0) + i * E for i in range(B)]
    for i in range(B):
        a = sel[i]
        if a.size == 0:
            continue
        for j in range(B):
            c = sel[j]
            if c.size == 0:
                continue
            blk = (Dm[a] @ Dm[c].T) * UU[i, j]
            blk += np.outer(Du[a, j], Du[c, i])
            blk *= 4.0 * P[i, j]
            blk += 2.0 * np.outer(K[a, j], K[c, i])
            H[np.ix_(rank[a], rank[c])] = blk
    return H, o, d[o]


def group_gradient(u, D, w_g, X_g, Emat, step):
    """Half gradient of ||E + dM||^2 for one group: b_ik = <E, dM_ik>, word units."""
    B, Ed, _ = D.shape
    Gam = (X_g @ w_g.T)                               # (N^2, B)
    EG = (Emat @ Gam).T.reshape(B, N, N)              # E g_i
    EGs = EG + EG.transpose(0, 2, 1)
    Y = np.einsum("ipq,iq->ip", EGs, u, optimize=True)
    return 2.0 * np.einsum("ikp,ip->ik", D * step, Y, optimize=True).reshape(-1)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
