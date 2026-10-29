#!/usr/bin/env python3
"""Native footprint placement audit in RAM. Never writes a KiCad board."""
from pathlib import Path
import hashlib,json,math
import wx,pcbnew as k
app=wx.App(False)
HERE=Path(__file__).resolve().parent;B2=HERE.parent
spec=json.loads((B2/'electrical-spec.json').read_text())
placement=json.loads((B2/'placement.json').read_text())
contract=json.loads((B2/'stock-module-contract.json').read_text())
source=B2/'kicad/house-rules-main-B2.kicad_pcb'
b=k.LoadBoard(str(source));native={f.GetReference():f for f in b.GetFootprints()}
new_refs={'U9','C15','C16','R21','R22','R23','J19','J20'};changed=new_refs|{'R15'}
for p in spec['parts']:
 if p['ref'] not in native:
  lib,name=p['footprint'].split(':')
  f=k.FootprintLoad(str(B2/'kicad/footprints'/(lib+'.pretty')),name)
  if f is None:raise ValueError('Missing native footprint '+p['footprint'])
  b.Add(f);f.SetReference(p['ref']);f.Flip(k.VECTOR2I(0,0),k.FLIP_DIRECTION_LEFT_RIGHT)
  native[p['ref']]=f
 if p['ref'] in changed:
  f=native[p['ref']];pp=placement[p['ref']]
  f.SetOrientationDegrees(pp['angle']);f.SetPosition(k.VECTOR2I(k.FromMM(pp['x']+50),k.FromMM(pp['y']+50)))
def box(v):
 return [k.ToMM(v.GetX())-50,k.ToMM(v.GetY())-50,k.ToMM(v.GetRight())-50,k.ToMM(v.GetBottom())-50]
def gap(a,c):
 return math.hypot(max(0,a[0]-c[2],c[0]-a[2]),max(0,a[1]-c[3],c[1]-a[3]))
def touch(a,c):return min(a[2],c[2])-max(a[0],c[0])>1e-6 and min(a[3],c[3])-max(a[1],c[1])>1e-6
pads=[];courts=[]
for ref,f in native.items():
 for p in f.Pads():pads.append({'ref':ref,'pad':p.GetNumber(),'box':box(p.GetBoundingBox())})
 g=[box(x.GetBoundingBox())for x in f.GraphicalItems()if x.GetLayer()==k.B_CrtYd]
 if g:courts.append({'ref':ref,'box':[min(a[0]for a in g),min(a[1]for a in g),max(a[2]for a in g),max(a[3]for a in g)]})
pad_conflicts=[];court_conflicts=[];stop_conflicts=[]
min_pad=1000
for i,a in enumerate(pads):
 for c in pads[i+1:]:
  if a['ref']==c['ref']or not({a['ref'],c['ref']}&changed):continue
  distance=gap(a['box'],c['box']);min_pad=min(min_pad,distance)
  if distance<.15-1e-6:pad_conflicts.append({'a':a,'b':c,'bounding_box_gap_mm':distance})
for i,a in enumerate(courts):
 for c in courts[i+1:]:
  if {a['ref'],c['ref']}&changed and touch(a['box'],c['box']):court_conflicts.append({'a':a,'b':c})
for st in contract['main_rear_contact_keepouts']:
 r=[st['x'][0],st['y'][0],st['x'][1],st['y'][1]]
 for a in pads+courts:
  if a['ref']in changed and touch(r,a['box']):stop_conflicts.append({'contact':r,'object':a})
report={'result':'PASS'if not(pad_conflicts or court_conflicts or stop_conflicts)else'FAIL',
 'scope':'Native pad bounding boxes/courtyards and declared case stops for BC additions;RAM only;no route/via clearance or whole-board DRC claimed.',
 'source_board':str(source.relative_to(B2)),'source_board_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'placement_sha256':hashlib.sha256((B2/'placement.json').read_bytes()).hexdigest(),
 'positions':{ref:placement[ref]for ref in sorted(changed)},
 'minimum_changed_to_other_pad_box_gap_mm':round(min_pad,6),
 'pad_conflicts':pad_conflicts,'courtyard_conflicts':court_conflicts,'case_stop_conflicts':stop_conflicts}
(HERE/'bc-placement-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if report['result']!='PASS':raise SystemExit(1)
