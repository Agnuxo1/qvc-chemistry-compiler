# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# https://orcid.org/0009-0001-1634-7063 | QVC Chemistry Compiler | 2026-11-13
"""Render fixed receipt-backed costs; animation only highlights observations."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
records=json.loads((ROOT/'figure-data.json').read_text())['records']
def face(size,bold=False):
    candidates=[Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf'),Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for candidate in candidates:
        if candidate.is_file():return ImageFont.truetype(str(candidate),size)
    return ImageFont.truetype('DejaVuSans.ttf',size)
font=face(19);small=face(16);big=face(28,True)
frames=[]
for focus in range(1,5):
    im=Image.new('RGB',(1120,570),'#0b1726');d=ImageDraw.Draw(im)
    d.text((30,20),'Source-backed DQI: measured benchmark costs',font=big,fill='#e8eff8')
    d.text((30,62),'Four new full native PASS checks | 102,400 shots per salt | costs include error penalties',font=small,fill='#bdcad9')
    for i,r in enumerate(records):
        result=r['result'];y=120+63*i;end=340+int(result['score']/1e9/430*600)
        color='#78a8ef' if i==0 else '#42d7c2' if i==focus else '#38516d'
        d.text((30,y),r['name'],font=font,fill='#eff5ff')
        d.text((30,y+24),f"Q={result['num_qubits']} | value errors={result['value_errors']} | phase errors={result['phase_errors']}",font=small,fill='#aebfd2')
        d.rectangle((340,y+3,end,y+30),fill=color)
        d.text((end+10,y+7),f"{result['score']/1e9:.3f}",font=font,fill='#eff5ff')
    d.text((340,94),'Local native cost / 10^9 (lower is better)',font=small,fill='#bdcad9')
    d.text((30,453),'Complete 46Q / 889Q / deep512 local composite: 26.97516 - 27.01640',font=font,fill='#42d7c2')
    d.text((30,485),'All 16 fixed component-cost combinations; not independent full trials, confidence bounds or official scores.',font=small,fill='#bdcad9')
    d.text((30,514),'Quantum generator source: Syed Asad Ali (Apache-2.0). Integration: Francisco Angulo de Lafuente.',font=small,fill='#bdcad9')
    d.text((30,541),'ORCID 0009-0001-1634-7063 | 2026-11-13 | fixed observations, animated emphasis',font=small,fill='#bdcad9')
    frames.append(im)
frames[0].save(ROOT/'resources.gif',save_all=True,append_images=frames[1:],duration=[1600]*4,loop=0,optimize=False)
sheet=Image.new('RGB',(1120,2280))
for i,frame in enumerate(frames):sheet.paste(frame,(0,570*i))
sheet.save(ROOT/'resources-contact.png')
print('rendered4fixed-observationframes')
