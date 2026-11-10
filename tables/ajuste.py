# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Fit one table on the GPU with free vectors, for a short queue ticket.

The tree decode launched about 1,500 small kernels per evaluation, so the 3090 sat idle at
21-26 ms. Vectors stay free here, as in the public pipeline; angles only appear at rounding.
Objective: error_2 + kappa D(w), big products in FP32, reported error in FP64.
Usage: ajuste.py <RxBxC> <wall_s> [lbfgs|adam] [lr0 lr1 total_steps]
"""
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")).replace("\\", "/")
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rapido import Canales, Gram

torch.set_num_threads(int(os.environ.get("HILOS", "4")))
N = 76
HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
ROOT = os.environ.get("QVC_ROOT", (_HOME + "/work/"))
DEV = os.environ.get("QVC_DEV", "cuda")
CHUNK = int(os.environ.get("QVC_CHUNK", "500"))
KAPPA = float(os.environ.get("QVC_KAPPA", "5e-5"))
shape, WALL = sys.argv[1], float(sys.argv[2])
MODE = sys.argv[3] if len(sys.argv) > 3 else "lbfgs"
G = torch.tensor(np.load(ROOT + "Gp.npy"), device=DEV, dtype=torch.float64)
G32 = G.float()

DTF = torch.float64 if os.environ.get("QVC_F64") == "1" else torch.float32
state = HERE + f"fit_{shape}.npz"
src = state if os.path.exists(state) else HERE + f"seed_{shape}.npz"
with np.load(src) as d:
    U = torch.tensor(d["u"], device=DEV, dtype=torch.float64)
    W = torch.tensor(d["w"], device=DEV, dtype=torch.float64)
    step0 = int(d["step"]) if "step" in d.files else 0
R, B, C = W.shape
SIGNO = os.environ.get("QVC_SIGNO") == "1"   # H13: every channel keeps one sign, so D = 0 by construction
S = torch.sign(W.sum(1, keepdim=True))
S[S == 0] = 1.0


def recorta(W):
    """Weights against the sign of their channel go to zero; a zero weight can come back with the right sign."""
    return torch.where(W * S > 0, W, torch.zeros_like(W))


if SIGNO:
    W = recorta(W)


def channels(U, W, dt):
    return Canales.apply((U / U.norm(dim=2, keepdim=True)).to(dt), W.to(dt))


def D(W):
    return 0.5 * (W.abs().sum(1) ** 2 - W.sum(1) ** 2).sum()


SIGMA = float(os.environ.get("QVC_SIGMA", "0"))     # noise on the vectors during the fit: a table that tolerates rounding (H11)


def objective(U, W):
    V = U + SIGMA * torch.randn_like(U) if SIGMA > 0 else U
    return Gram.apply(channels(V, W, DTF), G32 if DTF == torch.float32 else G) + KAPPA * D(W)


def err(U, W):
    with torch.no_grad():
        X = channels(U, W, torch.float64)
        return float(torch.linalg.vector_norm(X @ X.T - G))


def save(U, W, step):
    tmp = state + ".tmp.npz"
    np.savez(tmp, u=U.detach().cpu().numpy(), w=W.detach().cpu().numpy(), step=step)
    os.replace(tmp, state)


def mejor(U, W, step, e):
    """Lowest error seen in a schedule: Adam's current point wanders above it while the rate is high."""
    path = HERE + f"mejor_{shape}.npz"
    if os.path.exists(path):
        with np.load(path) as d:
            if float(d["e"]) <= e:
                return
    tmp = path + ".tmp.npz"
    np.savez(tmp, u=U.detach().cpu().numpy(), w=W.detach().cpu().numpy(), step=step, e=e)
    os.replace(tmp, path)


