"""Frozen b-width chart with its complete paired character replaced only."""
import frozen_chart as frozen
from frozen_chart import *
from core90 import phase_core90
from retimed import phase_rational_retimed240


def pay_charts(b, D, forward, reverse):
    A, g = D[:12], D[12:]
    F = ref.guarded.fresh_zero_flag(b, g)
    b.cz(F, forward['f'][0])
    b.cz(F, reverse['f'][0])
    b.free(forward['f'])
    b.free(reverse['f'])
    b.z(reverse['r'][0])
    b.cz(F, reverse['r'][0])
    masks = dict(g=add_masks(b, forward['g'], reverse['t']),
                 i=add_masks(b, forward['i'], reverse['h']),
                 h=add_masks(b, forward['h'], reverse['i']),
                 t=add_masks(b, forward['t'], reverse['g']),
                 r=add_masks(b, forward['r'], reverse['r']))
    b.cswap(F, A, g)
    with b.mark('direct_core90'):
        phase_core90(b, A, g, F, masks, extra_F_mask=masks['t'])
    for key in ('g', 'i', 'h', 'r'):
        b.free(masks[key])
    b.cswap(F, A, g)
    ref.guarded.zero_toggle(b, g, F)
    b.free(F)
    with b.mark('direct_residual240'):
        phase_rational_retimed240(b, A, g, masks['t'])
    b.free(masks['t'])


external_node_chain = clone(frozen.external_node_chain,
                            dict(frozen.external_node_chain.__globals__, pay_charts=pay_charts))
