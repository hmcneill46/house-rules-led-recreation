#!/usr/bin/env python3
"""Draw the numbered LED/connector assembly guide from the current circuit spec."""
from pathlib import Path
from html import escape
import json
ROOT=Path(__file__).resolve().parents[2]
spec=json.loads((ROOT/'hardware/kicad/circuit-spec.json').read_text())
main=next(p for p in spec['parts'] if p['board']=='main' and p['ref']=='J1')
carrier=next(p for p in spec['parts'] if p['board']=='usb' and p['ref']=='J2')
assert main['angle']==270 and carrier['angle']==270
parts=sorted((p for p in spec['parts'] if p['board']=='main' and p['ref'].startswith('DS')),key=lambda p:int(p['ref'][2:]))
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">','<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#3b759e"/></marker></defs>','<rect width="1600" height="1200" fill="#f8f7f2"/>','<g font-family="Arial, sans-serif" fill="#252525">']
def text(x,y,t,size=18,weight='normal',anchor='start',color='#252525'):
 s.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{escape(t)}</text>')
def rect(x,y,w,h,fill,stroke='#4a4a4a',opacity=1):
 s.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="1.2" opacity="{opacity}"/>')
def line(x1,y1,x2,y2,color='#777',width=1.4,arrow=False):
 s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
def circle(x,y,r,fill,stroke='#222'):
 s.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
text(50,44,'House Rules / LED and harness assembly',30,'bold')
text(50,76,'Numbered assembly guide. Dimensions in mm; this illustration is not a 1:1 fit template.',18)
text(250,118,'MAIN PCB FRONT / LED bodies removed to show the lead map',20,'bold')
X=lambda x:250+12*x
Y=lambda y:150+12*y
rect(X(0),Y(0),88.4*12,17.3*12,'#dce8dd',stroke='#397650')
for p in parts:rect(X(p['x']-6.35),Y(p['y']-8.9),12.7*12,17.8*12,'none',stroke='#999')
# Removable spacer bars: actual assembly XY placement, before removal.
for low in [3.07,13.23]:
 rect(X(-8),Y(low),100*12,12,'#c3deef',stroke='#3b759e',opacity=.8)
 rect(X(-15),Y(low),7*12,3*12,'#c3deef',stroke='#3b759e')
 line(X(-8)-10,Y(low+1.5),X(-17),Y(low+1.5),'#3b759e',2,True)
for p in parts:
 text(X(p['x']),134,p['ref'],17,'bold','middle')
 for side in [-1,1]:
  for r in range(6):
   n=r+1 if side<0 else 12-r
   x=p['x']+side*3.81;y=p['y']-6.35+2.54*r
   if n==1:rect(X(x)-8.4,Y(y)-8.4,16.8,16.8,'#d4942b',stroke='#794b10')
   else:circle(X(x),Y(y),8.4,'#e5b34c',stroke='#8c682b')
   circle(X(x),Y(y),5.4,'#f8f7f2')
   text(X(x)+side*16,Y(y)+5,str(n),14,'bold','middle', '#8d3a22' if n==1 else '#333')
text(50,150,'Pull handles left',16,'bold',color='#3b759e')
text(50,173,'after tacking and cooling',15,color='#3b759e')
text(250,397,'Pin 1: DS1 (2.29,2.30) · DS2 (14.99,2.30) · DS3 (27.69,2.30) · DS4 (40.39,2.30)',17)
text(250,423,'DS5 (53.09,2.30) · DS6 (65.79,2.30) · DS7 (78.49,2.30). Rear view mirrors left/right.',17)
text(50,475,'SIX-WIRE HARNESS / pin number to the same pin number',22,'bold')
text(50,503,'This is a net map, not a connector-face view. Cable colours are unverified and do not define signals.',18)
rect(80,530,320,215,'#e8ebe8')
rect(1200,530,320,215,'#e3edf1')
text(100,558,'MAIN J1',20,'bold');text(1220,558,'CARRIER J2',20,'bold')
names=['VBUS / 5 V','USB D−','USB D+','GND','CC1','CC2']
for i,name in enumerate(names,1):
 y=575+(i-1)*30
 circle(400,y,5,'#555');circle(1200,y,5,'#555')
 line(406,y,1194,y,'#777',2)
 rect(680,y-17,240,24,'#f8f7f2',stroke='none')
 text(800,y+1,f'{i} → {i}    {name}',18,'bold','middle')
 text(382,y+6,str(i),18,'bold','end');text(1218,y+6,str(i),18,'bold')
text(80,778,'BM06B-SRSS-TB / vertical',18,'bold')
text(80,804,f'Centre ({main["x"]:.2f},{main["y"]:.2f}), source270 / B.Cu',17)
text(80,830,'Pin 1 pad (70.325,9.70); pins 2–6 continue at 1.00 mm y steps.',17)
text(1040,778,'SM06B-SRSS-TB / side entry',18,'bold')
text(1040,804,'Local centre (3.10,5.00), source270 / F.Cu',17)
text(1040,830,'Pin 1 pad (5.10,2.50); pins 2–6 continue at 1.00 mm y steps.',17)
text(50,875,'Specify: two plain SHR-06V-S housings, 6 wires, factory crimped, 30–50 mm, continuity 1→1…6→6.',18,'bold')
text(50,902,'Keep positions 2/3 adjacent for USB data. Verify every conductor before connecting power; do not substitute a reverse-wired cable.',17)
text(50,950,'SET THE 3.0 GAP / print TWO removable spacer rails',21,'bold')
rect(100,978,430,100,'#c8c5b4');rect(100,1128,430,26,'#397650')
rect(130,1078,370,50,'#c3deef',stroke='#3b759e')
text(315,1038,'LED body',18,'bold','middle');text(315,1110,'3.0 spacer dimension',18,'bold','middle', '#275a7e')
text(550,1149,'PCB front',17)
text(700,987,'1. Front tray aligns the faces; rails set the air gap.',18)
text(700,1020,'2. Rail centres: y 3.57 and 13.73; bar 100 ×1 ×3.',18)
text(700,1053,'3. Tack two opposite pins on each module; let joints cool.',18)
text(700,1086,'4. Pull both rails left and remove; then finish the joints.',18)
text(700,1119,'5. Trim leads to the intended 1.0 rear projection.',18)
text(50,1180,'Fit status: full seven-module dry fit and physical pixel/polarity test remain pending. Printed tools are not manufacturing proof.',16,color='#666')
s.append('</g></svg>')
(ROOT/'hardware/mechanical/assembly-guide.svg').write_text('\n'.join(s)+'\n')
print('Assembly guide written: all84 numbered pads, exact pin1 locations, 1:1 numbered harness and removable3mm rails.')
