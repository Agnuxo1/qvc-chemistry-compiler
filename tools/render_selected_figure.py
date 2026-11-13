# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-14 | https://orcid.org/0009-0001-1634-7063
"""Render fixed measured selected resources; animation only changes emphasis."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from check_selected_candidate import verify
from render_figures import font,BG,PANEL,INK,MUTED,CYAN,BLUE,GOLD
ROOT=Path(__file__).resolve().parents[1]
def main():
    verify(ROOT)
    s=json.loads((ROOT/'SELECTED_CANDIDATE.json').read_text())
    receipts={k:json.loads((ROOT/p).read_text())['official_result'] for k,p in s['full_receipt_files'].items()}
    data={'scope':'Fixed measured v0.4.0 results; emphasis animation, not a simulation or official score','version':s['version'],'selection_sha256':hashlib.sha256((ROOT/'SELECTED_CANDIDATE.json').read_bytes()).hexdigest(),'receipt_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in s['full_receipt_files'].values()},'local_range':s['observed_composite_range'],'qubits':{k:receipts[k]['num_qubits'] for k in ['invsqrt_default','dqi_default','chem_a']},'shots':{kind:sum(r['verified_shots'] for k,r in receipts.items() if k.startswith(kind)) for kind in ['invsqrt','dqi','chem']},'dqi_value_errors':sum(r['value_errors'] for k,r in receipts.items() if k.startswith('dqi')),'dqi_phase_errors':sum(r['phase_errors'] for k,r in receipts.items() if k.startswith('dqi'))}
    frames=[]
    for focus in range(4):
        im=Image.new('RGB',(1100,540),BG);d=ImageDraw.Draw(im)
        d.rectangle((0,0,8,540),fill=CYAN)
        d.text((30,20),'Selected source portfolio · v0.4.0',font=font(34,True),fill=INK)
        d.text((30,67),'18 exact outputs · full local checks · fixed measured data',font=font(21),fill=MUTED)
        boxes=[('Inverse square root','46 qubits',f"{data['shots']['invsqrt']:,} shots",'2 salts + exact HMR proof'),('DQI decoder','889 qubits',f"{data['shots']['dqi']:,} shots",'4 salts; 1 value error, 0 phase'),('Project chemistry','427 total qubits',f"{data['shots']['chem']:,} shots",'2 salts; frozen deep512 recipe')]
        for i,(title,q,shots,detail) in enumerate(boxes):
            x=30+i*360;color=[CYAN,BLUE,GOLD][i]
            d.rounded_rectangle((x,117,x+330,310),radius=12,fill=PANEL,outline=color if focus==i else '#35516b',width=4 if focus==i else 1)
            d.text((x+15,132),title,font=font(23,True),fill=INK)
            d.text((x+15,177),q,font=font(27,True),fill=color)
            d.text((x+15,224),shots,font=font(21),fill=INK)
            d.text((x+15,268),detail,font=font(17),fill=MUTED)
        color=CYAN if focus==3 else INK
        d.text((30,335),f"Local index: {data['local_range'][0]:.5f}–{data['local_range'][1]:.5f}",font=font(31,True),fill=color)
        d.text((30,382),'All 16 cost combinations; the DQI error penalty is retained.',font=font(20),fill=MUTED)
        d.text((30,416),'I01 closed: selected source chain  |  I01-HIST open: earlier exact hashes',font=font(19),fill=CYAN)
        d.line((30,457,1070,457),fill='#35516b')
        d.text((30,469),'Classical local simulation · archived baselines · no official score or confidence interval',font=font(16),fill=MUTED)
        d.text((30,501),'Francisco Angulo de Lafuente · ORCID 0009-0001-1634-7063 · 2026-11-14',font=font(16),fill=MUTED)
        frames.append(im)
    assets=ROOT/'assets';path=assets/'selected-portfolio.gif'
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=1600,loop=0,optimize=True,comment=b'QVC Chemistry Compiler | Francisco Angulo de Lafuente | 2026-11-14 | MIT OR Apache-2.0; preserve upstream notices')
    sheet=Image.new('RGB',(1100,540),BG)
    for i,im in enumerate(frames):sheet.paste(im.resize((550,270)),((i%2)*550,(i//2)*270))
    sheet.save(assets/'selected-contact-sheet.png')
    data['gif_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();data['frames']=4
    (assets/'selected-figure-data.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'RENDERED_FIXED_MEASUREMENTS','sha256':data['gif_sha256'],'frames':4}))
if __name__=='__main__':main()
