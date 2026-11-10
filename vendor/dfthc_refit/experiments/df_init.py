"""A DF-informed seed: the target's own eigen-leaves as copies, their eigenvectors as shared bases.

    python notebooks/dfthc-refit/experiments/df_init.py OUT.npz R B C [--assign blocks|roundrobin] [--fit N] [--kappa 5e-5]

The structure is a sum of squares of one-body operators: in packed pair space (fastfit) the row of
copy (r, c) is pack(L_rc) with L_rc = sum_b w_rbc u_rb u_rb^T, and error_2 = |D (A^T A - T) D|_F with
D = diag(m), m = 1 on diagonal pairs and 2 elsewhere. So T' = D T D = sum_k lambda_k v_k v_k^T (eigh)
is a double factorization: the leaves L_k = unpack(sqrt(lambda_k) v_k / m) (positive lambda only)
satisfy sum_k pack(L_k) pack(L_k)^T = T exactly. The seed takes the R * C largest leaves as copies,
assigns them to groups, picks each group's B shared bases among its leaves' eigenvectors (simultaneous
OMP over the copies' pair-space residuals, or by |eigenvalue| rank with `--select eig`), and solves each copy's weights by weighted least
squares over the pair vectors of those bases. The only approximation is the shared basis (THC);
`--fit` then runs L-BFGS on error_2 + kappa D(w) and writes OUT.npz with the result (the seed itself
goes to OUT.init.npz). The random start of experiments/random_init.py is the control.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import FCIDUMP, SHIFTS, UPPER_ENERGY  # noqa: E402
import fastfit  # noqa: E402

import jax  # noqa: E402

jax.config.update('jax_enable_x64', True)
jax.config.update('jax_default_matmul_precision', 'highest')
import jax.numpy as jnp  # noqa: E402
from dfthc import df_thc_sga  # noqa: E402

df_thc_sga.dtype = jnp.float64
from dfthc.train_df_thc_sga import Initialize  # noqa: E402

N = 76
CHOL_TOL = 1e-6   # pivoted Cholesky stops when the residual diagonal falls below this fraction of its start


def unpack(a: np.ndarray, i: np.ndarray, j: np.ndarray) -> np.ndarray:
    L = np.zeros((N, N))
    L[i, j] = a
    L[j, i] = a
    return L


def omp_bases(cand: np.ndarray, targets: np.ndarray, i: np.ndarray, j: np.ndarray, m: np.ndarray, B: int,
              power: float = 1.0) -> np.ndarray:
    """Simultaneous orthogonal matching pursuit: B unit vectors from `cand` (K, N) whose pair vectors best span
    the copies' targets (C, P) when every copy is re-projected after each pick. The pair weights m and each
    copy's own norm enter the objective: error_2 = |A^T A - T| grows with |a_k| |delta_k| for a leaf a_k off by delta_k."""
    Pi = (cand[:, i] * cand[:, j]) * m[None, :]                       # (K, P) weighted pair vectors
    Pi_n = Pi / np.linalg.norm(Pi, axis=1, keepdims=True)
    Y = targets * m[None, :]                                           # (C, P)
    Y = Y * np.linalg.norm(Y, axis=1, keepdims=True) ** power          # error_2 weighs a leaf's residual by its norm
    resid = Y.copy()
    chosen: list[int] = []
    for _ in range(B):
        score = np.sum((Pi_n @ resid.T) ** 2, axis=1)                  # (K,) energy explained per candidate
        score[chosen] = -1.0
        chosen.append(int(np.argmax(score)))
        A = Pi[chosen].T                                               # (P, b)
        resid = Y - (A @ np.linalg.lstsq(A, Y.T, rcond=None)[0]).T
    return cand[chosen]


def balanced_kmeans(X: np.ndarray, R: int, size: int, weight: np.ndarray, iters: int = 60, seed: int = 0) -> np.ndarray:
    """R clusters of exactly `size` rows of X (unit rows), weighted centroids; greedy balanced assignment."""
    rng = np.random.default_rng(seed)
    n = len(X)
    lab = rng.permutation(np.repeat(np.arange(R), size))
    for _ in range(iters):
        cen = np.array([np.average(X[lab == r], axis=0, weights=weight[lab == r] + 1e-12) for r in range(R)])
        cen /= np.linalg.norm(cen, axis=1, keepdims=True)
        sim = X @ cen.T
        srt = np.sort(sim, axis=1)
        order = np.argsort(-(srt[:, -1] - srt[:, -2]))      # the most decided rows pick first
        left, new = np.full(R, size), np.zeros(n, int)
        for idx in order:
            for r in np.argsort(-sim[idx]):
                if left[r] > 0:
                    new[idx] = r
                    left[r] -= 1
                    break
        if np.all(new == lab):
            break
        lab = new
    return lab


