"""Original-D rational phase with small-field streaming and exact I6.

Named schedule: retain six N1 bits; stream three N0 bits at a time; D6
is inverted by a unitary 29T/3-fresh circuit, hence no quartic inverse mask
is deferred. The two cubic-source inverse calls cost 58T together.
Expected complete count: 102+29+87+29+48 = 295T, 15 fresh.
"""
import json
from functools import lru_cache
from rational import *
from exp.noscratch.schedules import norm_xor_noscratch
from exp.mul99.phase36 import phase_classical_parity

PERMS = json.loads((Path(__file__).resolve().parent / 'permutations3.json').read_text())


def permutation3(b, x, name, reverse=False):
    gates = PERMS[name]['gates']
    for gate in (reversed(gates) if reverse else gates):
        getattr(b, gate[0])(*(x[i] for i in gate[1:]))


def linear_ops(columns):
    n = len(columns)
    rows = [sum(((c >> i) & 1) << j for j, c in enumerate(columns)) for i in range(n)]
    ops = []
    for j in range(n):
        p = next(i for i in range(j, n) if rows[i] >> j & 1)
        if p != j:
            rows[p], rows[j] = rows[j], rows[p]
            ops.append(('swap', p, j))
        for i in range(n):
            if i != j and rows[i] >> j & 1:
                rows[i] ^= rows[j]
                ops.append(('cx', j, i))
    return tuple(reversed(ops))


def controlled_alpha(b, x, control):
    f = ar.field(3)
    ops = linear_ops([f.mul(2, 1 << j) for j in range(3)])
    assert len(ops) == 3
    for op, i, j in ops:
        if op == 'swap':
            b.cswap(control, x[i], x[j])
        else:
            b.ccx(control, x[i], x[j])


def inverse6_unitary29(b, x):
    """Exact inv0 permutation, 29T / 3 clean scratch, no deferred masks.

    norm E is converted directly to log(inv(E)); logarithm 7 represents 0.
    alpha^7=1, so the scale is reversible even on E=0. There x itself is0.
    After both scalings, antilog changes E into norm(inv0(x)), closed by HMR.
    """
    to, frm, kval = ar.tower(6)
    ar.linear_inplace(b, x, to)
    E = b.alloc_qubits(3)
    norm_xor_noscratch(b, x, E, kval)
    permutation3(b, E, 'log_inverse')
    b.cx(x[3:], x[:3])
    f = ar.field(3)
    for j in range(3):
        # F^j M_alpha F^-j = M_(alpha^(2^j)); F has order3.
        before = [f.pow(1 << i, 1 << ((3 - j) % 3)) for i in range(3)]
        after = [f.pow(1 << i, 1 << j) for i in range(3)]
        for half in (x[:3], x[3:]):
            ar.linear_inplace(b, half, before)
            controlled_alpha(b, half, E[j])
            ar.linear_inplace(b, half, after)
    permutation3(b, E, 'log', reverse=True)
    ar._erase_norm(b, x, E, kval)
    b.free(E)
    ar.linear_inplace(b, x, frm)


TO12, FROM12, K12 = ar.tower(12)
TO6, FROM6, K6 = ar.tower(6)


@lru_cache(None)
def part_columns(half, chunk=None):
    columns = [(ar.apply(TO12, 1 << j) >> (6 * half)) & 63 for j in range(12)]
    if chunk is not None:
        columns = [(ar.apply(TO6, v) >> (3 * chunk)) & 7 for v in columns]
    return tuple(columns)


def source_phase(b, A, g, mask, columns):
    """Phase mask dot columns(Norm24(A,g)); quadratic closure is free."""
    fullmask = b.alloc_bits(12)
    b.bit_store(fullmask, False)
    for j, value in enumerate(columns):
        for i in ar.bits(value):
            b.cx(mask[i], fullmask[j])
    f = ar.field(12)
    ar.phase_linear(b, A, fullmask, ar.square_columns(12))
    ar.phase_linear(b, g, fullmask, [f.mul(K, v) for v in ar.square_columns(12)])
    ar.phase_product(b, A, g, fullmask)
    b.free(fullmask)


def erase_part(b, A, g, target, half, chunk=None):
    mask = b.alloc_bits(len(target))
    b.hmr(target, mask)
    source_phase(b, A, g, mask, part_columns(half, chunk))
    b.free(mask)


def source_linear(b, A, g, target, half, chunk=None, omitted=None):
    cols = part_columns(half, chunk)
    if omitted is not None:
        cols = [v & ~(1 << omitted) for v in cols]
    f = ar.field(12)
    ar.linear_xor(b, A, target, [ar.apply(cols, v) for v in ar.square_columns(12)])
    ar.linear_xor(b, g, target, [ar.apply(cols, f.mul(K, v)) for v in ar.square_columns(12)])


