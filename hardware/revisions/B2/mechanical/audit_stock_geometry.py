#!/usr/bin/env python3
"""Read vendor native CAD without editing it. Run with KiCad bundled Python."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E
import wx,pcbnew as k
app=wx.App(False)
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
ref=PROJECT/'hardware/cost-down/reference'
source=next((ref/'xiao-rp2040-plus-cad').glob('*/*.kicad_pcb'))
b=k.LoadBoard(str(source));native_origin=(97.87274,63.946);place=(41.1,-.25)

def native_to_device(a):return [round(place[i]+a[i]-native_origin[i],5) for i in range(2)]
def mm(v):return k.ToMM(v)
def box_device(bb):
 a=native_to_device((mm(bb.GetX()),mm(bb.GetY())));z=native_to_device((mm(bb.GetRight()),mm(bb.GetBottom())))
 return a+z

def intersect(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-5 and min(a[3],b[3])-max(a[1],b[1])>1e-5
contacts=[{'name':'left-top','box':[41.1,.5,42.2,1.7]},{'name':'left-bottom','box':[41.1,15.7,42.2,16.9]},{'name':'right-top','box':[61,.5,62.1,1.7]},{'name':'right-bottom','box':[61,15.7,62.1,16.9]}]
objects=[];pads=[];excluded_offboard=[]
for f in b.GetFootprints():
 reference=f.GetReference()
 fx,fy=mm(f.GetPosition().x),mm(f.GetPosition().y)
 if not (97.7<=fx<=119.0 and 63.8<=fy<=81.9):
  excluded_offboard.append({'ref':reference,'value':f.GetValue(),'native_xy':[fx,fy],'note':'Unplaced source object outside physical stock-board outline;excluded from occupied model.'})
  continue
 for p in f.Pads():
  pos=native_to_device((mm(p.GetPosition().x),mm(p.GetPosition().y)))
  if reference=='U4' or reference in ['TP4','TP12']:
   pads.append({'ref':reference,'pad':p.GetNumber(),'net':p.GetNetname(),'centre_device_xy':pos,'size_xy':[mm(p.GetSize().x),mm(p.GetSize().y)]})
  # Copper pad rectangles are conservative even if actual pad is circular.
  objects.append({'ref':reference,'kind':'pad','pad':p.GetNumber(),'box':box_device(p.GetBoundingBox())})
 if reference!='U4' and not reference.startswith('TP') and reference not in ['G***']:
  objects.append({'ref':reference,'kind':'component-bound','box':box_device(f.GetBoundingBox(False,False))})
conflicts=[]
for contact in contacts:
 for obj in objects:
  if intersect(contact['box'],obj['box']):conflicts.append({'contact':contact,'object':obj})
# Manufacturer Eagle geometry and source pin/resistor map.
r=E.parse(ref/'adafruit4090.brd').getroot();sch=E.parse(ref/'adafruit4090.sch').getroot()
wire_outline=[w.attrib for w in r.findall('.//board/plain/wire') if w.get('layer')=='20']
signals={}
for sig in r.findall('.//board/signals/signal'):
 signals[sig.get('name')]=[e.attrib for e in sig.findall('contactref')]
resistors=[x.attrib for x in sch.findall('.//parts/part') if x.get('name','').startswith('R')]
caps=[]
for f in b.GetFootprints():
 if f.GetReference().startswith('C'):
  caps.append({'ref':f.GetReference(),'value':f.GetValue(),'nets':[p.GetNetname() for p in f.Pads()]})
report={'source_xiao':str(source.relative_to(PROJECT)),'source_xiao_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'source_adafruit_sha256':hashlib.sha256((ref/'adafruit4090.brd').read_bytes()).hexdigest(),
 'native_outline_edge_centerline_mm':{'x':[97.87274,118.82774],'y':[63.946,81.726],'size':[20.955,17.78],'corner_radius':1.905},
 'xiao_thickness_mm':mm(b.GetDesignSettings().GetBoardThickness()),'contact_rectangles_device_xy':contacts,'native_pad_centres':pads,
 'excluded_offboard_source_objects':excluded_offboard,'contact_overlap_conflicts':conflicts,'all_contact_rectangles_clear_of_copper_and_component_bounds':not conflicts,
 'adafruit_outline_wires':wire_outline,'adafruit_signals':{n:signals[n] for n in ['GND','VBUS','D+','D-','CC1','CC2'] if n in signals},
 'adafruit_resistors':resistors,'xiao_capacitors':caps,'f_component_boxes':[o for o in objects if o['kind']=='component-bound' and o['ref']!='USB1'],
 'scope':'XY pad/body bounding-box check only;no source3D-model heights,actual parts or solder envelopes measured.'}
(HERE/'stock-source-geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'contact_conflicts':conflicts,'all_contacts_clear':not conflicts,'report':str(HERE/'stock-source-geometry-audit.json')},indent=2))
if conflicts:raise SystemExit(1)
