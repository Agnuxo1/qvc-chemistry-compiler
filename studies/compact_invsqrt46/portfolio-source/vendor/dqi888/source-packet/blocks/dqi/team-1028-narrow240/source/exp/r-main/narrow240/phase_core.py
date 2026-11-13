"""Direct G/I/H/R chart characters; T=1/(gq) is deliberately NOT paid."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(root/'playbook/kit/decoder'),str(root/'playbook/kit')]
from exp.decoder.common import *
from exp.noscratch.schedules import inverse_stream_noscratch
from exp.mul99.phase36 import phase_inverse36_pivot

def phase_core(b,A,g,F,masks):
 """Pay G.g+I/g+H.(gq)+R.(A/g), q=(A/g)^2+A/g+K+F(K+1).

 Promise g!=0, and F=>A=0. Preserve A,g,F and every classical mask.
 168T/12 private, no ratio materialization. Does not pay T/(gq).
 """
 b.cz(g,masks['g']);b.cz(A,masks['h'])
 f=ar.field(12)
 for j in range(12):
  for k in ar.bits(f.mul(K,1<<j)):b.cz(g[j],masks['h'][k])
  for k in ar.bits(f.mul(K^1,1<<j)):b.ccz(F,g[j],masks['h'][k])
 z=inverse_stream_noscratch(b,g)
 b.cz(g,masks['i']);ar.phase_product(b,A,g,masks['r'])
 ar.linear_inplace(b,A,ar.square_columns(12));ar.phase_product(b,A,g,masks['h']);ar.linear_inplace(b,A,[ar.field(12).pow(1<<j,2048)for j in range(12)])
 zi=inverse_stream_noscratch(b,g)
 b.cz(g,z);b.free(z);phase_inverse36_pivot(b,g,zi);b.free(zi)
