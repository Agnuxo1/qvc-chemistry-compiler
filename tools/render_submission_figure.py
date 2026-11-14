# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-14 | https://orcid.org/0009-0001-1634-7063
"""Render two real public-score observations; animation only changes emphasis."""
import hashlib,json,math
from pathlib import Path
from PIL import Image,ImageDraw
from render_figures import font,BG,PANEL,INK,MUTED,CYAN,BLUE
ROOT=Path(__file__).resolve().parents[1]
def main():
    path=ROOT/'evidence/kaggle/v0.4.0.json';r=json.loads(path.read_text())
    assert r['repository_submission_state']=='COMPLETE' and r['submission']['api_status']=='COMPLETE'
    scores=[r['previous_submission']['public_score'],r['submission']['public_score']]
    assert all(type(x) in [int,float] and math.isfinite(x) and x>=0 for x in scores)
    assert scores[0]>0
    upper=max(5,5*math.ceil(max(scores)*1.12/5));left,right=285,1040
    gain=(scores[1]/scores[0]-1)*100;frames=[]
    for focus in range(4):
        im=Image.new('RGB',(1100,540),BG);d=ImageDraw.Draw(im)
        d.rectangle((0,0,8,540),fill=CYAN)
        d.text((30,20),'Official Kaggle result · v0.4.0',font=font(33,True),fill=INK)
        d.text((30,67),'Two dated platform observations · fixed data · zero-based axis',font=font(20),fill=MUTED)
        for x in range(0,upper+1,5):
            px=left+x/upper*(right-left);d.line((px,124,px,337),fill='#35516b')
            d.text((px-8,348),str(x),font=font(17),fill=MUTED)
        for i,(label,when,value,color) in enumerate(zip(['Previous submission','Selected v0.4.0'],['30 October 2026','14 November 2026'],scores,[BLUE,CYAN])):
            y=145+i*110;d.text((30,y),label,font=font(22,True),fill=INK)
            d.text((30,y+37),when,font=font(18),fill=MUTED)
            width=value/upper*(right-left)
            d.rounded_rectangle((left,y,left+max(width,1),y+58),radius=7,fill=color,outline=INK if focus==i else color,width=3)
            d.text((left+12,y+12),f'{value:.5f}',font=font(25,True),fill=BG)
        d.text((455,386),'Public leaderboard score',font=font(18),fill=MUTED)
        d.text((30,392),f'{gain:+.2f}%',font=font(33,True),fill=CYAN if focus>=2 else INK)
        d.text((30,435),f"Submission {r['submission']['ref']} · COMPLETE · exact source portfolio",font=font(21,True),fill=CYAN if focus==3 else INK)
        d.line((30,477,1070,477),fill='#35516b')
        d.text((30,487),'Prior: credited public baseline. v0.4.0: credited generators + project chemistry. No prize certification.',font=font(15),fill=MUTED)
        d.text((30,514),'Francisco Angulo de Lafuente · ORCID 0009-0001-1634-7063 · 2026-11-14',font=font(15),fill=MUTED)
        frames.append(im)
    assets=ROOT/'assets';gif=assets/'official-submission.gif'
    frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1600,loop=0,optimize=True,comment=b'QVC Chemistry Compiler | Francisco Angulo de Lafuente | 2026-11-14 | MIT OR Apache-2.0; preserve upstream notices')
    sheet=Image.new('RGB',(1100,540),BG)
    for i,frame in enumerate(frames):sheet.paste(frame.resize((550,270)),((i%2)*550,(i//2)*270))
    sheet.save(assets/'official-submission-contact.png')
    record={'scope':'Two actual dated public leaderboard scores, not simulation, confidence interval or hardware benchmark','receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'submission_refs':[r['previous_submission']['ref'],r['submission']['ref']],'scores':scores,'gain_percent':gain,'axis_min':0,'axis_max':upper,'frames':4,'gif_sha256':hashlib.sha256(gif.read_bytes()).hexdigest()}
    (assets/'official-submission-data.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
