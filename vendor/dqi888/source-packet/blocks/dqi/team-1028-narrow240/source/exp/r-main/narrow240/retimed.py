"""Retire the paid N1 source and retain N0 instead:250T/15fresh.

The earlier cached287 graph and reviewed streamed.py remain unchanged.
This is one completed retiming, not a family-level count claim.
"""
from streamed import *


def scale6_log_key(b, x, key, inverse=False):
    """Both GF8 halves times alpha^(+/-key),18T, no scratch."""
    f = ar.field(3)
    ops = linear_ops([f.mul(2, 1 << i) for i in range(3)])
    for j in range(3):
        before = [f.pow(1 << i, 1 << ((3 - j) % 3)) for i in range(3)]
        after = [f.pow(1 << i, 1 << j) for i in range(3)]
        for half in (x[:3], x[3:]):
            ar.linear_inplace(b, half, before)
            for op, i, t in (reversed(ops) if inverse else ops):
                if op == 'swap':
                    b.cswap(key[j], half[i], half[t])
                else:
                    b.ccx(key[j], half[i], half[t])
            ar.linear_inplace(b, half, after)


def inverse6_context_begin27(b, x):
    """x->inv0(x), retain log(inv(norm(oldx)))3;27T/3fresh."""
    ar.linear_inplace(b, x, TO6)
    key = b.alloc_qubits(3)
    norm_xor_noscratch(b, x, key, K6)
    permutation3(b, key, 'log_inverse')
    b.cx(x[3:], x[:3])
    scale6_log_key(b, x, key)
    ar.linear_inplace(b, x, FROM6)
    return key


def inverse6_context_end21(b, x, key):
    """Use the retained log key, invert back and close its quadratic mask."""
    ar.linear_inplace(b, x, TO6)
    b.cx(x[3:], x[:3])
    scale6_log_key(b, x, key, inverse=True)
    permutation3(b, key, 'log_inverse', reverse=True)
    ar._erase_norm(b, x, key, K6)
    b.free(key)
    ar.linear_inplace(b, x, FROM6)


def source_low6(b, A, g, target):
    """Low GF64 half of Norm24(A,g),30T, source bank6 included."""
    source_linear(b, A, g, target, 0)
    ar.linear_inplace(b, A, TO12)
    ar.linear_inplace(b, g, TO12)
    mul_xor_noscratch(b, A[:6], g[:6], target)
    scale_constant(b, target, ar.field(6).invert(K12))
    mul_xor_noscratch(b, A[6:], g[6:], target)
    scale_constant(b, target, K12)
    ar.linear_inplace(b, g, FROM12)
    ar.linear_inplace(b, A, FROM12)


def source_high_chunk(b, A, g, target, chunk):
    """One GF8 chunk of high GF64 half of Norm24(A,g),24T."""
    source_linear(b, A, g, target, 1, chunk)
    ar.linear_inplace(b, A, TO12)
    ar.linear_inplace(b, g, TO12)
    b.cx(A[6:], A[:6])
    b.cx(g[6:], g[:6])
    product6_chunk(b, A[:6], g[:6], target, chunk)
    b.cx(g[6:], g[:6])
    b.cx(A[6:], A[:6])
    product6_chunk(b, A[:6], g[:6], target, chunk)
    ar.linear_inplace(b, g, FROM12)
    ar.linear_inplace(b, A, FROM12)


def phase_rational_retimed250(b, A, g, mask, paired_key=False):
    """Complete ordinary-D phase m dot g/Norm24(A,g),250T/15fresh."""
    nz = nonzero_classical(b, mask)
    b.push_condition(nz)
    R = b.alloc_qubits(6)
    with b.mark('source_high'):
        source_high6(b, A, g, R)
    D = b.alloc_qubits(6)
    f = ar.field(6)
    ar.linear_xor(b, R, D, [f.mul(K12, v) for v in ar.square_columns(6)])
    for chunk in (0, 1):
        P = b.alloc_qubits(3)
        with b.mark('source_low_for_norm'):
            source_low_chunk(b, A, g, P, chunk)
        ar.linear_xor(b, P, D, [f.square(FROM6[i + 3 * chunk]) for i in range(3)])
        with b.mark('nested_norm_product'):
            partial_product(b, P, chunk, R, D)
        erase_part(b, A, g, P, 0, chunk)
        b.free(P)
    with b.mark('inverse_nested_norm'):
        if paired_key:
            key = inverse6_context_begin27(b, D)
        else:
            inverse6_unitary29(b, D)
    with b.mark('high_numerator_phase'):
        product_phase_virtual(b, R, D, g, mask, both=True)
    # The N1 character has been paid. Its source erasure is quadratic/free;
    # its bank can now hold the whole N0, avoiding two partial phase products.
    erase_part(b, A, g, R, 1)
    b.free(R)
    R = b.alloc_qubits(6)
    with b.mark('source_low_for_phase'):
        source_low6(b, A, g, R)
    with b.mark('low_numerator_phase'):
        product_phase_virtual(b, R, D, g, mask, both=False)
    with b.mark('restore_nested_norm'):
        if paired_key:
            inverse6_context_end21(b, D, key)
        else:
            inverse6_unitary29(b, D)
    dm = b.alloc_bits(6)
    b.hmr(D, dm)
    b.free(D)
    ar.phase_linear(b, R, dm, ar.square_columns(6))
    source_phase(b, A, g, dm, [f.mul(K12, f.square(v)) for v in part_columns(1)])
    # D's measurement has freed all six of its wires. Rebuild the whole N1
    # bank here (30T), rather than two separately sourced GF8 chunks (48T).
    P = b.alloc_qubits(6)
    with b.mark('source_high_for_closure'):
        source_high6(b, A, g, P)
    ar.phase_product(b, P, R, dm)
    erase_part(b, A, g, P, 1)
    b.free(P)
    b.free(dm)
    erase_part(b, A, g, R, 0)
    b.free(R)
    b.pop_condition()
    b.free(nz)


def phase_rational_retimed240(b, A, g, mask):
    """Keep the 3-bit log key through the bank swap:240T/15fresh."""
    phase_rational_retimed250(b, A, g, mask, paired_key=True)
