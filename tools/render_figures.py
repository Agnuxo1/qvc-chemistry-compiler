# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Project: QVC Chemistry Compiler | 2026-11-10
# Author-ORCID: https://orcid.org/0009-0001-1634-7063
"""Deterministically render evidence-driven scientific GIFs, never experiment videos."""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'
EVIDENCE=ROOT/'evidence/official'
W,H=1100,500
BG='#101d2b'; PANEL='#192b3e'; INK='#edf4fa'; MUTED='#abc2d4'; CYAN='#4ad9cf'; BLUE='#7eacff'; GOLD='#f2c76d'

def font(size,bold=False):
    paths=[Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf'),Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for p in paths:
        if p.exists():return ImageFont.truetype(str(p),size)
    raise FileNotFoundError('Install Segoe UI or DejaVu Sans fonts.')

F={s:font(s) for s in (13,15,17,19,22,25,29,35,42,50)}
B={s:font(s,True) for s in (17,19,22,25,29,35,42,50)}

def canvas(title,subtitle,source):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,8,H),fill=CYAN)
    d.text((34,22),title,font=B[35],fill=INK)
    d.text((35,69),subtitle,font=F[19],fill=MUTED)
    d.line((34,436,W-30,436),fill='#33516a',width=1)
    d.text((35,448),'Francisco Angulo de Lafuente  |  ORCID 0009-0001-1634-7063',font=F[15],fill=MUTED)
    d.text((35,472),'2026-11-10  ·  '+source,font=F[13],fill=MUTED)
    return im,d

def box(d,rect,label,detail,active=False,color=CYAN):
    d.rounded_rectangle(rect,12,fill=PANEL,outline=color if active else '#35516b',width=3 if active else 1)
    x,y,xx,yy=rect
    d.text((x+17,y+15),label,font=B[22],fill=INK)
    for k,line in enumerate(detail.split('\n')):d.text((x+17,y+51+25*k),line,font=F[17],fill=MUTED)

def arrow(d,start,end,color=CYAN):
    d.line((*start,*end),fill=color,width=3)
    x,y=end;d.polygon(((x,y),(x-10,y-6),(x-10,y+6)),fill=color)

