# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Staged rounding of a table to brot-bit words, resumable across short queue tickets.

Each stage freezes the angles whose rounding would hurt most (diagonal Gauss-Newton curvature
from random probes, times the squared offset), then refits the free angles and all weights by
L-BFGS. The schedule and the harm follow marculera's quantize.py (Apache-2.0). The tree decode
goes level by level, so an evaluation is a few dozen kernels and a ticket holds many stages.
Usage: redondeo.py <start.npz> <tag> <wall_s> [iters per stage] [bits]
Start holds (u, w) or (th, w); the state is red_<tag>.npz. Environment: QVC_DEV, HILOS, QVC_ROOT.
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
KAPPA = float(os.environ.get("QVC_KAPPA", "5e-5"))
CHUNK = int(os.environ.get("QVC_CHUNK", "250"))
start, tag, WALL = sys.argv[1], sys.argv[2], float(sys.argv[3])
ITERS = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
BITS = int(sys.argv[5]) if len(sys.argv) > 5 else 8
step = np.pi / 2 ** (BITS - 1)
SCHED = [.0005, .001, .002, .003, .004, .005, .007, .009, .011, .014, .017, .02, .025, .03, .035, .04, .045, .05, .06,
         .07, .08, .09, .1, .12, .14, .16, .18, .205, .23, .255, .28, .31, .34, .37, .4, .43, .46, .49, .52, .55, .58,
         .61, .64, .67, .7, .725, .75, .775, .8, .84, .88, .91, .935, .955, .97, .98, .988, .994, 1.0]



def log_depth_tree(n=N):
    """Breadth-first edges of the log-depth binary tree, the one the verifier's example and the public chain use."""
    edges, level, depth = [], [0], 0
    while len(edges) < n - 1:
        nxt = []
        for label in level:
            nxt.append(label)
            right = label + (1 << depth)
            if right < n:
                edges.append((label, right))
                nxt.append(right)
        level, depth = nxt, depth + 1
    return np.asarray(edges, dtype=np.int64)


tree = np.load(os.environ["QVC_TREE"]).astype(np.int64) if os.environ.get("QVC_TREE") else log_depth_tree()   # any tree rooted at 0, parents first
G = torch.tensor(np.load(ROOT + "Gp.npy"), device=DEV, dtype=torch.float64)
G32 = G.float()


def levels():
    runs, cur, used = [], [], set()
    for t, (p, q) in enumerate(tree):
        if p in used or q in used:
            runs.append(cur)
            cur, used = [], set()
        cur.append(t)
        used.update((int(p), int(q)))
    return runs + [cur]


LV = [(torch.tensor(ts, device=DEV), torch.tensor(tree[ts, 0], device=DEV), torch.tensor(tree[ts, 1], device=DEV))
      for ts in levels()]


def decode(th):
    """Unit rows from angles; a child is still zero when its edge is reached."""
    u = torch.zeros(th.shape[0], N, device=th.device, dtype=th.dtype)
    u[:, 0] = 1.0
    c, s = torch.cos(th), torch.sin(th)
    for ts, p, q in LV:
        up = u[:, p]
        v = u.clone()
        v[:, p] = c[:, ts] * up
        v[:, q] = s[:, ts] * up
        u = v
    return u


def channels(th, w, dt):
    R, B, C = w.shape
    return Canales.apply(decode(th.to(dt)).reshape(R, B, N), w.to(dt))


def D(w):
    return 0.5 * (w.abs().sum(1) ** 2 - w.sum(1) ** 2).sum()


def err(th, w):
    with torch.no_grad():
        X = channels(th, w, torch.float64)
        return float(torch.linalg.vector_norm(X @ X.T - G))


def curvature(th, w, probes=8):
    """E[(d<dM, V>/d theta)^2] = sum (dM/d theta)^2 for V with unit normal entries."""
    t = th.clone().requires_grad_(True)
    X = channels(t, w, torch.float32)
    out = torch.zeros_like(th)
    for k in range(probes):
        V = torch.randn(G32.shape, device=th.device, dtype=torch.float32)
        V = V + V.T
        (g,) = torch.autograd.grad((X * (V @ X.detach())).sum(), t, retain_graph=k < probes - 1)
        out += g ** 2
    return out / probes


