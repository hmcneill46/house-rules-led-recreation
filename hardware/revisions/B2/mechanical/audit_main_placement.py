#!/usr/bin/env python3
"""Read-only native-board mechanical placement audit. Use KiCad Python."""
from pathlib import Path
import hashlib,json,math
import wx,pcbnew as k
app=wx.App(False)
HERE=Path(__file__).resolve().parent
CONTRACT=HERE.parent/'stock-module-contract.json'
d=json.loads(CONTRACT.read_text())
board=HERE.parent/'kicad/house-rules-main-B2.kicad_pcb'
b=k.LoadBoard(str(board))
# Main-board native origin in the B2 builder is (50,50) mm.
origin=(50,50)
def box(bb):
 return [k.ToMM(bb.GetX())-50,k.ToMM(bb.GetY())-50,
         k.ToMM(bb.GetRight())-50,k.ToMM(bb.GetBottom())-50]
def intersects(a,c):
 return min(a[2],c[2])-max(a[0],c[0])>1e-6 and min(a[3],c[3])-max(a[1],c[1])>1e-6
def circle_rect(c,r,a):
 return math.hypot(c[0]-max(a[0],min(c[0],a[2])),c[1]-max(a[1],min(c[1],a[3])))<r
objects=[]
for f in b.GetFootprints():
 ref=f.GetReference();lib=str(f.GetFPID().GetLibItemName())
 for p in f.Pads():objects.append({'ref':ref,'kind':'pad','pad':p.GetNumber(),'box':box(p.GetBoundingBox())})
 if not ref.startswith('DS'):
  objects.append({'ref':ref,'kind':'footprint-bound','footprint':lib,'box':box(f.GetBoundingBox(False,False))})
conflicts=[]
for stop in d['main_rear_contact_keepouts']:
 rect=[stop['x'][0],stop['y'][0],stop['x'][1],stop['y'][1]]
 for o in objects:
  if intersects(rect,o['box']):conflicts.append({'contact':rect,'object':o})
cap=d['mcu']['left_cap'];circle=cap['screw_centre_xy'];radius=cap['main_keepout_radius']
head_overlaps=[o for o in objects if o['kind']=='footprint-bound' and circle_rect(circle,radius,o['box'])]
# In the frozen B2 placement only R9 overlaps this local low-height envelope.
# UniOhm 0603 WAF body height 0.45+/-0.10 mm; the contract allows 1 mm
# including solder. This check is deliberately not a generic SMD-height guess.
head_conflicts=[o for o in head_overlaps if o['ref']!='R9' or o['footprint']!='R_0603_1608Metric']
report={'board':str(board.relative_to(HERE.parent)),
 'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),
 'contract_sha256':hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
 'native_origin_mm':origin,'contact_conflicts':conflicts,
 'mcu_screw_head_local_overlaps':head_overlaps,'mcu_screw_head_height_conflicts':head_conflicts,
 'height_evidence':{'part':'R9,0603WAF4701T5E','body_height_mm':[.35,.55],
 'allowed_including_solder_mm':1.0,'head_lowest_z':12.6,'main_back_z':10.9,
 'minimum_clearance_if_contract_met_mm':.7,
 'manufacturer_datasheet':'https://datasheet.lcsc.com/lcsc/2206010230_UNI-ROYAL-Uniroyal-Elec-0603WAF2201T5E_C4190.pdf'},
 'pass':not conflicts and not head_conflicts,
 'scope':'Native pad and footprint XY bounds; a body-height contract at the cap screw; not a solder/wire/printed-fit or full 3D component audit.'}
(HERE/'main-placement-mechanical-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['pass']:raise SystemExit(1)