def source_high6(b, A, g, target):
    """High GF64 component of N=Norm24(A,g), 30T / no scratch."""
    source_linear(b, A, g, target, 1)
    ar.linear_inplace(b, A, TO12)
    ar.linear_inplace(b, g, TO12)
    b.cx(A[6:], A[:6])
    b.cx(g[6:], g[:6])
    mul_xor_noscratch(b, A[:6], g[:6], target)
    b.cx(g[6:], g[:6])
    b.cx(A[6:], A[:6])
    mul_xor_noscratch(b, A[:6], g[:6], target)
    ar.linear_inplace(b, g, FROM12)
    ar.linear_inplace(b, A, FROM12)


def scale_constant(b, x, c):
    f = ar.field(len(x))
    ar.linear_inplace(b, x, [f.mul(c, 1 << i) for i in range(len(x))])


def product3_projected(b, x, y, target, omitted=None):
    if omitted is None:
        mul_xor_noscratch(b, x, y, target)
    else:
        from exp.noscratch.kernels import tensor_xor_noscratch
        terms = [(sm, vv & ~(1 << omitted)) for sm, vv in ar.tensor(3)
                 if vv & ~(1 << omitted)]
        tensor_xor_noscratch(b, x, y, target, terms)


def product6_chunk(b, x, y, target, chunk, omitted=None):
    """One GF8 component of a GF64 product, 12T / no scratch."""
    ar.linear_inplace(b, x, TO6)
    ar.linear_inplace(b, y, TO6)
    if chunk == 0:
        mul_xor_noscratch(b, x[:3], y[:3], target)
        scale_constant(b, target, ar.field(3).invert(K6))
        mul_xor_noscratch(b, x[3:], y[3:], target)
        scale_constant(b, target, K6)
    else:
        b.cx(x[3:], x[:3])
        b.cx(y[3:], y[:3])
        product3_projected(b, x[:3], y[:3], target, omitted)
        b.cx(y[3:], y[:3])
        b.cx(x[3:], x[:3])
        product3_projected(b, x[:3], y[:3], target, omitted)
    ar.linear_inplace(b, y, FROM6)
    ar.linear_inplace(b, x, FROM6)


def source_low_chunk(b, A, g, target, chunk, cached=None):
    """One GF8 component of low GF64 half of Norm24(A,g), 24T."""
    omitted = 0 if cached is not None else None
    assert cached is None or chunk == 1
    if cached is not None:
        b.cx(cached, target[0])
    source_linear(b, A, g, target, 0, chunk, omitted=omitted)
    ar.linear_inplace(b, A, TO12)
    ar.linear_inplace(b, g, TO12)
    product6_chunk(b, A[:6], g[:6], target, chunk, omitted=omitted)
    scale_constant(b, A[6:], K12)
    product6_chunk(b, A[6:], g[6:], target, chunk, omitted=omitted)
    scale_constant(b, A[6:], ar.field(6).invert(K12))
    ar.linear_inplace(b, g, FROM12)
    ar.linear_inplace(b, A, FROM12)


def partial_product(b, p, chunk, x, output):
    """output6 ^= embed(p3)*x6, 12T/no scratch, canonical GF64 x/out."""
    ar.linear_inplace(b, x, TO6)
    ar.linear_inplace(b, output, TO6)
    if chunk == 0:
        mul_xor_noscratch(b, p, x[:3], output[:3])
        mul_xor_noscratch(b, p, x[3:], output[3:])
    else:
        scale_constant(b, output[:3], ar.field(3).invert(K6))
        mul_xor_noscratch(b, p, x[3:], output[:3])
        scale_constant(b, output[:3], K6)
        b.cx(x[3:], x[:3])
        mul_xor_noscratch(b, p, x[:3], output[3:])
        b.cx(x[3:], x[:3])
    ar.linear_inplace(b, output, FROM6)
    ar.linear_inplace(b, x, FROM6)


def coefficient_parity(b, g, mask, h, a, c):
    co = b.alloc_bits(12)
    b.bit_store(co, False)
    f = ar.field(12)
    for j in range(12):
        for i in ar.bits(f.mul(1 << j, h)):
            b.cx(mask[i], co[j])
    phase_classical_parity(b, a, c, g, co)
    b.free(co)


def product_phase_virtual(b, x, y, g, mask, both):
    """m dot g*embed(x6*y6), <=15T, virtual mask in live g."""
    for sm, vv in ar.tensor(6):
        h = ar.apply(FROM12, vv | ((vv << 6) if both else 0))
        ix = list(ar.bits(sm))
        p = ix[0]
        for i in ix[1:]:
            b.cx(x[i], x[p])
            b.cx(y[i], y[p])
        coefficient_parity(b, g, mask, h, x[p], y[p])
        for i in reversed(ix[1:]):
            b.cx(y[i], y[p])
            b.cx(x[i], x[p])


