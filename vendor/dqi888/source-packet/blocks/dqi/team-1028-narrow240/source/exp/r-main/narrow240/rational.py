"""Exact rational character baselines; all physical banks are counted.

No circuit in this module is claimed to meet the <=15-fresh target yet.
The source-preserving composition is 132 executed T / 24 fresh qubits.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'exp/r-main/narrow240'), str(ROOT / 'playbook/kit/decoder'),
                str(ROOT / 'playbook/kit')]
from phase_quantum import phase_inverse12_quantum90
from phase_core import ar, K
from exp.noscratch.kernels import mul_xor_noscratch


def norm_source(b, A, g, out, F=None):
    """out ^= A^2 + A*g + (K+F*(K+1))*g^2, 42T/0 scratch."""
    f = ar.field(12)
    ar.linear_xor(b, A, out, ar.square_columns(12))
    ar.linear_xor(b, g, out, [f.mul(K, v) for v in ar.square_columns(12)])
    if F is not None:
        for j, v in enumerate(ar.square_columns(12)):
            for k in ar.bits(f.mul(K ^ 1, v)):
                b.ccx(F, g[j], out[k])
    mul_xor_noscratch(b, A, g, out)


def erase_norm_source(b, A, g, out, F=None):
    """Every source measurement is closed, including the F*g^2 term."""
    m = b.alloc_bits(12)
    b.hmr(out, m)
    f = ar.field(12)
    ar.phase_linear(b, A, m, ar.square_columns(12))
    ar.phase_linear(b, g, m, [f.mul(K, v) for v in ar.square_columns(12)])
    if F is not None:
        for j, v in enumerate(ar.square_columns(12)):
            for k in ar.bits(f.mul(K ^ 1, v)):
                b.ccz(F, g[j], m[k])
    ar.phase_product(b, A, g, m)
    b.free(m)


def coefficient_ops(b, mask):
    """Classical elimination transcript for L_m(g)[j] = m dot (g*2^j).

    For m!=0, L_m is invertible by nondegeneracy of the field product.
    The transcript contains only classical controls, never quantum data.
    Return its row-reduction operations and allocated classical registers.
    Reverse order applies L_m; forward order restores g.
    """
    n = len(mask)
    f = ar.field(n)
    rows = [b.alloc_bits(n) for _ in range(n)]
    for j in range(n):
        b.bit_store(rows[j], False)
        for i in range(n):
            for k in ar.bits(f.mul(1 << i, 1 << j)):
                b.cx(mask[k], rows[j][i])
    ops = []
    allocated = list(rows)
    for j in range(n):
        seen = b.alloc_bits(1)[0]
        b.bit_store(seen, False)
        allocated.append([seen])
        for i in range(j, n):
            p = b.alloc_bits(1)[0]
            allocated.append([p])
            b.bit_store(p, False)
            b.x(seen)
            b.push_condition(seen)
            b.cx(rows[i][j], p)
            b.pop_condition()
            b.x(seen)
            b.bit_store(seen, True, control=p)
            if i != j:
                b.push_condition(p)
                b.swap(rows[i], rows[j])
                b.pop_condition()
                ops.append(('swap', i, j, p))
        for i in range(n):
            if i == j:
                continue
            c = b.alloc_bits(1)[0]
            allocated.append([c])
            b.bit_store(c, False)
            b.cx(rows[i][j], c)
            b.push_condition(c)
            b.cx(rows[j], rows[i])
            b.pop_condition()
            ops.append(('cx', j, i, c))
    return ops, allocated


def apply_coefficient_ops(b, g, ops, reverse=False):
    for op, i, j, cond in (reversed(ops) if reverse else ops):
        b.push_condition(cond)
        getattr(b, op)(g[i], g[j])
        b.pop_condition()


def nonzero_classical(b, mask):
    nz = b.alloc_bits(1)[0]
    b.bit_store(nz, False)
    for q in mask:
        b.bit_store(nz, True, control=q)
    return nz


def phase_rational_baseline(b, A, g, mask, F=None):
    """Phase mask dot g/Norm(A,g), exact; 24 fresh, 132T at F absent.

    With F present the source F*g^2 CCXs add 53 static/mean T for the
    supplied K and tower basis. The F-free lead split avoids those gates.
    """
    nz = nonzero_classical(b, mask)
    b.push_condition(nz)
    N = b.alloc_qubits(12)
    with b.mark('source'):
        norm_source(b, A, g, N, F)
    ops, allocated = coefficient_ops(b, mask)
    apply_coefficient_ops(b, g, ops, reverse=True)
    with b.mark('inverse_character'):
        phase_inverse12_quantum90(b, N, g)
    apply_coefficient_ops(b, g, ops)
    for reg in allocated:
        b.free(reg)
    with b.mark('source_cleanup'):
        erase_norm_source(b, A, g, N, F)
    b.free(N)
    b.pop_condition()
    b.free(nz)
