"""Reed-Muller codes on the low bits of the angle words, per 16-address block, for cheaper loaders.

A loaded output bit f(l, h) has a mixed tensor over 15 low monomials m(l) and the high monomials. On each block
(fixed h) it is a word of length 16. If that word lies in RM(d, 4), the low monomials of degree above d vanish
for this output, so its rank falls and the loader needs fewer products: RM(1, 4) (rank 4) is somejoint's coded
bit, RM(2, 4) (rank 10, the extended Hamming code, 5 parity relations) kills the five monomials of degree 3 and 4,
and RM(3, 4) (rank 14) kills only the last one.

An extended Hamming word is at most two flips away from any bit pattern, and most (row, column) entries of a table
act on almost no amplitude: a row lives on about 3 orbitals and the tree has 75 angles. So the relations can be
met on entries that hardly matter, above all in the late columns near the leaves of the tree.

`deg[col, bit]` is the degree of the code on that bit of that word column, 0 when the bit is free; the coded bits of
a column are contiguous from bit 0. A column in RM(d) on two consecutive batches gives a delta in RM(d) too.
"""
from __future__ import annotations

import itertools
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@lru_cache(maxsize=None)
def code(d: int) -> np.ndarray:
    """All words of RM(d, 4), (2**k, 16), as floats."""
    pts = [[(x >> i) & 1 for i in range(4)] for x in range(16)]
    gens = [[1] * 16] + [[int(all(p[i] for i in m)) for p in pts]
                         for e in range(1, d + 1) for m in itertools.combinations(range(4), e)]
    G = np.array(gens, np.uint8)
    k = len(G)
    return (np.array([[(c >> i) & 1 for i in range(k)] for c in range(1 << k)], np.uint8) @ G % 2).astype(np.float64)


def parse(spec: str | None, ncols: int, bits: int = 8) -> np.ndarray:
    """deg (ncols, bits) from 'bit:degree:first-last,...' over five-word batches, e.g. '0:1:3-14,1:2:3-14'."""
    deg = np.zeros((ncols, bits), np.int64)
    for item in filter(None, (spec or '').split(',')):
        bit, d, span = item.split(':')
        lo, hi = (int(x) for x in span.split('-')) if '-' in span else (int(span),) * 2
        deg[5 * lo:5 * hi + 5, int(bit)] = int(d)
    assert not np.any((deg[:, 1:] > 0) & (deg[:, :-1] == 0)), 'coded bits must be contiguous from bit 0'
    return deg


def residue_round(t: np.ndarray, r: np.ndarray, m) -> np.ndarray:
    """The nearest value to t (in steps) whose integer is r mod m."""
    lo = np.floor(t)
    lo = lo - np.mod(lo - r, m)
    hi = lo + m
    return np.where(t - lo <= hi - t, lo, hi)


def into_gauge(v: np.ndarray, m, scale: float) -> np.ndarray:
    """Coded words (in steps) kept inside the signed range by whole code periods m."""
    v = np.where(v > scale / 2 - 1, v - m, v)
    return np.where(v < -scale / 2, v + m, v)