CODES = os.environ.get("QVC_CODES", "")   # e.g. 0:1:3-14: bit 0 of batches 3-14 stays in RM(1,4) per block
if CODES:
    sys.path.insert(0, os.environ.get("QVC_RM", (_os.environ.get("QVC_PIPELINE", _HOME + "/third_party/public_pipeline") + "/dfthc_refit/experiments")))
    import rmcode
    deg = rmcode.parse(CODES, N - 1, BITS)
    ccols = np.flatnonzero(deg.any(axis=1))
# Codes above bit 0: the final gauge fix negates words, which flips those bits, so every angle stays in the signed gauge
# from the start, wrapped half a step early as in the public quantize_rm.py --open (a hard wall at +-1/2 costs far more).
GAUGED = bool(CODES) and bool(deg[:, 1:].any())
SC = 2 ** (BITS - 1)
LO, HI = -SC / 2 - 0.5, SC / 2 - 0.5 - 1e-6

st = HERE + f"red_{tag}.npz"
if os.path.exists(st):
    with np.load(st) as d:
        z, w = torch.tensor(d["z"], device=DEV), torch.tensor(d["w"], device=DEV)
        fr, qv, stage, inner = torch.tensor(d["fr"], device=DEV), torch.tensor(d["qv"], device=DEV), int(d["stage"]), int(d["inner"])
else:
    with np.load(start) as d:
        w = torch.tensor(d["w"], device=DEV, dtype=torch.float64)
        if "th" in d.files:
            th0 = torch.tensor(d["th"], device=DEV, dtype=torch.float64)
        else:
            raise SystemExit("start needs angles: conv.py")
    z = th0 / step
    if GAUGED:
        z = torch.tensor(rmcode.gauge_angles(z.cpu().numpy() / SC, tree, 0.5 / SC) * SC, device=DEV).clamp(LO, HI)
    fr = torch.zeros_like(z, dtype=torch.bool)
    qv = torch.zeros_like(z)
    stage, inner = -1, 0

SIGNO = os.environ.get("QVC_SIGNO") == "1"   # H13: every channel keeps one sign, so D = 0 by construction
S = torch.sign(w.sum(1, keepdim=True))
S[S == 0] = 1.0


def recorta(x):
    """Weights against the sign of their channel count as zero; one at zero keeps its gradient and can come back."""
    return torch.where(x * S >= 0, x, torch.zeros_like(x))


if SIGNO:
    w = recorta(w)


def save():
    tmp = st + ".tmp.npz"
    np.savez(tmp, z=z.cpu().numpy(), w=w.cpu().numpy(), fr=fr.cpu().numpy(), qv=qv.cpu().numpy(), stage=stage, inner=inner)
    os.replace(tmp, st)


def angles(zf):
    return torch.where(fr, qv, zf.clamp(LO, HI) if GAUGED else zf) * step


def freeze(frac):
    need = int(round(frac * z.numel())) - int(fr.sum())
    if need <= 0:
        return
    th = angles(z)
    c = curvature(th, w)
    cur = torch.where(fr, qv, z)
    q = torch.round(cur)
    if CODES:
        # codewords stay open until frozen entries pin them down, as in the public quantize_rm.py --open
        t = cur.cpu().numpy()[:, ccols]
        addr = N + np.arange(z.shape[0])
        r, m = rmcode.residues(t, c.cpu().numpy()[:, ccols].astype(np.float64), addr // 16, addr % 16, deg[ccols],
                               fr.cpu().numpy()[:, ccols], np.round(qv.cpu().numpy()[:, ccols]).astype(np.int64),
                               SC if GAUGED else None)
        v = rmcode.residue_round(t, r, m)
        q[:, ccols] = torch.tensor(rmcode.into_gauge(v, m, SC) if GAUGED else v, device=q.device, dtype=q.dtype)
    harm = c * (q - cur) ** 2 * step ** 2
    harm[fr] = -1.0
    pick = torch.topk(harm.flatten(), need).indices
    fr.view(-1)[pick] = True
    qv.view(-1)[pick] = q.view(-1)[pick]