def scales(U, W):
    """Diagonal preconditioner from probes: entries differ by orders of magnitude and plain L-BFGS stalls."""
    a, b = U.detach().clone().requires_grad_(True), W.detach().clone().requires_grad_(True)
    X = channels(a, b, torch.float32)
    cu, cw = torch.zeros_like(U), torch.zeros_like(W)
    P = 4
    for k in range(P):
        V = torch.randn(G32.shape, device=U.device, dtype=torch.float32)
        V = V + V.T
        g1, g2 = torch.autograd.grad((X * (V @ X.detach())).sum(), (a, b), retain_graph=k < P - 1)
        cu += g1 ** 2
        cw += g2 ** 2
    fl = float(os.environ.get("QVC_FLOOR", "1e-4"))
    su = 1.0 / torch.sqrt(cu / P + fl * (cu / P).mean())
    sw = 1.0 / torch.sqrt(cw / P + fl * (cw / P).mean())
    m = 1.0 / su.median()
    return su * m, sw * m


BLOCK = int(os.environ.get("QVC_BLOCK", "2000"))
SCALE = os.environ.get("QVC_SCALE", "1") == "1"
e0 = err(U, W)
best, t0, done = e0, time.time(), 0
stale = 0
print(shape, "inicio", e0, "D", float(D(W)), flush=True)
if MODE == "lbfgs":
    while time.time() - t0 < WALL:
        su, sw = scales(U, W) if SCALE else (torch.ones_like(U), torch.ones_like(W))
        a = torch.zeros_like(U, requires_grad=True)
        b = torch.zeros_like(W, requires_grad=True)
        opt = torch.optim.LBFGS([a, b], lr=1.0, max_iter=CHUNK, history_size=30, tolerance_grad=1e-12,
                                tolerance_change=1e-14, line_search_fn="strong_wolfe")

        def closure():
            opt.zero_grad()
            f = objective(U + su * a, W + sw * b)
            f.backward()
            return f

        n = 0
        while n < BLOCK and time.time() - t0 < WALL:
            opt.step(closure)
            n += CHUNK
        done += n
        U, W = (U + su * a).detach(), (W + sw * b).detach()
        e = err(U, W)
        print(f"{done} t={time.time()-t0:.0f}s error_2 {e:.6f} D {float(D(W)):.3f}", flush=True)
        stale = stale + 1 if best - e < 1e-7 else 0
        if e < best:
            best = e
            save(U, W, step0)
        if stale >= 2:                      # the line search has stopped moving: give the GPU to the next job
            print("L-BFGS parado", flush=True)
            break
else:
    U.requires_grad_(True)
    W.requires_grad_(True)
    lr0, lr1, total = float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
    opt = torch.optim.Adam([U, W], lr=lr0)
    moments = HERE + f"adam_{shape}.pt"       # a long schedule spans many tickets: moments and the current point carry over
    if os.path.exists(moments):
        opt.load_state_dict(torch.load(moments, map_location=DEV))
    step = step0
    while time.time() - t0 < WALL and step < total:
        for g in opt.param_groups:
            g["lr"] = lr0 * (lr1 / lr0) ** (step / total)
        for _ in range(200):
            opt.zero_grad(set_to_none=True)
            objective(U, W).backward()
            opt.step()
            if SIGNO:
                with torch.no_grad():
                    W.copy_(recorta(W))
        step += 200
        done += 200
        if done % 10000 == 0:
            e = err(U.detach(), W.detach())
            print(f"{step} t={time.time()-t0:.0f}s error_2 {e:.6f} D {float(D(W)):.3f}", flush=True)
            mejor(U, W, step, e)
e = err(U.detach(), W.detach())
if MODE == "adam":
    best = min(best, e)
    mejor(U, W, step, e)
    save(U, W, step)
    torch.save(opt.state_dict(), moments)
elif e < best:
    best = e
    save(U, W, step0)
rate = done / max(time.time() - t0, 1e-9)
print(json.dumps(dict(forma=shape, modo=MODE, antes=e0, despues=best, pasos=done, por_s=round(rate, 1))), flush=True)
with open(HERE + "ajuste.jsonl", "a") as f:
    f.write(json.dumps(dict(forma=shape, modo=MODE, antes=e0, despues=best, pasos=done, por_s=round(rate, 1), t=time.strftime("%Y-%m-%d %H:%M"))) + chr(10))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
