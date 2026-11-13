"""Consume the GF64 norm into its inverse; rebuild it after part scales."""
from types import FunctionType,SimpleNamespace
import inspect
from final_decoder import synthesis as folds
from exp.noscratch.schedules import inverse_stream_noscratch

def clone(fn,env):
 out=FunctionType(fn.__code__,env,fn.__name__,fn.__defaults__,fn.__closure__)
 out.__kwdefaults__=fn.__kwdefaults__;return out

def make_synthesize(ref):
 source=inspect.getsource(folds.divide_fused)
 before='    t = inverse6_xor20(b, M)\n'
 after='''    inverse_mask = inverse_stream_noscratch(b, M)
    t = M
    part_masks = []
'''
 assert source.count(before)==1;source=source.replace(before,after)
 before='            ar.erase_product(b, out, M, part)\n'
 after='''            pm = b.alloc_bits(6); b.hmr(part, pm); part_masks.append(pm)
'''
 assert source.count(before)==1;source=source.replace(before,after)
 before='    for off, m in zip((0, 12), masks):\n'
 after='''    M = b.alloc_qubits(6)
    ar.linear_inplace(b, N, to)
    norm_xor_noscratch(b, N, M, k6)
    ar.linear_inplace(b, N, frm)
    b.cz(M, inverse_mask); b.free(inverse_mask)
    for off in (0, 12):
        half = x[off:off + 12]
        ar.linear_inplace(b, half, to)
        for j in (0, 6):
            pm = part_masks.pop(0)
            ar.phase_product(b, half[j:j + 6], M, pm); b.free(pm)
        ar.linear_inplace(b, half, frm)
    assert not part_masks
    for off, m in zip((0, 12), masks):
'''
 assert source.count(before)==1;source=source.replace(before,after)
 env=dict(folds.divide_fused.__globals__,inverse_stream_noscratch=inverse_stream_noscratch)
 exec(compile(source,__file__,'exec'),env)
 ug=dict(folds.ug)
 for key in ('absorb','absorb_even'):
  fn=ug[key];ug[key]=clone(fn,dict(fn.__globals__,divide_fused=env['divide_fused']))
 proxy=SimpleNamespace(**dict(vars(folds),ug=ug))
 return clone(ref.synthesize,dict(ref.synthesize.__globals__,folds=proxy)),env['divide_fused']
