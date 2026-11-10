# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Minimize lambda_eff with error_2 and the gap floor as constraints.

Augmented Lagrangian over angles, weights and offsets, in continuous variables.
Usage: lam_opt.py <input.npz | publica> <tau> <tag> [outer] [inner] [wall_s]
Reference: public table lambda_eff 46.8933, error_2 0.02, E_gap at its floor.
"""
import sys
from gpu_lib import *

src, TAU, TAG = sys.argv[1], float(sys.argv[2]), sys.argv[3]
OUTER = int(sys.argv[4]) if len(sys.argv) > 4 else 12
INNER = int(sys.argv[5]) if len(sys.argv) > 5 else 150
WALL = float(sys.argv[6]) if len(sys.argv) > 6 else 600
m = Chem()
c = np.load(ROOT + "chem_state.npz")
R, B, C0 = c["w"].shape
if src == "publica":
    th = torch.tensor(c["words"][N:] * (np.pi / 2 ** (int(c["brot"]) - 1)), device=DEV, dtype=DT)
    w = torch.tensor(c["w"], device=DEV, dtype=DT)
    W = m.W0.clone()
else:
    d = np.load(ROOT + src)
    th = torch.tensor(d["th"], device=DEV, dtype=DT)
    w = torch.tensor(d["w"], device=DEV, dtype=DT)
    W = torch.tensor(d["W"], device=DEV, dtype=DT) if "W" in d else torch.cat(
        [m.W0, torch.zeros(R, w.shape[2] - C0, device=DEV, dtype=DT)], dim=1)
th.requires_grad_(True); w.requires_grad_(True); W.requires_grad_(True)
GAP = m.GAP_FLOOR + 1e-6
nu = [0.0, 0.0]
mu = [50.0, 200.0]


def constraints():
    e2 = m.loss(th, w)
    Lam, gap, leff = m.costs(th, w, W)
    return leff, (e2 / TAU ** 2 - 1.0), (GAP - gap) / GAP, e2, Lam, gap


def report(k, t0):
    with torch.no_grad():
        leff, c1, c2, e2, Lam, gap = constraints()
    print(f"{TAG} ronda {k} t={time.time()-t0:.0f}s lambda_eff {float(leff):.5f} error_2 {float(e2)**.5:.6f} "
          f"Lambda {float(Lam):.3f} E_gap {float(gap):.6f} nu {nu[0]:.2f} {nu[1]:.2f}", flush=True)
    return float(c1), float(c2), float(leff), float(e2) ** .5, float(gap)


t0 = time.time()
report(-1, t0)
best = None
for k in range(OUTER):
    opt = torch.optim.LBFGS([th, w, W], lr=1.0, max_iter=INNER, history_size=30, tolerance_grad=1e-12,
                            tolerance_change=1e-14, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        leff, c1, c2, *_ = constraints()
        J = leff + (torch.relu(nu[0] + mu[0] * c1) ** 2 - nu[0] ** 2) / (2 * mu[0]) \
                 + (torch.relu(nu[1] + mu[1] * c2) ** 2 - nu[1] ** 2) / (2 * mu[1])
        J.backward()
        return J

    opt.step(closure)
    c1, c2, leff, e2, gap = report(k, t0)
    nu[0] = max(0.0, nu[0] + mu[0] * c1)
    nu[1] = max(0.0, nu[1] + mu[1] * c2)
    if e2 <= TAU * 1.0005 and gap >= m.GAP_FLOOR and (best is None or leff < best):
        best = leff
        np.savez(ROOT + f"lam_{TAG}.npz", th=th.detach().cpu().numpy(), w=w.detach().cpu().numpy(),
                 W=W.detach().cpu().numpy(), leff=leff, e2=e2, gap=gap)
    if time.time() - t0 > WALL:
        break
print("fin", TAG, "mejor lambda_eff factible", best, flush=True)

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
