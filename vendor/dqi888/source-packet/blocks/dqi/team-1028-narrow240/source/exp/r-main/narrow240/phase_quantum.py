"""Direct quantum-coefficient inverse12 character:90T/12private."""
from phase_core import *
from types import FunctionType
from exp.noscratch.schedules import norm_xor_noscratch
from exp.arithmetic.lowwidth import phase_product_quantum,phase_inverse_generic6
from exp.noscratch.kernels import inverse3_noscratch
phase_inverse6_9=FunctionType(phase_inverse_generic6.__code__,dict(phase_inverse_generic6.__globals__,inverse=inverse3_noscratch),'phase_inverse6_9')

def phase_inverse12_quantum90(b,x,co):
 to,frm,k=ar.tower(12);ar.linear_inplace(b,x,to)
 tr=[sum(((frm[j]>>i)&1)<<j for j in range(12))for i in range(12)]
 ar.linear_inplace(b,co,tr)
 N=b.alloc_qubits(6);norm_xor_noscratch(b,x,N,k)
 nm=inverse_stream_noscratch(b,N);ar._phase_norm(b,x,nm,k);b.free(nm)
 b.cx(x[6:],x[:6]);phase_product_quantum(b,x[:6],N,co[:6]);phase_product_quantum(b,x[6:],N,co[6:]);b.cx(x[6:],x[:6])
 im=b.alloc_bits(6);b.hmr(N,im);b.free(N)
 N=b.alloc_qubits(6);norm_xor_noscratch(b,x,N,k);phase_inverse6_9(b,N,im);b.free(im)
 ar._erase_norm(b,x,N,k);b.free(N);ar.linear_inplace(b,x,frm);ar.linear_inplace(b,co,ar.inverse_columns(tr))
