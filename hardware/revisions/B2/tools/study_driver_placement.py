#!/usr/bin/env python3
"""Read-only native-footprint study against the unchanged 84 LED pads."""
import json, math
from pathlib import Path
import wx, pcbnew as k
ROOT=Path(__file__).resolve().parents[4]
DEST=ROOT/'hardware/revisions/B2/reports'
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
app=wx.App(False)
def mm(x):return k.FromMM(x)
def pt(x,y):return k.VECTOR2I(mm(x+50),mm(y+50))
def bbox(p):
 b=p.GetBoundingBox()
 return [k.ToMM(b.GetX())-50,k.ToMM(b.GetY())-50,k.ToMM(b.GetRight())-50,k.ToMM(b.GetBottom())-50]
b=k.LoadBoard(str(ROOT/'hardware/kicad/house-rules-main.kicad_pcb'))
leds=[]
for f in b.GetFootprints():
 if f.GetReference().startswith('DS'):
  for p in f.Pads():
   leds.append({'ref':f.GetReference()+'.'+p.GetNumber(),'x':k.ToMM(p.GetPosition().x)-50,'y':k.ToMM(p.GetPosition().y)-50,'r':k.ToMM(p.GetSize().x)/2,'rect':p.GetShape()==k.PAD_SHAPE_RECT,'bbox':bbox(p)})
def clearance(rect,led):
 x0,y0,x1,y1=rect
 if led['rect']:
  a,b,c,d=led['bbox']
  return math.hypot(max(a-x1,x0-c,0),max(b-y1,y0-d,0)) if not(x0<c and x1>a and y0<d and y1>b) else -min(x1-a,c-x0,y1-b,d-y0)
 return math.hypot(max(x0-led['x'],led['x']-x1,0),max(y0-led['y'],led['y']-y1,0))-led['r']
results=[]
for fpname in ['Package_SO:SSOP-24_3.9x8.7mm_P0.635mm','Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm']:
 lib,name=fpname.split(':');f=k.FootprintLoad(str(LIB/(lib+'.pretty')),name)
 trials=[]
 for angle in (0,90):
  f.SetOrientationDegrees(angle)
  for ix in range(-16,17):
   x=6.1+ix*.05
   for iy in range(0,161):
    y=4.65+iy*.05
    f.SetPosition(pt(x,y))
    pads=[p for p in f.Pads() if p.GetNumber()]
    boxes=[(p.GetNumber(),bbox(p))for p in pads]
    if any(a<.25 or bb<.25 or c>88.15 or d>17.05 for _,(a,bb,c,d)in boxes):continue
    best=10;pair=None
    for pin,rect in boxes:
     for led in leds:
      gap=clearance(rect,led)
      if gap<best:best=gap;pair=[pin,led['ref']]
    trials.append((best,x,y,angle,pair))
 trials.sort(reverse=True)
 top=trials[:8]
 results.append({'footprint':fpname,'test':'Conservative rectangle/circle copper envelopes on native footprints, all driver/LED nets assumed different','required_clearance_mm':.15,'best_pose':{'min_gap_mm':top[0][0],'x':top[0][1],'y':top[0][2],'angle':top[0][3],'closest_pair':top[0][4]},'passing_poses':sum(t[0]>=.15 for t in trials),'tested_poses':len(trials),'note':'Placement candidate only; complete native DRC, physical solder/body review and routing still required.'})
DEST.mkdir(parents=True,exist_ok=True)
(DEST/'driver-placement-study.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
