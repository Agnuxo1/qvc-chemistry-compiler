"""Four chart characters as one inverse character with a virtual affine mask.

Unlike materializing the mask bank, a classical first-nonzero pivot exposes
each requested affine parity directly in A. Preserves A, g, F, and masks.
"""
from rational import *
from phase_quantum import phase_inverse6_9
from exp.noscratch.schedules import norm_xor_noscratch, inverse_stream_noscratch
from exp.mul99.phase36 import phase_classical_parity


def affine_inverse_g_character(b, A, g, masks, extra_F_mask=None, F=None):
    """Pay (I + R*A + H*A^2)/g as binary-dot characters, 90T/12fresh."""
    to, frm, kval = ar.tower(12)
    ar.linear_inplace(b, g, to)
    D = b.alloc_qubits(6)
    norm_xor_noscratch(b, g, D, kval)
    dm = inverse_stream_noscratch(b, D)
    ar._phase_norm(b, g, dm, kval)
    b.free(dm)
    f = ar.field(12)
    b.cx(g[6:], g[:6])
    for seg in (0, 1):
        x = g[:6] if seg == 0 else g[6:]
        for sm, vv in ar.tensor(6):
            h = ar.apply(frm, vv << (6 * seg))
            co = b.alloc_bits(12 + (extra_F_mask is not None))
            offset = b.alloc_bits(1)[0]
            b.bit_store(co, False)
            b.bit_store(offset, False)
            for j in ar.bits(h):
                b.cx(masks['i'][j], offset)
            for i in range(12):
                for j in ar.bits(f.mul(1 << i, h)):
                    b.cx(masks['r'][j], co[i])
                for j in ar.bits(f.mul(f.square(1 << i), h)):
                    b.cx(masks['h'][j], co[i])
            if extra_F_mask is not None:
                for j in ar.bits(h):
                    b.cx(extra_F_mask[j], co[12])
            ix = list(ar.bits(sm))
            p = ix[0]
            for i in ix[1:]:
                b.cx(x[i], x[p])
                b.cx(D[i], D[p])
            b.ccz(x[p], D[p], offset)
            source = list(A) + ([F] if extra_F_mask is not None else [])
            phase_classical_parity(b, x[p], D[p], source, co)
            for i in reversed(ix[1:]):
                b.cx(D[i], D[p])
                b.cx(x[i], x[p])
            b.free([offset])
            b.free(co)
    b.cx(g[6:], g[:6])
    im = b.alloc_bits(6)
    b.hmr(D, im)
    b.free(D)
    D = b.alloc_qubits(6)
    norm_xor_noscratch(b, g, D, kval)
    phase_inverse6_9(b, D, im)
    b.free(im)
    ar._erase_norm(b, g, D, kval)
    b.free(D)
    ar.linear_inplace(b, g, frm)


def phase_core90(b, A, g, F, masks, extra_F_mask=None):
    b.cz(g, masks['g'])
    b.cz(A, masks['h'])
    f = ar.field(12)
    for j in range(12):
        for k in ar.bits(f.mul(K, 1 << j)):
            b.cz(g[j], masks['h'][k])
        for k in ar.bits(f.mul(K ^ 1, 1 << j)):
            b.ccz(F, g[j], masks['h'][k])
    affine_inverse_g_character(b, A, g, masks, extra_F_mask, F)