def partial_phase(b, p, chunk, x, g=None, mask=None, classical=None):
    """Phase embed(p3)*x6 with virtual g-dependent or classical mask."""
    ar.linear_inplace(b, x, TO6)
    configs = [(x[:3], 0, 1), (x[3:], 1, 1)] if chunk == 0 else [(x[3:], 0, K6), (x[:3], 1, 1)]
    if chunk:
        b.cx(x[3:], x[:3])
    for controls, segment, constant in configs:
        for sm, vv in ar.tensor(3):
            vector = ar.apply(FROM6, ar.field(3).mul(constant, vv) << (3 * segment))
            ix = list(ar.bits(sm))
            pivot = ix[0]
            for i in ix[1:]:
                b.cx(p[i], p[pivot])
                b.cx(controls[i], controls[pivot])
            if classical is not None:
                for i in ar.bits(vector):
                    b.ccz(p[pivot], controls[pivot], classical[i])
            else:
                h = ar.apply(FROM12, vector)
                coefficient_parity(b, g, mask, h, p[pivot], controls[pivot])
            for i in reversed(ix[1:]):
                b.cx(controls[i], controls[pivot])
                b.cx(p[i], p[pivot])
    if chunk:
        b.cx(x[3:], x[:3])
    ar.linear_inplace(b, x, FROM6)


def phase_rational_streamed295(b, A, g, mask, cache_source_bit=False):
    """Phase m dot g/Norm24(A,g), 295T/15fresh or cached 287T/16fresh."""
    nz = nonzero_classical(b, mask)
    b.push_condition(nz)
    R = b.alloc_qubits(6)
    with b.mark('source_high'):
        source_high6(b, A, g, R)
    D = b.alloc_qubits(6)
    f = ar.field(6)
    ar.linear_xor(b, R, D, [f.mul(K12, v) for v in ar.square_columns(6)])
    cached = None
    for chunk in (0, 1):
        P = b.alloc_qubits(3)
        with b.mark('source_low_for_norm'):
            source_low_chunk(b, A, g, P, chunk)
        if cache_source_bit and chunk == 1:
            cached = b.alloc_qubits(1)[0]
            b.cx(P[0], cached)
        ar.linear_xor(b, P, D, [f.square(FROM6[i + 3 * chunk]) for i in range(3)])
        with b.mark('nested_norm_product'):
            partial_product(b, P, chunk, R, D)
        erase_part(b, A, g, P, 0, chunk)
        b.free(P)
    with b.mark('inverse_nested_norm'):
        inverse6_unitary29(b, D)
    with b.mark('retained_numerator_phase'):
        product_phase_virtual(b, R, D, g, mask, both=True)
    for chunk in (0, 1):
        P = b.alloc_qubits(3)
        with b.mark('source_low_for_phase'):
            source_low_chunk(b, A, g, P, chunk, cached=cached if chunk == 1 else None)
        with b.mark('streamed_numerator_phase'):
            partial_phase(b, P, chunk, D, g=g, mask=mask)
        erase_part(b, A, g, P, 0, chunk)
        b.free(P)
    with b.mark('restore_nested_norm'):
        inverse6_unitary29(b, D)
    dm = b.alloc_bits(6)
    b.hmr(D, dm)
    b.free(D)
    ar.phase_linear(b, R, dm, [f.mul(K12, v) for v in ar.square_columns(6)])
    source_phase(b, A, g, dm, [f.square(v) for v in part_columns(0)])
    for chunk in (0, 1):
        P = b.alloc_qubits(3)
        with b.mark('source_low_for_closure'):
            source_low_chunk(b, A, g, P, chunk, cached=cached if chunk == 1 else None)
        partial_phase(b, P, chunk, R, classical=dm)
        erase_part(b, A, g, P, 0, chunk)
        b.free(P)
    if cached is not None:
        cm = b.alloc_bits(1)
        b.hmr(cached, cm[0])
        source_phase(b, A, g, cm, [v & 1 for v in part_columns(0, 1)])
        b.free(cm)
        b.free([cached])
    b.free(dm)
    erase_part(b, A, g, R, 1)
    b.free(R)
    b.pop_condition()
    b.free(nz)


def phase_rational_streamed287(b, A, g, mask):
    """Retain one quadratic source bit: 287T/16fresh, all closures included."""
    phase_rational_streamed295(b, A, g, mask, cache_source_bit=True)
