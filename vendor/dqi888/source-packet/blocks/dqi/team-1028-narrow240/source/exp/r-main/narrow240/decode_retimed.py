from pathlib import Path
import sys
from types import SimpleNamespace
import inspect
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path[:0]=[str(here),str(here),str(root/'playbook/kit/decoder'),str(root/'playbook/kit')]
from exp.inverse19_joint.kernel import inverse24_reverse19
from final_decoder import decode as ref
from high_stream import convert_safe
import replay_erase
import chart_retimed as chart
from synth_stream import make_synthesize
clone=chart.clone
synthesize,_divide=make_synthesize(ref)
chart_chain=clone(chart.external_node_chain,dict(chart.external_node_chain.__globals__,scalar_erase_second24=replay_erase.scalar_erase_second24))
def external_node_chain(b,words,gi,reverse=False,token=None,normalizer=None):
 if gi==8:return replay_erase.external_node_chain(b,words,gi,reverse,token,normalizer)
 return chart_chain(b,words,gi,reverse,token,normalizer)
ext_source=inspect.getsource(ref.external_extraction)
old='inverse24_reverse209(b,v,local,K)'
assert ext_source.count(old)==1
ext_source=ext_source.replace(old,'(inverse24_reverse19 if gi>=15 else inverse24_reverse209)(b,v,local,K)')
ext_env=dict(ref.external_extraction.__globals__,external_node_chain=external_node_chain,inverse24_reverse19=inverse24_reverse19)
exec(compile(ext_source,__file__,'exec'),ext_env)
ext=ext_env['external_extraction']
fwd=clone(ref.extraction,dict(ref.extraction.__globals__,external_extraction=ext))
proxy=SimpleNamespace(**dict(vars(ref),extraction=fwd))
extraction=clone(replay_erase.extraction,dict(replay_erase.extraction.__globals__,ref=proxy,external_extraction=ext))
decode=clone(ref.decode,dict(ref.decode.__globals__,convert_safe=convert_safe,extraction=extraction,synthesize=synthesize))