def residues(t: np.ndarray, c: np.ndarray, blk: np.ndarray, pos: np.ndarray, deg: np.ndarray,
             fixed: np.ndarray | None = None, value: np.ndarray | None = None, scale: float | None = None,
             reserved: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Per coded column, the block codewords of least curvature-weighted squared offset, bit by bit from bit 0.

    t (rows, cols) in steps, c its curvature, deg (cols, bits). A `fixed` entry keeps the bits of its integer
    `value`, so a codeword stays open until its frozen entries pin it down, instead of locking at the first freeze.
    With `scale`, words stay in the signed range, and an offset counts the wrap: an entry at 63.4 that a code sends to
    64 lands on 60. `reserved` entries (see `slack`) cost nothing, so they alone absorb the relations until they freeze:
    a flipped entry has a large offset and would freeze at once, and as free angles drift the parity fails again, so
    without them flips pile up stage after stage. Returns the residue of every entry and each column's modulus.
    """
    near = lambda r_, m_, t_: (lambda v_: rmcode_gauge(v_, m_))(residue_round(t_, r_, m_))  # noqa: E731
    rmcode_gauge = (lambda v_, m_: into_gauge(v_, m_, scale)) if scale else (lambda v_, m_: v_)  # noqa: E731
    nblocks = int(blk.max()) + 1
    r = np.zeros(t.shape, np.int64)
    for bit in range(deg.shape[1]):
        idx = np.flatnonzero(deg[:, bit])
        if not len(idx):
            break
        m = 1 << bit
        cost = [c[:, idx] * (near(r[:, idx] + v * m, 2 * m, t[:, idx]) - t[:, idx]) ** 2 for v in (0, 1)]
        if reserved is not None:
            cost = [np.where(reserved[:, idx], 0.0, x) for x in cost]
        if fixed is not None:
            have = (value[:, idx] >> bit) & 1
            big = 1e4 * max(float(x.max()) for x in cost) + 1e-300   # not larger: a double must still resolve the real costs
            cost = [np.where(fixed[:, idx], np.where(have == v, 0.0, big), cost[v]) for v in (0, 1)]
        table = [np.zeros((nblocks, 16, len(idx))) for _ in (0, 1)]
        for v in (0, 1):
            table[v][blk, pos] = cost[v]
        for d in np.unique(deg[idx, bit]):
            s = np.flatnonzero(deg[idx, bit] == d)
            words = code(int(d))
            gain = (table[1] - table[0])[:, :, s].transpose(0, 2, 1) @ words.T            # (blocks, columns, words)
            pick = words[gain.argmin(axis=2)]                                              # (blocks, columns, 16)
            r[:, idx[s]] += (pick[blk, :, pos] * m).astype(np.int64)
    return r, 1 << (deg > 0).sum(axis=1)


def gauge_angles(theta: np.ndarray, edges: np.ndarray, early: float = 0.0) -> np.ndarray:
    """onebody.signed_gauge on angles in units of pi: the same unit vectors up to sign, for frozen and free angles alike.

    A hard clip to the signed range is not an option during rounding: in a compact table the strong entries that
    hand all their amplitude to the child sit at +-1/2, so a wall there costs far more than any code (12.5 -> 18.7 mHa at
    the first stage). So angles stay free, and this runs once, when only the reserved entries are left to absorb what
    it does to the coded bits: negating a word changes every bit above bit 0 of an odd one, and a half turn none.
    `early` moves the wrap down: angles land in [-1/2 - early, 1/2 - early), so half a step rounds into the signed range."""
    out = np.mod(theta, 2.0)
    sign = np.ones((len(out), edges.shape[0] + 1), np.int8)
    for k in reversed(range(edges.shape[0])):
        p, q = edges[k]
        a = np.where(sign[:, p] != sign[:, q], np.mod(-out[:, k], 2.0), out[:, k])
        flip = (a >= 0.5 - early) & (a < 1.5 - early)
        out[:, k] = np.where(flip, np.mod(a + 1.0, 2.0), a)
        sign[flip, p] *= -1
        sign[:, q] = 1
    return np.where(out >= 1.0 - early, out - 2.0, out)


def slack(c: np.ndarray, blk: np.ndarray, pos: np.ndarray, deg: np.ndarray, fixed: np.ndarray | None = None) -> np.ndarray:
    """Entries kept for last: in each block of a column, the weakest positions whose parity checks are independent,
    five for RM(2, 4) and one for RM(3, 4). Rounding freezes angles by impact, so a strong entry with a small offset can
    freeze late and then be forced by a relation with nothing left to absorb it. With these frozen last, every
    relation can be met on an entry that hardly matters. RM(1, 4) needs none: its pattern pins down within five
    entries. Blocks with seven or fewer open positions need none either: any seven positions of RM(2, 4) are free."""
    mask = np.zeros(c.shape, bool)
    for col in range(c.shape[1]):
        high = deg[col][deg[col] > 1]
        if not len(high):
            continue
        need = 5 if high.min() == 2 else 1
        for b in np.unique(blk):
            idx = np.flatnonzero((blk == b) & (~fixed[:, col] if fixed is not None else True))
            if len(idx) <= 7:
                continue
            piv: dict[int, int] = {}
            for i in idx[np.argsort(c[idx, col])]:
                v = 16 | int(pos[i])
                while v and v.bit_length() in piv:
                    v ^= piv[v.bit_length()]
                if v:
                    piv[v.bit_length()] = v
                    mask[i, col] = True
                    if len(piv) == need:
                        break
    return mask


def last(impact: np.ndarray, reserved: np.ndarray) -> np.ndarray:
    """Impacts with the reserved entries below every other open entry, in their own order."""
    return np.where(reserved, -1.0 / (1.0 + impact), impact)


def check(words: np.ndarray, addr: np.ndarray, deg: np.ndarray) -> None:
    """Every coded bit lies in its code on every block, on the addresses present."""
    blk, pos = addr // 16, addr % 16
    for col, bit in zip(*np.nonzero(deg)):
        cw = code(int(deg[col, bit]))
        bits = (words[:, col] >> bit) & 1
        for b in np.unique(blk):
            rows = np.flatnonzero(blk == b)
            assert np.any(np.all(cw[:, pos[rows]] == bits[rows], axis=1)), f'bit {bit} of column {col}, block {b}'


def one_order(lam: np.ndarray, mode: str = 'strong') -> np.ndarray:
    """Which eigenvector each one-body row holds. The verifier pairs rows with eigenvectors by a one-to-one assignment
    on |overlap|, so the order is free. A row's error scales with its eigenvalue, so rows are dealt across the
    blocks by |lam|: 'weak' puts each block's weakest rows on {0, 1, 2, 4, 8}, whose bits reach every syndrome of
    RM(2, 4), 'strong' its strongest there (an information set of RM(1, 4)), 'sorted' keeps ascending order."""
    N = len(lam)
    if mode == 'sorted':
        return np.arange(N)
    nblocks = -(-N // 16)
    rank = np.argsort(np.abs(lam))                                     # weakest first
    pivots = [0, 1, 2, 4, 8]
    rest = [p for p in range(16) if p not in pivots]
    positions = pivots + rest if mode == 'weak' else rest + pivots     # filled from the weakest row up
    order, used = -np.ones(N, np.int64), 0
    for p in positions:
        for b in range(nblocks):
            a = 16 * b + p
            if a < N:
                order[a] = rank[used]
                used += 1
    return order


def quantize_onebody(h1p: np.ndarray, edges: np.ndarray, brot: int, deg: np.ndarray, following: np.ndarray,
                     order: np.ndarray | None = None, iters: int = 300, probes: int = 8, seed: int = 0, log=None) -> np.ndarray:
    """One-body words by onebody_quant's progressive rounding, with the codes of `deg` on every block of 16 addresses.
    `following` holds the two-body rows that complete the last block; their bits are fixed. Row a holds
    eigenvector order[a] (default ascending)."""
    import jax
    import jax.numpy as jnp
    from scipy.optimize import minimize
    import encode
    from onebody_quant import FREE
    from quantize import decode
    jax.config.update('jax_enable_x64', True)
    N = h1p.shape[0]
    lam, vecs = np.linalg.eigh(h1p)
    if order is not None:
        lam, vecs = lam[order], vecs[:, order]
    scale, mod = float(1 << (brot - 1)), 1 << brot
    theta = encode.signed_angles(vecs.T, edges)
    H, L = jnp.asarray(h1p), jnp.asarray(lam)
    resid = lambda th: ((decode(th, edges, N).T * L) @ decode(th, edges, N) - H).ravel()  # noqa: E731
    vg = jax.jit(jax.value_and_grad(lambda th: jnp.sum(resid(th) ** 2)))

    @jax.jit
    def curvature(th, key):
        _, vjp = jax.vjp(resid, th)
        return jnp.mean(jax.vmap(lambda k: vjp(jax.random.normal(k, (N * N,), th.dtype))[0] ** 2)(jax.random.split(key, probes)), axis=0)

    ccols = np.flatnonzero(deg.any(axis=1))
    extra = -N % 16
    addr = np.arange(N + extra)
    blk, pos = addr // 16, addr % 16
    follow = np.where(following[:extra] >= mod // 2, following[:extra] - mod, following[:extra])
    frozen = np.zeros(theta.shape, bool)
    qvals = np.zeros_like(theta)
    g_lo, g_hi = -0.5, 0.5 - 1.0 / scale
    reserved = None

    def choose(th, c):
        q = np.round(th * scale) / scale
        t = np.vstack([th[:, ccols] * scale, follow[:, ccols].astype(np.float64)])
        cc = np.vstack([c[:, ccols], np.zeros((extra, len(ccols)))])
        fixed = np.vstack([frozen[:, ccols], np.ones((extra, len(ccols)), bool)])
        value = np.vstack([np.round(qvals[:, ccols] * scale).astype(np.int64), follow[:, ccols]])
        extra_false = np.zeros((extra, len(ccols)), bool)
        r, m = residues(t, cc, blk, pos, deg[ccols], fixed, value, scale, np.vstack([reserved[:, ccols], extra_false]))
        q[:, ccols] = into_gauge(residue_round(t[:N], r[:N], m), m, scale) / scale
        return q, c * (q - th) ** 2

    def refit(th):
        mask = frozen.astype(np.float64)

        def fun(x):
            v, g = vg(jnp.asarray(mask * qvals + (1.0 - mask) * x.reshape(th.shape)))
            return float(v), (np.asarray(g, np.float64) * (1.0 - mask)).ravel()

        res = minimize(fun, np.clip(th, g_lo, g_hi).ravel(), jac=True, method='L-BFGS-B', bounds=[(g_lo, g_hi)] * th.size,
                       options={'maxiter': iters, 'maxcor': 30})
        return np.where(frozen, qvals, res.x.reshape(th.shape))

    key = jax.random.key(seed)
    current = theta
    for stage, fr in enumerate(FREE):
        need = int(round((1.0 - fr) * theta.size)) - int(frozen.sum())
        if need > 0:
            key, sub = jax.random.split(key)
            now = np.where(frozen, qvals, current)
            c = np.asarray(curvature(jnp.asarray(now), sub))
            if reserved is None:
                reserved = np.zeros(theta.shape, bool)
                reserved[:, ccols] = slack(c[:, ccols], blk[:N], pos[:N], deg[ccols])
            q, impact = choose(now, c)
            impact = last(impact, reserved)
            impact[frozen] = -np.inf
            pick = np.argsort(-impact, axis=None)[:need]
            frozen.flat[pick] = True
            qvals.flat[pick] = q.flat[pick]
        current = refit(current) if not frozen.all() else qvals
        if log:
            log(f'one-body stage {stage:2d}: frozen {frozen.mean():.4f}  error_1 {1e3 * float(np.sqrt(vg(jnp.asarray(current))[0])):7.3f} mHa')
    words = np.round(current * scale).astype(np.int64) % mod
    check(np.vstack([words, following[:extra]]), addr, deg)
    return words


def one_error(words: np.ndarray, h1p: np.ndarray, edges: np.ndarray, brot: int, order: np.ndarray | None = None) -> float:
    """error_1 with row a assigned to eigenvector order[a]."""
    import encode
    lam = np.linalg.eigvalsh(h1p)
    lam = lam if order is None else lam[order]
    V = encode.decode(words % (1 << brot), edges, brot)
    return float(np.linalg.norm((V.T * lam) @ V - h1p))


def polish(words: np.ndarray, h1p: np.ndarray, edges: np.ndarray, brot: int, period: np.ndarray, order: np.ndarray | None = None,
           sweeps: int = 20, steps=(-16, -8, -4, -2, -1, 1, 2, 4, 8, 16)) -> np.ndarray:
    """onebody.polish with each column moving by multiples of its code period, so its coded bits stay."""
    import encode
    lam = np.linalg.eigvalsh(h1p)
    lam = lam if order is None else lam[order]
    mod, lo, hi = 1 << brot, -(1 << (brot - 2)), (1 << (brot - 2)) - 1
    k = np.where(words > hi, words - mod, words).astype(np.int64)
    V = encode.decode(k % mod, edges, brot)
    M = (V.T * lam) @ V - h1p
    for _ in range(sweeps):
        moved = 0
        for j in range(len(k)):
            cands, moves = [], []
            for t in range(k.shape[1]):
                for s in steps:
                    if s % period[t] or not lo <= k[j, t] + s <= hi:
                        continue
                    row = k[j].copy()
                    row[t] += s
                    cands.append(row)
                    moves.append((t, s))
            U = encode.decode(np.array(cands) % mod, edges, brot)
            v = V[j]
            quad = np.einsum('np,pq,nq->n', U, M, U) - v @ M @ v
            gain = 2 * lam[j] * quad + lam[j] ** 2 * (2 - 2 * (U @ v) ** 2)
            i = int(np.argmin(gain))
            if gain[i] < -1e-15:
                t, s = moves[i]
                k[j, t] += s
                u = U[i]
                M += lam[j] * (np.outer(u, u) - np.outer(v, v))
                V[j] = u
                moved += 1
        if not moved:
            break
    return k % mod


def refresh(h1p: np.ndarray, edges: np.ndarray, brot: int, deg: np.ndarray, following: np.ndarray, kicks: int = 10,
            seed: int = 0, mode: str = 'strong', **_) -> np.ndarray:
    """onebody.refresh for these codes: progressive rounding, polish, kicks. Stands in for it during refine and refit."""
    period = 1 << (deg > 0).sum(axis=1)
    mod, lo, hi = 1 << brot, -(1 << (brot - 2)), (1 << (brot - 2)) - 1
    order = one_order(np.linalg.eigvalsh(h1p), mode)
    k = polish(quantize_onebody(h1p, edges, brot, deg, following, order), h1p, edges, brot, period, order)
    best = one_error(k, h1p, edges, brot, order)
    rng = np.random.default_rng(seed)
    for _ in range(kicks):
        trial = k.copy()
        for r in rng.choice(len(k), 4, replace=False):
            cols = rng.choice(trial.shape[1], 6, replace=False)
            moved = trial[r, cols] + rng.choice([-1, 1], 6) * period[cols]
            signed = np.where(moved > hi, moved - mod, moved)
            trial[r, cols] = np.where((signed >= lo) & (signed <= hi), moved, trial[r, cols])
        trial = polish(trial % mod, h1p, edges, brot, period, order)
        e = one_error(trial, h1p, edges, brot, order)
        if e < best:
            best, k = e, trial
    check(np.vstack([k, following[:-len(k) % 16]]), np.arange(len(k) + (-len(k) % 16)), deg)
    return k


def output_degrees(deg: np.ndarray, k: int, j: int = 5, brot: int = 8) -> np.ndarray:
    """The code of each output bit of circuit k's delta (output o = (brot - 1) word + bit): the larger of both batches'."""
    out = np.zeros(j * (brot - 1), np.int64)
    for w in range(j):
        col = k * j + w
        if col >= len(deg):
            continue
        for bit in range(brot - 1):
            now, before = deg[col, bit], deg[col - j, bit] if k else 99
            if now and before:
                out[w * (brot - 1) + bit] = now if not k else max(now, before)
    return out


def layout(out: np.ndarray, sizes: dict | None = None) -> tuple[list[int], list[int]]:
    """Output order and group sizes: free outputs first, then by falling degree; RM(1, 4) outputs in fives."""
    sizes = {0: 7, 3: 7, 2: 7, 1: 5, **(sizes or {})}
    order, groups = [], []
    for d in (0, 3, 2, 1):
        o = [int(i) for i in np.flatnonzero(out == d)]
        order += o
        groups += [sizes[d]] * (len(o) // sizes[d]) + ([len(o) % sizes[d]] if len(o) % sizes[d] else [])
    return order, groups


def pad(delta: np.ndarray, out: np.ndarray, brot: int = 8) -> np.ndarray:
    """Rows past the table padded to whole 16-address blocks, each coded output completed to a word of its code."""
    A = len(delta)
    full = np.concatenate([delta, np.zeros((-A % 16, delta.shape[1]), delta.dtype)])
    n = A % 16
    if n:
        b0 = A - n
        for o in np.flatnonzero(out):
            w, bit = int(o) // (brot - 1), int(o) % (brot - 1)
            cw = code(int(out[o]))
            have = (full[b0:b0 + n, w] >> bit) & 1
            word = cw[np.flatnonzero(np.all(cw[:, :n] == have, axis=1))[0]].astype(np.int64)
            full[b0:b0 + 16, w] = (full[b0:b0 + 16, w] & ~(1 << bit)) | (word << bit)
    return full


def build_family(words: np.ndarray, deg: np.ndarray, brot: int = 8, j: int = 5, lowbits: int = 4, trials: int = 6,
                 jobs: int = 8, sizes: dict | None = None, log=print) -> list:
    """tensorqrom.build_family for these codes."""
    from concurrent.futures import ProcessPoolExecutor
    import tensorqrom as tq
    from fourqrom import batch_deltas
    A = len(words)
    n_sel = max(1, (A - 1).bit_length())
    deltas, tasks = list(batch_deltas(words, j)), []
    for k, d in enumerate(deltas):
        out = output_degrees(deg, k, j, brot)
        deltas[k] = d = pad(d, out, brot)
        perm, groups = layout(out, sizes)
        log(f'circuit {k}: outputs by degree { {int(x): int((out == x).sum()) for x in np.unique(out)} }, groups {groups}')
        tasks.append((d, n_sel, brot, lowbits, groups, trials, k, perm))
    with ProcessPoolExecutor(jobs) as ex:
        results = list(ex.map(tq._one, tasks))
    log('products per circuit: ' + ' '.join(str(len(t)) for t, _ in results))
    groups = tq.low_groups(lowbits)
    return [tq.build_circuit(d, t, n_sel, brot, lowbits, groups=groups, scratch=True) if g
            else tq.build_circuit(d, t, n_sel, brot, lowbits) for d, (t, g) in zip(deltas, results)]


def bound(words: np.ndarray, addr: np.ndarray, deg: np.ndarray) -> float:
    """Share of block-column-bit triples whose bits are in their code (a diagnostic)."""
    good = total = 0
    for col, bit in zip(*np.nonzero(deg)):
        cw = code(int(deg[col, bit]))
        bits = (words[:, col] >> bit) & 1
        for b in np.unique(addr // 16):
            rows = np.flatnonzero(addr // 16 == b)
            total += 1
            good += bool(np.any(np.all(cw[:, addr[rows] % 16] == bits[rows], axis=1)))
    return good / max(total, 1)


__all__ = ['build_family', 'check', 'code', 'math', 'parse', 'quantize_onebody', 'refresh', 'residues']
