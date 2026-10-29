import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'candidate6-BC.kicad_pcb';dest=P/'clean6-BC.kicad_pcb';b=k.LoadBoard(str(source));d=json.loads((P/'candidate6-BC-drc.json').read_text());tracks={str(t.m_Uuid.AsString()):t for t in b.GetTracks()};remove=set();protected=[]
for v in d['violations']:
 if v['type']in('track_dangling','via_dangling'):continue
 for i in v['items']:
  o=tracks.get(i['uuid'])
  if o is not None:
   if o.IsLocked():protected.append({'type':v['type'],'net':o.GetNetname(),'uuid':i['uuid']})
   else:remove.add(i['uuid'])
if protected:raise RuntimeError('Protected route conflicts '+str(protected))
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),remove))
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
b=k.LoadBoard(str(dest));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu];log=[]
# Add additional thermal barrels without changing any existing route.
for f in b.GetFootprints():
 if f.GetReference()not in('U1','U2','U3','U4'):continue
 ep=next(p for p in f.Pads()if p.GetNumber()=='25');center=ep.GetPosition();inside=lambda p:abs(p.x-center.x)<800000 and abs(p.y-center.y)<800000
 existing=[t for t in b.GetTracks()if isinstance(t,k.PCB_VIA)and t.GetNetname()=='GND'and inside(t.GetPosition())]
 for x,y in[(x/10,y/10)for x in(-6,0,6)for y in(-6,0,6)]+[(x/10,y/10)for x in range(-7,8)for y in range(-7,8)]:
  if len(existing)>=3:break
  point=k.VECTOR2I(center.x+k.FromMM(x),center.y+k.FromMM(y));shape=k.SHAPE_SEGMENT(point,point,450000);okay=True
  for o in[p for ff in b.GetFootprints()for p in ff.Pads()]+list(b.GetTracks()):
   if o.GetNetname()!='GND'and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):okay=False;break
   drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
   if drill and(point-o.GetPosition()).EuclideanNorm()<(300000+drill)/2+250000:okay=False;break
  if not okay:continue
  via=k.PCB_VIA(b);via.SetPosition(point);via.SetWidth(450000);via.SetDrill(300000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(ep.GetNet());via.SetLocked(True);b.Add(via);existing.append(via)
 log.append({'ref':f.GetReference(),'EP_thermal_vias':[{'xy':[k.ToMM(v.GetPosition().x),k.ToMM(v.GetPosition().y)],'diameter':k.ToMM(v.GetWidth(k.B_Cu)),'drill':k.ToMM(v.GetDrill())}for v in existing]})
# Filled/capped6L allows direct ground barrels in the new decouplers/divider.
for f in b.GetFootprints():
 if f.GetReference()not in('C15','C16','R22','U9'):continue
 for pad in f.Pads():
  if pad.GetNetname()!='GND':continue
  point=pad.GetPosition();diameter=450000 if f.GetReference()=='U9'else 600000;shape=k.SHAPE_SEGMENT(point,point,diameter);blocked=[]
  for o in[p for ff in b.GetFootprints()for p in ff.Pads()]+list(b.GetTracks()):
   if o.GetNetname()!='GND'and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):blocked.append(o)
  if blocked:log.append({'ref':f.GetReference(),'pin':pad.GetNumber(),'ground_via':'blocked','items':[(o.GetClass(),o.GetNetname())for o in blocked]});continue
  via=k.PCB_VIA(b);via.SetPosition(point);via.SetWidth(diameter);via.SetDrill(300000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(pad.GetNet());via.SetLocked(True);b.Add(via);log.append({'ref':f.GetReference(),'pin':pad.GetNumber(),'ground_via':'added','diameter':diameter/1e6})
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
(P/'clean6-actions.json').write_text(json.dumps({'removed_conflicting_unlocked_objects':[{'uuid':x,'net':tracks[x].GetNetname()}for x in sorted(remove)],'thermal_and_new_ground':log},indent=2));print('removed',len(remove),'unlocked objects');print(json.dumps(log,indent=2))
