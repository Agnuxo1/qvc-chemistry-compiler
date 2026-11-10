"""Deal a table's rows across the QROM's 16-address blocks before coded rounding.

    python notebooks/dfthc-refit/experiments/deal_rows.py IN.npz OUT.npz [--block 16]

Permuting the rows (bases) inside a group leaves the represented Hamiltonian unchanged, but the coded
low bits share one pattern per block of 16 consecutive addresses, so blocks full of strong rows pay
more rounding error. The fit sorts rows nearly by strength, so strong rows crowd into the same blocks;
dealing the ranks round-robin over the blocks spreads them (the other lane's estimate: bit 0's raw
added noise falls to 33-43% of the sorted order's). Row strength = sum over copies of w^2.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def deal(order_strength: np.ndarray, block: int) -> np.ndarray:
    """Positions for the rows ranked by strength: rank k goes to block k % nb, slot k // nb."""
    B = len(order_strength)
    nb = -(-B // block)
    ranks = np.argsort(-order_strength)                       # row indices, strongest first
    perm = np.empty(B, dtype=int)                              # perm[position] = original row
    sizes = [min(block, B - j * block) for j in range(nb)]
    slots = [0] * nb
    j = 0
    for row in ranks:
        while slots[j] >= sizes[j]:
            j = (j + 1) % nb
        perm[j * block + slots[j]] = row
        slots[j] += 1
        j = (j + 1) % nb
    return perm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('inp', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--block', type=int, default=16)
    a = ap.parse_args()
    z = np.load(a.inp)
    U, W = np.array(z['U']), np.array(z['W'])
    R, B, C = W.shape
    strength = np.sum(W ** 2, axis=2)                          # (R, B)

    def block_spread(w2):
        nb = -(-B // a.block)
        shares = np.array([w2[j * a.block:(j + 1) * a.block].sum() for j in range(nb)]) / w2.sum()
        return shares.max() / shares.mean()

    before = np.mean([block_spread(strength[r]) for r in range(R)])
    for r in range(R):
        perm = deal(strength[r], a.block)
        U[r], W[r] = U[r][perm], W[r][perm]
    after = np.mean([block_spread(np.sum(W[r] ** 2, axis=1)) for r in range(R)])
    out = {k: np.array(z[k]) for k in z.files}
    out.update(U=U, W=W, H2_I=W.sum(axis=1))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, **out)
    print(f'{a.inp.name} -> {a.out.name}: {R} groups x {B} rows dealt over blocks of {a.block}; '
          f'heaviest block / mean block weight {before:.2f} -> {after:.2f}')


if __name__ == '__main__':
    main()