def seed(R: int, B: int, C: int, prob, assign: str, select: str = 'omp', cos: float = 0.98,
         power: float = 1.0, leaves_kind: str = 'eig') -> tuple[np.ndarray, np.ndarray, dict]:
    T, M, i, j = (np.asarray(x) for x in prob)
    m = np.sqrt(np.diag(M))
    Tw = m[:, None] * T * m[None, :]
    lam, V = np.linalg.eigh(Tw)
    order = np.argsort(-lam)
    pos = int((lam > 0).sum())
    K = R * C
    if K > pos:
        raise SystemExit(f'only {pos} positive eigenvalues for {K} copies')
    info = {'positive': pos, 'kept_weight': float(lam[order[:K]].sum() / lam[lam > 0].sum()),
            'dropped_negative': float(-lam[lam < 0].sum() / lam[lam > 0].sum())}
    if leaves_kind == 'chol':
        # Pivoted Cholesky of the weighted target: each leaf is a column, local in orbital space by construction
        # (the other lane's measurement: public groups touch ~18 orbitals each, eigen-leaf groups ~30).
        P = len(Tw)
        diag, L, tol = np.diag(Tw).copy(), np.zeros((P, K)), float(CHOL_TOL) * float(np.diag(Tw).max())
        nchol = K
        for k in range(K):
            q = int(np.argmax(diag))
            v = Tw[:, q] - L[:, :k] @ L[q, :k]
            if v[q] <= tol:                      # the residual is exhausted: stop before dividing by noise
                nchol = k
                break
            L[:, k] = v / np.sqrt(v[q])          # v[q], not the tracked diagonal: no catastrophic cancellation
            diag = np.maximum(diag - L[:, k] ** 2, 0)
        if nchol < K:                            # pad with the residual's eigen-leaves (tiny weight, not local)
            resid = Tw - L[:, :nchol] @ L[:, :nchol].T
            lr, Vr = np.linalg.eigh(resid)
            take = np.argsort(-lr)[:K - nchol]
            L[:, nchol:] = np.sqrt(np.maximum(lr[take], 0)) * Vr[:, take]
        info['chol_leaves'] = nchol
        info['chol_reproduction_mHa'] = 1e3 * float(np.linalg.norm(L @ L.T - Tw))
        leaves = [unpack(L[:, k] / m, i, j) for k in range(K)]
    else:
        leaves = [unpack(np.sqrt(lam[k]) * V[:, k] / m, i, j) for k in order[:K]]     # by weight, descending
    if assign == 'cluster':
        # Groups of leaves that live on the same orbitals: balanced k-means on the leaves' orbital profiles.
        prof = np.array([np.sqrt(np.sum(l ** 2, axis=1)) for l in leaves])
        prof /= np.linalg.norm(prof, axis=1, keepdims=True)
        wt = np.array([np.sum(l ** 2) for l in leaves])
        lab = balanced_kmeans(prof, R, C, wt)
        groups = [list(np.flatnonzero(lab == r)) for r in range(R)]
        info['group_weight_share'] = [float(wt[g].sum() / wt.sum()) for g in groups]
    else:
        groups = [list(range(r * C, (r + 1) * C)) if assign == 'blocks' else list(range(r, K, R)) for r in range(R)]
    U = np.zeros((R, B, N))
    W = np.zeros((R, B, C))
    for r, ks in enumerate(groups):
        # Candidate bases: the leaves' eigenvectors, scored by |eigenvalue| (a leaf's rank-1 terms); the B best
        # distinct ones (|cos| < 0.98 with every basis already chosen) become the group's shared bases.
        cand, score = [], []
        for k in ks:
            e, Q = np.linalg.eigh(leaves[k])
            cand.append(Q.T)
            score.append(np.abs(e))
        cand, score = np.concatenate(cand), np.concatenate(score)
        if select == 'omp':
            U[r] = omp_bases(cand, np.stack([leaves[k][i, j] for k in ks]), i, j, m, B, power)
        else:
            chosen: list[np.ndarray] = []
            for idx in np.argsort(-score):
                v = cand[idx]
                if all(abs(v @ c) < cos for c in chosen):
                    chosen.append(v)
                if len(chosen) == B:
                    break
            if len(chosen) < B:
                raise SystemExit(f'group {r}: only {len(chosen)} distinct candidate bases for B = {B}')
            U[r] = np.stack(chosen)
        u = U[r] / np.linalg.norm(U[r], axis=1, keepdims=True)
        Pi = (u[:, i] * u[:, j]) * m[None, :]                                        # (B, P) weighted pair vectors
        for c, k in enumerate(ks):
            target = leaves[k][i, j] * m
            W[r, :, c] = np.linalg.lstsq(Pi.T, target, rcond=None)[0]
    return U, W, info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('out', type=Path)
    ap.add_argument('R', type=int)
    ap.add_argument('B', type=int)
    ap.add_argument('C', type=int)
    ap.add_argument('--assign', choices=('blocks', 'roundrobin', 'cluster'), default='roundrobin')
    ap.add_argument('--leaves', choices=('eig', 'chol'), default='eig', help='eigen-leaves or pivoted-Cholesky leaves')
    ap.add_argument('--chol-tol', type=float, default=1e-6)
    ap.add_argument('--select', choices=('omp', 'eig'), default='omp',
                    help='shared bases by simultaneous OMP over the copies (omp) or by |eigenvalue| rank (eig)')
    ap.add_argument('--fit', type=int, default=0)
    ap.add_argument('--kappa', type=float, default=5e-5)
    ap.add_argument('--report', type=int, default=1000)
    ap.add_argument('--cos', type=float, default=0.98, help='eig: skip a candidate within this |cos| of a chosen basis')
    ap.add_argument('--power', type=float, default=1.0, help='omp: weight a copy\'s residual by its norm to this power')
    ap.add_argument('--start', type=Path, help='skip the seed: fit this structure npz instead (e.g. a random_init.py start)')
    a = ap.parse_args()
    global CHOL_TOL
    CHOL_TOL = a.chol_tol

    ref = Initialize(str(FCIDUMP), UPPER_ENERGY)
    ref = {k: (jnp.asarray(v, jnp.float64) if hasattr(v, 'dtype') and jnp.issubdtype(v.dtype, jnp.floating) else v)
           for k, v in ref.items()}
    with np.load(SHIFTS) as z:
        frozen = {k: jnp.asarray(z[k], jnp.float64) for k in ('Hsym_lower', 'H1_I')}
        shifts = {k: np.array(z[k]) for k in ('H1_I', 'Hsym_lower')}
    prob = fastfit.problem(ref, frozen, jnp.float64)

    t0 = time.time()
    if a.start:
        with np.load(a.start) as z:
            U, W = np.asarray(z['U'], np.float64), np.asarray(z['W'], np.float64)
    else:
        U, W, info = seed(a.R, a.B, a.C, prob, a.assign, a.select, a.cos, a.power, a.leaves)
        print(f'leaves: {info["positive"]} positive eigenvalues, the {a.R * a.C} kept carry {100 * info["kept_weight"]:.2f}% '
              f'of the positive weight, negative weight {100 * info["dropped_negative"]:.3f}% ({time.time() - t0:.0f} s)')
        if 'chol_reproduction_mHa' in info:
            print(f'pivoted Cholesky: {info["chol_leaves"]} of {a.R * a.C} leaves (rest: residual eigen-leaves) reproduce the target to {info["chol_reproduction_mHa"]:.2f} mHa')
        if 'group_weight_share' in info:
            sh = info['group_weight_share']; print(f'clustered groups hold {100 * min(sh):.1f}% to {100 * max(sh):.1f}% of the weight')

    def objective(p):
        eps = fastfit.error2(p[0], p[1], prob)
        D = 0.5 * jnp.sum(jnp.sum(jnp.abs(p[1]), axis=1) ** 2 - jnp.sum(p[1], axis=1) ** 2)
        return eps + a.kappa * D

    err = jax.jit(lambda U, w: fastfit.error2(U, w, prob))
    Dw = lambda w: 0.5 * float(np.sum(np.sum(np.abs(w), axis=1) ** 2 - np.sum(w, axis=1) ** 2))  # noqa: E731
    print(f'seed {W.shape} ({a.start.name if a.start else a.leaves + "/" + a.assign + "/" + a.select}): error_2 {1e3 * float(err(U, W)):8.3f} mHa  D {Dw(W):7.2f}', flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out.with_suffix('.init.npz'), U=U, W=W, H2_I=W.sum(axis=1), **shifts)
    p = (jnp.asarray(U), jnp.asarray(W))
    done = 0
    while done < a.fit:
        n = min(a.report, a.fit - done)
        p = fastfit.lbfgs(objective, p, n, chunk=min(200, n))
        done += n
        print(f'{done:7d}: error_2 {1e3 * float(err(*p)):8.3f} mHa  D {Dw(np.asarray(p[1])):7.2f}  ({time.time() - t0:.0f} s)',
              flush=True)
    U, W = (np.asarray(x) for x in p)
    np.savez(a.out, U=U, W=W, H2_I=W.sum(axis=1), **shifts)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
