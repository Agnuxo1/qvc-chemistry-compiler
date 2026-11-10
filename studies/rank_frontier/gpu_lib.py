# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Two-body model on GPU, in the packed symmetric basis.

X and the target are symmetric in (p, q), so with weight sqrt(2) on off-diagonal
pairs the Frobenius norm over N^2 x N^2 equals the one over 2926 x 2926: the
GEMMs are four times cheaper and the target takes 68 MB.
"""
import json, os, sys, time
import numpy as np
import torch

N = 76
ROOT = os.environ.get("QVC_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "work")).replace(chr(92), "/") + "/")
DEV = os.environ.get("QVC_DEV") or ("cuda" if torch.cuda.is_available() else "cpu")
DT = torch.float64


def pack_index():
    i, j = np.triu_indices(N)
    wgt = np.where(i == j, 1.0, np.sqrt(2.0))
    return i, j, wgt


def build_packed(tei, S):
    """Packed target from the chemist tensor and the fixed shift."""
    G = tei.copy()
    d = np.arange(N)
    G[:, :, d, d] += 0.5 * S[:, :, None]
    G[d, d, :, :] += 0.5 * S[None, :, :]
    i, j, wgt = pack_index()
    return (G[i, j][:, i, j] * wgt[:, None]) * wgt[None, :]


class GramLoss(torch.autograd.Function):
    """||X X^T - G||^2 with the two big GEMMs in FP32; the 3090 has 1/64 FP64 rate."""

    @staticmethod
    def forward(ctx, X, G32):
        X32 = X.float()
        E = X32 @ X32.T
        E -= G32
        ctx.save_for_backward(E, X32)
        return torch.linalg.vector_norm(E, dtype=torch.float64) ** 2

    @staticmethod
    def backward(ctx, g):
        E, X32 = ctx.saved_tensors
        return g * 4.0 * (E @ X32).double(), None


class Model:
    def __init__(self):
        c = np.load(ROOT + "chem_state.npz")
        self.tree = [(int(a), int(b)) for a, b in c["tree"]]
        self.Gp = torch.tensor(np.load(ROOT + "Gp.npy"), device=DEV, dtype=DT)
        i, j, wgt = pack_index()
        self.i = torch.tensor(i, device=DEV)
        self.j = torch.tensor(j, device=DEV)
        self.wgt = torch.tensor(wgt, device=DEV, dtype=DT)
        self.fast = os.environ.get("QVC_FP32") == "1"
        self.G32 = self.Gp.float() if self.fast else None

    def decode(self, th):
        """Unit vectors from angles (rows, N-1); parents precede children."""
        cols = {0: torch.ones(th.shape[0], device=th.device, dtype=th.dtype)}
        co, si = torch.cos(th), torch.sin(th)
        for t, (p, c) in enumerate(self.tree):
            a = cols[p]
            cols[p] = co[:, t] * a
            cols[c] = si[:, t] * a
        return torch.stack([cols[k] for k in range(N)], dim=1)

    def channels(self, th, w):
        """Packed channels (2926, R*C) from angles (R*B, N-1) and weights (R, B, C)."""
        R, B, C = w.shape
        u = self.decode(th)
        s = (u[:, self.i] * u[:, self.j] * self.wgt).reshape(R, B, -1)
        return torch.bmm(s.transpose(1, 2), w).permute(1, 0, 2).reshape(s.shape[2], R * C)

    def loss(self, th, w):
        X = self.channels(th, w)
        if self.fast:
            return GramLoss.apply(X, self.G32)
        E = X @ X.T - self.Gp
        return (E * E).sum()

    def error2(self, th, w):
        """Always FP64, so reported numbers do not depend on the fast path."""
        with torch.no_grad():
            X = self.channels(th, w)
            E = X @ X.T - self.Gp
            return float(torch.sqrt((E * E).sum()))

    def residual(self, th, w):
        with torch.no_grad():
            X = self.channels(th, w)
            return self.Gp - X @ X.T


def lbfgs(model, th, w, iters, every=200, tag="", wall=None, train_th=True):
    th = th.clone().requires_grad_(train_th)
    w = w.clone().requires_grad_(True)
    params = [th, w] if train_th else [w]
    opt = torch.optim.LBFGS(params, lr=1.0, max_iter=every, history_size=30,
                            tolerance_grad=1e-14, tolerance_change=1e-16, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        f = model.loss(th, w)
        f.backward()
        return f

    t0 = time.time()
    done = 0
    while done < iters:
        f = opt.step(closure)
        done += every
        e = model.error2(th.detach(), w.detach())
        print(f"{tag} iter {done} t={time.time()-t0:.0f}s error_2 {e:.6f}", flush=True)
        if wall and time.time() - t0 > wall:
            break
    return th.detach(), w.detach(), e


def grow_channels(model, th, w, extra):
    """Add `extra` channels per group from the top eigenvectors of the residual."""
    R, B, C = w.shape
    E = model.residual(th, w)
    ev, Q = torch.linalg.eigh(E)
    order = torch.argsort(ev, descending=True)
    u = model.decode(th)
    s = (u[:, model.i] * u[:, model.j] * model.wgt).reshape(R, B, -1)
    gram = torch.bmm(s, s.transpose(1, 2))
    gram += 1e-8 * gram.diagonal(dim1=1, dim2=2).mean(1)[:, None, None] * torch.eye(B, device=w.device, dtype=w.dtype)
    Lc = torch.linalg.cholesky(gram)
    slots = [extra] * R
    new = torch.zeros(R, B, extra, device=w.device, dtype=w.dtype)
    used = 0
    for k in order[: 4 * R * extra]:
        if used == R * extra or ev[k] <= 0:
            break
        x = torch.sqrt(ev[k]) * Q[:, k]
        rhs = torch.bmm(s, x.expand(R, -1)[:, :, None])
        coef = torch.cholesky_solve(rhs, Lc)[:, :, 0]
        fit = (coef * rhs[:, :, 0]).sum(1)
        for r in torch.argsort(fit, descending=True).tolist():
            if slots[r]:
                new[r, :, extra - slots[r]] = coef[r]
                slots[r] -= 1
                used += 1
                break
    return torch.cat([w, new], dim=2), ev[order[:8]].tolist(), float((ev * ev).sum().sqrt())


class Chem(Model):
    """Model plus the verifier's Lambda, E_gap and lambda_eff, differentiable."""
    ECORE, ETA, EUP = -21021.2140122, 113, -22140.27335
    GAP_FLOOR = 3.914898

    def __init__(self):
        super().__init__()
        c = np.load(ROOT + "chem_state.npz")
        self.beta1 = float(c["beta_1"])
        self.W0 = torch.tensor(c["W"], device=DEV, dtype=DT)
        S = c["S"].astype(np.float64)
        h1 = np.load(ROOT + "h1.npy")
        self.H1c = torch.tensor(h1 - 0.5 * self.ETA * S + self.beta1 * np.eye(N), device=DEV, dtype=DT)

    def costs(self, th, w, W):
        R, B, C = w.shape
        u = self.decode(th).reshape(R, B, N)
        a = torch.einsum("rbc,rc->rb", w, W)
        h1p = self.H1c - torch.einsum("rb,rbp,rbq->pq", a, u, u)
        ev = torch.linalg.eigvalsh(h1p)
        lam1 = ev.abs().sum()
        wB = W + w.sum(1)
        lam2 = 0.25 * ((w.abs().sum(1) + wB.abs()) ** 2).sum()
        Lam = lam1 + lam2
        esos = self.ECORE - self.ETA * self.beta1 - (lam1 - ev.sum()) - 0.5 * (W * W).sum()
        gap = self.EUP - esos
        return Lam, gap, torch.sqrt(gap * (2 * Lam - gap))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
