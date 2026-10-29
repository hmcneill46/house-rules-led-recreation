"""Add ordinary outside-pad GND vias in scratch, checking native copper shapes."""
import argparse,json,math,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=P/'escaped4.kicad_pcb');ap.add_argument('--output',type=Path,default=P/'grounded4.kicad_pcb');a=ap.parse_args();b=k.LoadBoard(str(a.input));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
def vec(x,y):return k.VECTOR2I(round(x*1e6),round(y*1e6))
def ident(o):return str(o.m_Uuid.AsString())
def xy(p):return [k.ToMM(p.x),k.ToMM(p.y)]
def connected(p):return any(o.GetClass()=='ZONE'for o in b.GetConnectivity().GetConnectedItems(p))
def obst(o):return {'id':ident(o),'net':o.GetNetname(),'kind':o.GetClass()}
pads=[p for f in b.GetFootprints()for p in f.Pads()];tracks=list(b.GetTracks());log=[]
b.BuildConnectivity()
for pad in sorted([p for p in pads if p.GetNetname()=='GND'],key=lambda p:(0 if p.GetParentFootprint().GetReference()in('J2','J14')else 1,p.GetParentFootprint().GetReference())):
 ref=pad.GetParentFootprint().GetReference();pin=pad.GetNumber()
 if connected(pad):continue
 start=pad.GetPosition();nearby=[]
 for o in pads+tracks:
  bb=o.GetBoundingBox();r=2400000
  if bb.GetLeft()<=start.x+r and bb.GetRight()>=start.x-r and bb.GetTop()<=start.y+r and bb.GetBottom()>=start.y-r:nearby.append(o)
 width=500000 if ref in ('J2','J14')else 240000
 if ref in ('J2','J14'):candidates=[vec(k.ToMM(start.x),51.95)]
 else:candidates=[vec(k.ToMM(start.x)+d*math.cos(angle*math.pi/180),k.ToMM(start.y)+d*math.sin(angle*math.pi/180))for d in (.8,.85,.9,1,1.1,1.2,1.4,1.6,1.8)for angle in range(0,360,15)]
 options=[]
 for end in candidates:
  if not(50.55<=k.ToMM(end.x)<=137.85 and 50.55<=k.ToMM(end.y)<=66.75):continue
  viaShape=k.SHAPE_SEGMENT(end,end,600000)
  # No via copper, and hence no drill, overlaps the solderable pad.
  if pad.GetEffectiveShape(k.B_Cu).Collide(viaShape,49999):continue
  stub=k.SHAPE_SEGMENT(start,end,width);blocked={}
  for o in nearby:
   # Same-net drills still need hole spacing; all solderable lands stay open.
   drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
   if drill and(end-o.GetPosition()).EuclideanNorm()<(300000+drill)/2+250000:blocked[ident(o)]=o
   if isinstance(o,k.PAD)and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(viaShape,49999)for l in layers):blocked[ident(o)]=o
   if o.GetNetname()=='GND':continue
   if o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999):blocked[ident(o)]=o
   if any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(viaShape,149999)for l in layers):blocked[ident(o)]=o
   drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
   if drill and(end-o.GetPosition()).EuclideanNorm()<(300000+drill)/2+250000:blocked[ident(o)]=o
  if any(isinstance(o,k.PAD)or o.IsLocked()for o in blocked.values()):continue
  options.append((len(blocked),(end-start).EuclideanNorm(),end,list(blocked.values())))
 if not options:log.append({'ref':ref,'pin':pin,'status':'blocked'});print(ref,pin,'BLOCKED',flush=True);continue
 options.sort(key=lambda x:(x[0],x[1]));_,_,end,remove=options[0]
 for o in remove:b.Remove(o)
 removed={ident(o)for o in remove};tracks=[t for t in tracks if ident(t)not in removed]
 t=k.PCB_TRACK(b);t.SetStart(start);t.SetEnd(end);t.SetWidth(width);t.SetLayer(k.B_Cu);t.SetNet(pad.GetNet());t.SetLocked(True);b.Add(t);tracks.append(t)
 via=k.PCB_VIA(b);via.SetPosition(end);via.SetWidth(600000);via.SetDrill(300000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(pad.GetNet());via.SetLocked(True);b.Add(via);tracks.append(via)
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
 log.append({'ref':ref,'pin':pin,'status':'added','via':xy(end),'stub':[xy(start),xy(end)],'width_mm':width/1e6,'ripped':[obst(o)for o in remove]});print(ref,pin,'via',xy(end),'rip',len(remove),flush=True)
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA)and t.GetWidth()<110000:t.SetWidth(110000)
b.GetDesignSettings().m_TrackMinWidth=110000;b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.output),b)
for ext in ('kicad_pro','kicad_dru'):shutil.copy2(a.input.with_suffix('.'+ext),a.output.with_suffix('.'+ext))
project=json.loads(a.output.with_suffix('.kicad_pro').read_text());project['board']['design_settings']['rules']['min_track_width']=.11;a.output.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2))
(P/'ground-via-plans.json').write_text(json.dumps(log,indent=2))
