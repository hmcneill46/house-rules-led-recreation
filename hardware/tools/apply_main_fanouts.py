#!/usr/bin/env python3
"""Lock reviewed USB routing and local QFN escapes; rip conflicting auto copper.

No component/pad, locked copper or outline is removed. Full native DRC required.
Run once on the pre-finish main board, not as a general regeneration operation.
"""
from pathlib import Path
import json,sys,shutil
import wx,pcbnew as k
sys.path.insert(0,str(Path(__file__).parent))
from clear_route_conflicts import blocks
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware/kicad/house-rules-main.kicad_pcb'
app=wx.App(False);mm=k.FromMM
V=lambda a:k.VECTOR2I(mm(a[0]),mm(a[1]))
# Global coordinates; reviewed collision-free against pads and fixed copper.
plans=json.loads((ROOT/'hardware/reports/sw1-escape-plans.json').read_text())

# Work on a temporary copy until every protected-copper check passes.
s=P.read_text()
for a,z,block in reversed(list(blocks(s))):
 if block.startswith(('(segment','(via'))and any(f'(net "{n}")'in block for n in ['USB_DM','USB_DP']):s=s[:a]+s[z:]
tmp=P.with_name('_main-fanout-planning.kicad_pcb');tmp.write_text(s)
# The native SaveBoard call also writes the associated project's design rules.
# A temporary basename must receive the real project before it is loaded.
for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(P.with_suffix(suffix),tmp.with_suffix(suffix))
b=k.LoadBoard(str(tmp));new=[]
def track(net,points,layer=k.B_Cu,width=.1):
 for a,c in zip(points,points[1:]):
  t=k.PCB_TRACK(b);t.SetStart(V(a));t.SetEnd(V(c));t.SetLayer(layer);t.SetWidth(mm(width));t.SetNet(b.FindNet(net));t.SetLocked(True);new.append(t)
def via(net,p):
 v=k.PCB_VIA(b);v.SetPosition(V(p));v.SetWidth(mm(.4));v.SetDrill(mm(.2));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net));v.SetLocked(True);new.append(v)
track('USB_DM',[(94.95,56.2125),(94.95,55.65),(94.55,55.25)],width=.15)
track('USB_DP',[(95.45,56.2125),(95.45,55.25),(95.2,55.0)],width=.15)
for n,p in [('USB_DM',(94.55,55.25)),('USB_DP',(95.2,55)),('USB_DM',(121.8,60.7)),('USB_DP',(121.15,61.7))]:via(n,p)
track('USB_DM',[(94.55,55.25),(94.55,50.8),(118.75,50.8),(121.8,53.85),(121.8,60.7)],k.F_Cu,.15)
track('USB_DP',[(95.2,55),(95.2,51.15),(118.6,51.15),(121.15,53.7),(121.15,61.7)],k.F_Cu,.15)
track('USB_DM',[(121.8,60.7),(120.325,60.7)],width=.15)
track('USB_DP',[(121.15,61.7),(120.325,61.7)],width=.15)
for j,x in enumerate([56.1,81.5,106.9,132.3],1):
 p=(x-3,58.15);track(f'D{j}_SW1',[(x-1.95,58.05),p]);via(f'D{j}_SW1',p)
for net,points in [('LED_SDB',[(91.7625,57.4),(92.1,57.4)]),('SDA',[(96.6375,59.9),(96.3,59.9)]),('LED_SDB',[(107.1,56.7),(107.1,55.8)]),('LED_SDB',[(132.5,56.7),(132.5,55.8)])]:
 track(net,points);via(net,points[-1])
layers=[k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu];rip=set();protected=[]
old=list(b.GetTracks());pads=[p for f in b.GetFootprints()for p in f.Pads()]
for ni,item in enumerate(new):
 for l in layers:
  if not item.IsOnLayer(l):continue
  shape=item.GetEffectiveShape(l)
  for other in pads+old+new[:ni]:
   if not other.IsOnLayer(l)or other.GetNetCode()==item.GetNetCode():continue
   if not shape.Collide(other.GetEffectiveShape(l),mm(.152)):continue
   if other in new or isinstance(other,k.PAD)or other.IsLocked():protected.append((item.GetNetname(),other.GetNetname(),str(other.m_Uuid.AsString()),k.LayerName(l)))
   else:rip.add(str(other.m_Uuid.AsString()))
if protected:
 print('PROTECTED COLLISIONS',json.dumps(protected));tmp.unlink();raise SystemExit(1)
for a,z,block in reversed(list(blocks(s))):
 if block.startswith(('(segment','(via'))and any(u in block for u in rip):s=s[:a]+s[z:]
tmp.write_text(s);# Objects already reference the old board; remove old copper in text, then re-add copies to a fresh native board.
b2=k.LoadBoard(str(tmp))
for item in new:
 if isinstance(item,k.PCB_VIA):
  out=k.PCB_VIA(b2);out.SetPosition(item.GetPosition());out.SetWidth(item.GetWidth(k.F_Cu));out.SetDrill(item.GetDrill());out.SetViaType(k.VIATYPE_THROUGH);out.SetLayerPair(k.F_Cu,k.B_Cu)
 else:
  out=k.PCB_TRACK(b2);out.SetStart(item.GetStart());out.SetEnd(item.GetEnd());out.SetWidth(item.GetWidth());out.SetLayer(item.GetLayer())
 out.SetNet(b2.FindNet(item.GetNetname()));out.SetLocked(True);b2.Add(out)
b2.BuildConnectivity();k.ZONE_FILLER(b2).Fill(b2.Zones());k.SaveBoard(str(P),b2);tmp.unlink()
(ROOT/'hardware/reports/main-manual-fanout-ripup.json').write_text(json.dumps({'removed_unlocked_copper':sorted(rip),'added_tracks_vias':len(new),'protected_conflicts':protected},indent=2)+'\n')
print('Locked',len(new),'reviewed tracks/vias; ripped',len(rip),'auto objects. Run native DRC.')