def main():
    ASSETS.mkdir(exist_ok=True)
    names=['quimica-base2494-64-a.json','quimica-gengsr-64-a.json','quimica-s2-64-a.json','quimica-s37-64-a.json']
    chemistry=[json.loads((EVIDENCE/n).read_text()) for n in names]
    ratios=[x['improvement'] for x in chemistry]
    inv=json.loads((EVIDENCE/'invsqrt-gengsr-64-linux-a.json').read_text())['official_result']
    dqi=[json.loads((EVIDENCE/f'dqi-gengsr-102400-{s}.json').read_text()) for s in ('a','b')]
    anc=json.loads((EVIDENCE/'ancillas-fran.json').read_text())
    sources=names+['ancillas-fran.json','invsqrt-gengsr-64-linux-a.json','dqi-gengsr-102400-a.json','dqi-gengsr-102400-b.json']
    payload={'scope':'Illustrations of saved local evidence; schematic panels are not simulations','source_sha256':{n:hashlib.sha256((EVIDENCE/n).read_bytes()).hexdigest() for n in sources},'chemistry_ratios':ratios,'invsqrt_verified_shots':inv['verified_shots'],'dqi_verified_shots':[x['official_result']['verified_shots'] for x in dqi],'ancilla_rows':anc['rows']}
    (ASSETS/'figure-data.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    frames={name:[] for name in ('overview','chemistry','compiler','reproducibility','verification','ancillas')}
    for frame in range(30):
        t=min(1.,frame/22);active=min(3,frame//7)
        im,d=canvas('QVC Chemistry Compiler','Source-reproducible FeMoCo angle loaders · classical virtual laboratory','Workflow schematic; metrics from quimica-s37-64-a.json')
        for i,(label,detail) in enumerate([('Frozen table','8 groups · 143 vectors\nRank 44 · 8-bit words'),('GF(2) plan','Saved product masks\nShared Boolean features'),('15 loaders','Exact source emission\n128-qubit loader limit'),('Native checks','Unmodified verifier\nHashes and error receipts')]):
            x=35+i*269;box(d,(x,133,x+245,270),label,detail,i==active)
            if i<3:arrow(d,(x+247,201),(x+265,201),CYAN if i<active else '#35516b')
        for x,value,label in [(45,'11.2328903x','Local chemistry ratio'),(405,'14,848','Total Toffolis'),(760,'427','Total qubits')]:
            d.text((x,306),value,font=B[42],fill=CYAN);d.text((x,366),label,font=F[19],fill=MUTED)
        frames['overview'].append(im)

        im,d=canvas('Measured chemistry frontier','Pinned artifacts · identical total qubit count Q = 427','Data: four full official-check receipts; y-axis zoom is explicit')
        left,right,top,bottom=85,785,135,375
        lo,hi=11.19,11.24
        for value in (11.19,11.20,11.21,11.22,11.23,11.24):
            y=bottom-(value-lo)/(hi-lo)*(bottom-top)
            d.line((left,y,right,y),fill='#2c455d');d.text((17,y-10),f'{value:.2f}',font=F[17],fill=MUTED)
        pts=[]
        for i,(name,value) in enumerate(zip(('Public base','Public gengsr','Project s2','Project s37'),ratios)):
            x=left+35+i*205;y=bottom-(value-lo)/(hi-lo)*(bottom-top)
            d.text((x-55,bottom+12),name,font=F[15],fill=MUTED)
            if t>=i/4:
                pts.append((x,y));d.ellipse((x-7,y-7,x+7,y+7),fill=CYAN if i==3 else BLUE)
                d.text((x-54,y-31),f'{value:.7f}x',font=B[17],fill=INK)
        if len(pts)>1:d.line(pts,fill=BLUE,width=3)
        d.text((832,150),'+0.2570%',font=B[29],fill=CYAN)
        d.text((832,194),'vs tested gengsr',font=F[17],fill=MUTED)
        d.text((832,252),'14,848',font=B[35],fill=INK)
        d.text((832,299),'Toffolis in s37',font=F[17],fill=MUTED)
        d.text((87,108),'Reference / cost (zoomed axis)',font=F[15],fill=MUTED)
        frames['chemistry'].append(im)

        im,d=canvas('From address bits to angle words','Illustrative GF(2) factorization · not the selected full circuit','Schematic only; exact masks and compiler source: recipes/s37/')
        for i,y in enumerate((160,218,276)):
            d.text((50,y-14),f'address x{i}',font=F[19],fill=INK)
            d.line((185,y,355,y),fill=BLUE,width=2)
            for j in range(3):
                xx=200+40*j
                if (frame//4)%3==j:d.ellipse((xx-5,y-5,xx+5,y+5),fill=CYAN)
        box(d,(359,132,606,321),'Shared products','p0 = x0 AND x1\np1 = x1 XOR x2\nReuse across outputs',True)
        arrow(d,(610,224),(674,224))
        box(d,(684,132,1057,321),'Angle-word map','y0 = p0 XOR x2\ny1 = p1 XOR x0\nOne loader per indexed output',True,BLUE)
        d.text((50,357),'Saved algebraic masks  →  source emission  →  truth-table identity checks',font=F[22],fill=CYAN)
        frames['compiler'].append(im)

        im,d=canvas('Reconstruction and evidence chain','Saved table and declarative plan → exact portable outputs','Recorded reconstruction results; animation illustrates the process')
        for i,(label,detail) in enumerate([('Pin inputs','Source + numeric hashes\nNo circuit input needed'),('Rebuild','15 KMB + one NPZ\nSource identities checked'),('Compare','16 exact output hashes\nWindows and Linux'),('Verify','Full stock native check\nPreserved JSON receipt')]):
            x=35+i*269;box(d,(x,139,x+245,284),label,detail,i==active)
            if i<3:arrow(d,(x+247,211),(x+265,211))
        d.text((50,327),'Exact reproduction starts at the frozen trained table.',font=B[25],fill=CYAN)
        d.text((50,370),'Rerunning numerical training is not guaranteed to recreate that table bit for bit.',font=F[19],fill=MUTED)
        frames['reproducibility'].append(im)

        im,d=canvas('Verification coverage','Unmodified official verifiers · local circuit checks','Data: evidence/official/*; binary PASS and source completeness are separate')
        focus=min(2,frame//10)
        box(d,(35,128,358,316),'Inverse square root',f"{inv['verified_shots']:,} shots\n3,133,452 inputs x 64\nPASS · public circuit",focus==0)
        box(d,(385,128,709,316),'DQI decoder','102,400 shots per salt\nSalt a: 1 phase error\nSalt b: 0 phase errors',focus==1,BLUE)
        box(d,(735,128,1065,316),'Chemistry s37','78,080 shots per salt\nTwo full salts PASS\n16-file exact reconstruction',focus==2)
        d.text((46,346),'Local composite indices: 25.2098283 and 25.2483618',font=B[25],fill=CYAN)
        d.text((46,387),'Archived baselines; these are neither Kaggle scores nor confidence limits.',font=F[19],fill=MUTED)
        frames['verification'].append(im)

        row=anc['rows'][-1]
        im,d=canvas('Synthetic ancilla scheduling','32-bit operands · 16-bit accumulator · a checked primitive','Data: ancillas-fran.json; no measured full-QVC improvement')
        for i,(kind,label,color) in enumerate([('parallel','Parallel schedule',BLUE),('serial','Serial reuse',CYAN)]):
            y=154+i*96;count=row[kind]['Q']
            d.text((40,y-8),label,font=B[22],fill=INK)
            d.rounded_rectangle((310,y,310+count/128*650*max(.01,t),y+40),7,fill=color)
            d.text((310+count/128*650+12,y+3),str(count),font=B[25],fill=color)
        d.text((43,352),f"{row['parallel']['C_toffoli_like']} Toffolis in both schedules",font=B[25],fill=GOLD)
        d.text((43,392),'3,344 checks per variant; exhaustive small pairs and seeded larger cases.',font=F[19],fill=MUTED)
        frames['ancillas'].append(im)
    manifest={}
    previews=[]
    for name,sequence in frames.items():
        path=ASSETS/(name+'.gif')
        sequence[0].save(path,save_all=True,append_images=sequence[1:],duration=110,loop=0,optimize=True,comment=b'QVC Chemistry Compiler | Francisco Angulo de Lafuente | ORCID 0009-0001-1634-7063 | 2026-11-10 | MIT OR Apache-2.0; see component notices')
        with Image.open(path) as encoded:
            count=encoded.n_frames
        manifest[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'encoded_frames':count,'source_frames':len(sequence),'source_frame_ms':110,'width':W,'height':H}
        previews.append(sequence[-1].resize((660,300)))
    sheet=Image.new('RGB',(1320,900),BG)
    for i,im in enumerate(previews):sheet.paste(im,((i%2)*660,(i//2)*300))
    sheet.save(ASSETS/'contact-sheet.png')
    (ASSETS/'figure-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
