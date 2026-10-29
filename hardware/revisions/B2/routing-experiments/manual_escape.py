"""Scratch only: ordinary outside-pad vias, protected pads/locked routing."""
import json,math,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;b=k.LoadBoard(str(P/'routed4.kicad_pcb'));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def ident(o):return str(o.m_Uuid.AsString())
def obstacle(o):return {'id':ident(o),'kind':'pad'if isinstance(o,k.PAD)else'via'if isinstance(o,k.PCB_VIA)else'track','net':o.GetNetname(),'locked':o.IsLocked(),'name':o.GetParentFootprint().GetReference()+'.'+o.GetNumber()if isinstance(o,k.PAD)else''}
pads=[p for f in b.GetFootprints()for p in f.Pads()];tracks=list(b.GetTracks())
needed=[('U1','2'),('U2','3'),('U2','5'),('U3','6'),('U3','8'),('U4','7')]
plans=[]
for ref,pin in needed:
 f=next(f for f in b.GetFootprints()if f.GetReference()==ref);pad=next(p for p in f.Pads()if p.GetNumber()==pin);start=pad.GetPosition();cp=f.GetPosition()
 dx=start.x-cp.x;dy=start.y-cp.y;normal=(-1 if dx<0 else 1,0)if abs(dx)>abs(dy)else(0,-1 if dy<0 else 1)
 nearby=[]
 for o in pads+tracks:
  bb=o.GetBoundingBox();r=3000000
  if bb.GetLeft()<=start.x+r and bb.GetRight()>=start.x-r and bb.GetTop()<=start.y+r and bb.GetBottom()>=start.y-r:nearby.append(o)
 options=[]
 for dist in [0.6,0.65,0.7,0.75,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5]:
  for shift in [0,-.05,.05,-.1,.1,-.15,.15,-.2,.2,-.3,.3,-.4,.4,-.5,.5,-.6,.6]:
   ex=k.ToMM(start.x)+normal[0]*dist-normal[1]*shift;ey=k.ToMM(start.y)+normal[1]*dist+normal[0]*shift;end=vec(ex,ey)
   # An orthogonal neck first leaves the land before any lateral motion.
   mid=vec(k.ToMM(start.x)+normal[0]*min(dist,.45),k.ToMM(start.y)+normal[1]*min(dist,.45))
   poly=[start,mid,end];stub=[k.SHAPE_SEGMENT(a,z,150000)for a,z in zip(poly,poly[1:])]
   vs=k.SHAPE_SEGMENT(end,end,600000);blocked={}
   for o in nearby:
    if o.GetNetname()==pad.GetNetname():continue
    if o.IsOnLayer(k.B_Cu)and any(o.GetEffectiveShape(k.B_Cu).Collide(seg,149999)for seg in stub):blocked[ident(o)]=o
    if any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(vs,149999)for l in layers):blocked[ident(o)]=o
   for o in nearby:
    drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
    if drill and(end-o.GetPosition()).EuclideanNorm()<(300000+drill)/2+250000:blocked[ident(o)]=o
   protected=[o for o in blocked.values()if isinstance(o,k.PAD)or o.IsLocked()]
   if not protected:options.append((len(blocked),dist+abs(shift),poly,end,list(blocked.values())))
 if not options:
  plans.append({'ref':ref,'pin':pin,'net':pad.GetNetname(),'status':'no pad-safe via found'});continue
 options.sort(key=lambda x:(x[0],x[1]));cost,_,poly,end,remove=options[0]
 # Do not mutate shared pad list; only remove unlocked tracks locally.
 for o in remove:b.Remove(o)
 tracks=[t for t in tracks if ident(t)not in {ident(o)for o in remove}]
 for a,z in zip(poly,poly[1:]):
  if a==z:continue
  t=k.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetWidth(150000);t.SetLayer(k.B_Cu);t.SetNet(pad.GetNet());t.SetLocked(True);b.Add(t);tracks.append(t)
 via=k.PCB_VIA(b);via.SetPosition(end);via.SetWidth(600000);via.SetDrill(300000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(pad.GetNet());via.SetLocked(True);b.Add(via);tracks.append(via)
 plans.append({'ref':ref,'pin':pin,'net':pad.GetNetname(),'status':'added','via':[k.ToMM(end.x),k.ToMM(end.y)],'poly':[[k.ToMM(p.x),k.ToMM(p.y)]for p in poly],'ripped':[obstacle(o)for o in remove]});print(ref,pin,cost,flush=True)
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA)and t.GetWidth()<110000:t.SetWidth(110000)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());dest=P/'escaped4.kicad_pcb';k.SaveBoard(str(dest),b)
for ext in ('kicad_pro','kicad_dru'):shutil.copy2((P/'routed4.kicad_pcb').with_suffix('.'+ext),dest.with_suffix('.'+ext))
project=json.loads(dest.with_suffix('.kicad_pro').read_text());project['board']['design_settings']['rules']['min_track_width']=.11;dest.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2))
(P/'escape-plans.json').write_text(json.dumps(plans,indent=2));print(json.dumps(plans,indent=2))