SCALE = os.environ.get("QVC_SCALE", "1") == "1"
VERB = os.environ.get("QVC_VERB") == "1"


def scales(th):
    """Diagonal preconditioner: word sensitivities span five orders of magnitude, which stalls plain L-BFGS."""
    t = th.clone().requires_grad_(True)
    ww = w.float().clone().requires_grad_(True)
    X = channels(t, ww, torch.float32)
    cz, cw = torch.zeros_like(th), torch.zeros_like(w)
    P = 4
    for k in range(P):
        V = torch.randn(G32.shape, device=th.device, dtype=torch.float32)
        V = V + V.T
        g1, g2 = torch.autograd.grad((X * (V @ X.detach())).sum(), (t, ww), retain_graph=k < P - 1)
        cz += g1.double() ** 2
        cw += g2.double() ** 2
    cz, cw = (cz / P) * step ** 2, cw / P
    fl = float(os.environ.get("QVC_FLOOR", "1e-4"))
    sz = 1.0 / torch.sqrt(cz + fl * cz.mean())
    sw = 1.0 / torch.sqrt(cw + fl * cw.mean())
    m = 1.0 / sz.median()
    return sz * m, sw * m


def refit(iters):
    global z, w
    a0, b0 = z.clone(), w.clone()
    sz, sw = scales(angles(z)) if SCALE else (torch.ones_like(z), torch.ones_like(w))
    za = torch.zeros_like(z, requires_grad=True)
    wa = torch.zeros_like(w, requires_grad=True)
    opt = torch.optim.LBFGS([za, wa], lr=1.0, max_iter=CHUNK, history_size=30, tolerance_grad=1e-13,
                            tolerance_change=1e-15, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        wf = b0 + sw * wa
        if SIGNO:
            wf = recorta(wf)
        f = Gram.apply(channels(angles(a0 + sz * za), wf, torch.float32), G32) + KAPPA * D(wf)
        f.backward()
        return f

    n = 0
    while n < iters and time.time() - t0 < WALL:
        opt.step(closure)
        n += CHUNK
        if VERB:
            print(n, f"{err(angles(a0 + sz * za.detach()), b0 + sw * wa.detach()):.6f}", f"{time.time()-t0:.0f}s", flush=True)
    z, w = a0 + sz * za.detach(), b0 + sw * wa.detach()
    if SIGNO:
        w = recorta(w)
    if GAUGED:
        z = z.clamp(LO, HI)
    return n


t0 = time.time()
print(tag, "continuo o estado", err(angles(z), w), "etapa", stage, "fijadas", float(fr.float().mean()), flush=True)
while time.time() - t0 < WALL:
    if inner <= 0:
        stage += 1
        if stage >= len(SCHED):
            break
        e0 = err(angles(z), w)
        freeze(SCHED[stage])
        e1 = err(angles(z), w)
        inner = ITERS
    else:
        e0 = e1 = float("nan")
    inner -= refit(inner)
    e2 = err(angles(z), w)
    if inner <= 0:
        print(f"etapa {stage} fijadas {float(fr.float().mean()):.4f} error_2 {e1:.5f} -> {e2:.5f} D {float(D(w)):.2f} t={time.time()-t0:.0f}s", flush=True)
    save()
if stage >= len(SCHED):
    w0 = err(angles(z), w)
    print("fin", tag, "error_2", w0, "enteras", bool(fr.all()), flush=True)
    with open(HERE + "redondeo.jsonl", "a") as f:
        f.write(json.dumps(dict(tag=tag, error_2=w0, iters=ITERS, t=time.strftime("%Y-%m-%d %H:%M"))) + "\n")

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
