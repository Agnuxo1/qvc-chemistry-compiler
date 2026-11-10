"""The orbital-clustered seed at any (R, B, C), with the verifier's weighting.

    python notebooks/dfthc-refit/experiments/compact_seed.py OUT.npz R B C [--check SEED.npz]

Pivoted Cholesky of the weighted target gives R * C leaves, local in orbital space. Balanced k-means on their
orbital profiles makes R groups of C leaves; each group picks B shared vectors by simultaneous OMP over its leaves'
eigenvectors, and each leaf's weights come from least squares. error_2 weighs a packed residual entry by
sqrt(m_p m_q) (fastfit.error2, m = 1 on diagonal pairs and 2 elsewhere), so the target is d T d with d = sqrt(m).
df_init.seed weights by m instead, which leaves an exact factorization but ranks and truncates it in the wrong norm.
This is the construction of runs/r10/chol9_143x46.init.npz; `--check` compares a rebuild against such a file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import FCIDUMP, SHIFTS, UPPER_ENERGY  # noqa: E402
import fastfit  # noqa: E402
import df_init  # noqa: E402

import jax.numpy as jnp  # noqa: E402
from dfthc.train_df_thc_sga import Initialize  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('out', type=Path)
    ap.add_argument('R', type=int)
    ap.add_argument('B', type=int)
    ap.add_argument('C', type=int)
    ap.add_argument('--check', type=Path)
    ap.add_argument('--kmeans-seed', type=int, default=0, help='start of the balanced k-means')
    a = ap.parse_args()
    ref = Initialize(str(FCIDUMP), UPPER_ENERGY)
    ref = {k: (jnp.asarray(v, jnp.float64) if hasattr(v, 'dtype') and jnp.issubdtype(v.dtype, jnp.floating) else v)
           for k, v in ref.items()}
    with np.load(SHIFTS) as z:
        frozen = {k: jnp.asarray(z[k], jnp.float64) for k in ('Hsym_lower', 'H1_I')}
        shifts = {k: np.array(z[k]) for k in ('H1_I', 'Hsym_lower')}
    T, M, ii, jj = (np.asarray(x) for x in fastfit.problem(ref, frozen, jnp.float64))
    mult = np.where(ii == jj, 1.0, 2.0)
    d = np.sqrt(mult)
    Tw = d[:, None] * T * d[None, :]
    K = a.R * a.C
    diag, L = np.diag(Tw).copy(), np.zeros((len(Tw), K))
    for k in range(K):
        q = int(np.argmax(diag))
        L[:, k] = (Tw[:, q] - L[:, :k] @ L[q, :k]) / np.sqrt(diag[q])
        diag = np.maximum(diag - L[:, k] ** 2, 0)
    leaves = [df_init.unpack(L[:, k] / d, ii, jj) for k in range(K)]
    profile = np.array([np.sqrt(np.sum(l ** 2, axis=1)) for l in leaves])
    profile /= np.linalg.norm(profile, axis=1, keepdims=True)
    weight = np.array([np.sum(l ** 2) for l in leaves])
    label = df_init.balanced_kmeans(profile, a.R, a.C, weight, seed=a.kmeans_seed)
    N = leaves[0].shape[0]
    U, W = np.zeros((a.R, a.B, N)), np.zeros((a.R, a.B, a.C))
    for r in range(a.R):
        ks = list(np.flatnonzero(label == r))
        cand = np.concatenate([np.linalg.eigh(leaves[k])[1].T for k in ks])
        U[r] = df_init.omp_bases(cand, np.stack([leaves[k][ii, jj] for k in ks]), ii, jj, mult, a.B, 0.0)
        pairs = (U[r][:, ii] * U[r][:, jj]) * mult[None, :]
        for c, k in enumerate(ks):
            W[r, :, c] = np.linalg.lstsq(pairs.T, leaves[k][ii, jj] * mult, rcond=None)[0]
    A = np.einsum('rbc,rbp->rcp', W, U[:, :, ii] * U[:, :, jj]).reshape(-1, len(ii)) * d
    share = np.bincount(label, weights=weight, minlength=a.R) / weight.sum()
    print(f'{K} leaves reproduce the target to {1e3 * np.linalg.norm(L @ L.T - Tw):.2f} mHa; seed {W.shape}: error_2 '
          f'{1e3 * np.linalg.norm(A.T @ A - Tw):.2f} mHa; groups hold {100 * share.min():.1f}% to {100 * share.max():.1f}% of the weight')
    if a.check:
        with np.load(a.check) as z:
            Uc, Wc = z['U'].astype(float), z['W'].astype(float)
        print(f'against {a.check.name}: weights differ by {np.abs(W - Wc).max():.1e}, vectors by {np.abs(np.abs(np.sum(U * Uc, axis=2)) - 1).max():.1e}')
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, U=U, W=W, H2_I=W.sum(axis=1), **shifts)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
