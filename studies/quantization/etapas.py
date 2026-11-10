# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Staged Babai quantization: freeze the most sensitive words, reoptimize the rest.

Each stage commits part of each group through Babai back-substitution, gives the
still-free words their exact conditional optimum, then polishes free angles and
all weights with L-BFGS. Reference at brot 7: one-shot Babai 0.0622, public 0.11.
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
import scipy.linalg as sl
from scipy.optimize import minimize
from quant_lib import *

BITS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
ALPHA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
POLISH = int(sys.argv[3]) if len(sys.argv) > 3 else 30
TAG = sys.argv[4] if len(sys.argv) > 4 else f"b{BITS}"
FRACS = [.30, .50, .65, .75, .82, .87, .91, .94, .96, .975, .985, .992, 1.0]
if TAG.endswith("fino"):                     # the first stages set the plateau in the b7 run
    FRACS = [.05 * k for k in range(1, 20)] + [.98, 1.0]

st, tei = load()
G = target(tei, st["S"])
del tei
tree, brot = st["tree"], st["brot"]
R, B, C = st["w"].shape
E_ = N - 1
step = np.pi / 2 ** (BITS - 1)
p0 = np.load(ROOT + os.environ.get("QVC_START", "piloto4_p.npy"))
nth = R * B * E_
z = p0[:nth].reshape(R * B, E_) / step
w = p0[nth:].reshape(R, B, C).copy()
frozen = np.zeros(z.shape, bool)
t0 = time.time()

# Words of the least sensitive edges keep their low bit at zero for every row, so
# that loader output bit vanishes: a fractional brot without changing the registers.
even = np.zeros(z.shape, bool)
EVENF = float(os.environ.get("QVC_EVEN", "0"))
if EVENF > 0:
    sens = np.zeros(E_)
    X0 = channels(decode(z * step, tree).reshape(R, B, N), w)
    for r in range(R):
        rows = slice(r * B, (r + 1) * B)
        _, D = decode_jac(z[rows] * step, tree)
        g2 = ((X0[:, r * C:(r + 1) * C] @ w[r].T) ** 2).sum(0)
        sens += (g2[:, None] * (D * D).sum(2)).sum(0)
    del X0
    cols = np.argsort(sens)[:int(round(EVENF * E_))]
    even[:, cols] = True
    print("aristas con bit bajo a cero", cols.size, "de", E_, "peso", sens[cols].sum() / sens.sum(), flush=True)


def fg_factory(free):
    idx = np.flatnonzero(free.ravel())

    def fg(p):
        zz = z.ravel().copy()
        zz[idx] = p[:idx.size]
        ww = p[idx.size:].reshape(R, B, C)
        u, D = decode_jac(zz.reshape(R * B, E_) * step, tree)
        u3 = u.reshape(R, B, N)
        Xm = channels(u3, ww)
        E = Xm @ Xm.T
        E -= G
        f = float((E * E).sum())
        EX = (E @ Xm).reshape(N, N, R, C)
        EXs = EX + EX.transpose(1, 0, 2, 3)
        gw = 2.0 * np.einsum("rbp,rbq,pqrc->rbc", u3, u3, EXs, optimize=True)
        Y = np.einsum("pqrc,rbc,rbq->rbp", EXs, ww, u3, optimize=True)
        gz = 4.0 * step * np.einsum("ikp,ip->ik", D, Y.reshape(R * B, N), optimize=True)
        return f, np.concatenate([gz.ravel()[idx], gw.ravel()])
    return fg, idx


def polish(iters):
    global z, w
    free = ~frozen
    fg, idx = fg_factory(free)
    r = minimize(fg, np.concatenate([z.ravel()[idx], w.ravel()]), jac=True, method="L-BFGS-B",
                 options=dict(maxiter=iters, maxcor=20))
    zz = z.ravel().copy()
    zz[idx] = r.x[:idx.size]
    z = zz.reshape(R * B, E_)
    w = r.x[idx.size:].reshape(R, B, C)
    return float(np.sqrt(r.fun))


def now():
    return error2(decode(z * step, tree).reshape(R, B, N), w, G)


log = []
if Path(ROOT + f"etapas_{TAG}.json").exists():      # resume after the last saved stage
    log = json.load(open(ROOT + f"etapas_{TAG}.json"))
    ck = np.load(ROOT + f"etapas_{TAG}.npz")
    z, w, frozen = ck["z"], ck["w"], ck["frozen"]
    print("reanudo tras la etapa", len(log) - 1, "fijadas", frozen.mean(), flush=True)
for s, frac in enumerate(FRACS):
    if s < len(log):
        continue
    e, E, Xm = now()
    for r in range(R):
        rows = slice(r * B, (r + 1) * B)
        fr = frozen[rows].ravel()
        target_n = int(round(frac * fr.size))
        commit = target_n - int(fr.sum())
        if commit <= 0:
            continue
        uu, D = decode_jac(z[rows] * step, tree)
        X_g = Xm[:, r * C:(r + 1) * C]
        Hf, o, d = group_hessian_free(uu, D, w[r], X_g, step, np.flatnonzero(~fr))
        b = group_gradient(uu, D, w[r], X_g, E, step)
        Hf[np.diag_indices_from(Hf)] += ALPHA * d.mean() + 1e-14
        L = sl.cholesky(Hf, lower=True, check_finite=False, overwrite_a=True)
        delta = -sl.cho_solve((L, True), b[o], check_finite=False)
        zr = z[rows].ravel().copy()
        y = zr[o] + delta
        n = y.size
        err = np.zeros(n)
        zq = np.empty(n)
        Ld = np.diag(L).copy()
        ev = even[rows].ravel()[o]
        for k in range(n - 1, -1, -1):
            c = y[k] - (L[k + 1:, k] @ err[k + 1:]) / Ld[k]
            zq[k] = (2 * np.round(c / 2) if ev[k] else np.round(c)) if k >= n - commit else c
            err[k] = zq[k] - y[k]
        del L, Hf
        zr[o] = zq
        z[rows] = zr.reshape(B, E_)
        fz = frozen[rows].ravel().copy()
        fz[o[n - commit:]] = True
        frozen[rows] = fz.reshape(B, E_)
        e, E, Xm = now()
    ec = e
    ep = polish(POLISH)
    log.append(dict(stage=s, frac=frac, tras_babai=ec, tras_pulido=ep, t=time.time() - t0))
    print(f"etapa {s} fijadas {frozen.mean():.3f} error_2 {ec:.5f} -> pulido {ep:.5f} t={time.time()-t0:.0f}s", flush=True)
    np.savez(ROOT + f"etapas_{TAG}.npz", z=z, w=w, frozen=frozen, even=even)
    json.dump(log, open(ROOT + f"etapas_{TAG}.json", "w"), indent=1)

assert frozen.all()
z = np.round(z)
print("enteras, error_2", now()[0], flush=True)
ep = polish(120)
print("final tras pesos", ep, "t", time.time() - t0, flush=True)
np.savez(ROOT + f"etapas_{TAG}.npz", z=z, w=w, frozen=frozen, even=even)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
