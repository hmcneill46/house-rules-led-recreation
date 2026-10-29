import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'clean6-BC.kicad_pcb';dest=P/'ready6-BC.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu];plans=[];rip=set()
def ident(o):return str(o.m_Uuid.AsString())
def test(point,diam,net):
 shape=k.SHAPE_SEGMENT(point,point,diam);blocked=[];holebad=False
 for o in[p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
  if ident(o)in rip:continue
  if o.GetNetname()!=net and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):blocked.append(o)
  drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
  if drill and(point-o.GetPosition()).EuclideanNorm()<(300000+drill)/2+250000:holebad=True
 if holebad or any(isinstance(o,k.PAD)or o.IsLocked()for o in blocked):return None
 return blocked
for f in b.GetFootprints():
 if f.GetReference()not in('U3','U4'):continue
 ep=next(p for p in f.Pads()if p.GetNumber()=='25');c=ep.GetPosition();options=[]
 for x in range(-7,8):
  for y in range(-7,8):
   p=k.VECTOR2I(c.x+x*100000,c.y+y*100000);blocked=test(p,450000,'GND')
   if blocked is not None:options.append((len(blocked),x*x+y*y,p,blocked))
 if not options:raise RuntimeError('No thermal candidate '+f.GetReference())
 options.sort(key=lambda x:(x[0],x[1]));_,_,point,blocked=options[0];rip.update(ident(o)for o in blocked);plans.append({'ref':f.GetReference(),'kind':'third_EP','xy':[point.x,point.y],'diameter':450000,'net':'GND','ripped':[(ident(o),o.GetNetname())for o in blocked]})
for f in b.GetFootprints():
 if f.GetReference()not in('C15','C16','R22','U9'):continue
 for pad in f.Pads():
  if pad.GetNetname()!='GND':continue
  point=pad.GetPosition();diam=450000 if f.GetReference()=='U9'else 600000;blocked=test(point,diam,'GND')
  if blocked is None:raise RuntimeError('Protected new-ground collision '+f.GetReference())
  rip.update(ident(o)for o in blocked);plans.append({'ref':f.GetReference(),'pin':pad.GetNumber(),'kind':'new_ground','xy':[point.x,point.y],'diameter':diam,'net':'GND','ripped':[(ident(o),o.GetNetname())for o in blocked]})
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),rip));b=k.LoadBoard(str(dest))
for item in plans:
 v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(*item['xy']));v.SetWidth(item['diameter']);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('GND'));v.SetLocked(True);b.Add(v)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'final-ground6-actions.json').write_text(json.dumps(plans,indent=2));print('Added',len(plans),'GND barrels; removed',len(rip),'unlocked segments; all4QFNs now3EPbarrels')
