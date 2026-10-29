"""Choose clock-bus layers by native collision cost; preserve USB and placement."""
import ast,itertools,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'final-routed6.kicad_pcb';dest=P/'clock-opt6.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In3_Cu];alllayers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]
def uid(o):return str(o.m_Uuid.AsString())
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def pad(ref,pin):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin)
objects=[p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks());ids={uid(o):o for o in objects};owned={uid(t)for t in b.GetTracks()if t.GetNetname()in('SCLK','CT_5V')};captures=[];paths=[]
for ref,pin in[('U1','24'),('U2','24'),('U3','24'),('U4','24'),('J5','1')]:
 p=pad(ref,pin);pt=p.GetPosition();x,y=pt.x/1e6,pt.y/1e6;captures.append((ref,pin,pt,'SCLK'));paths.append([(x,y),(x-.45,y+.45),(x-.45,66.8)]if ref.startswith('U')else[(x,y),(96.5,53.15),(96.5,66.8)])
paths.append([(54.4,66.8),(130.6,66.8)]);captures+=[('C10','1',vec(111.9,58.5),'CT_5V'),('U6','4',pad('U6','4').GetPosition(),'CT_5V')]
def allowed(found):return not any(isinstance(ids[i],k.PAD)or ids[i].IsLocked()or ids[i].GetNetname().startswith('USB_')for i in found)
def hits(shape,layer,net):return {uid(o)for o in objects if uid(o)not in owned and o.GetNetname()!=net and o.IsOnLayer(layer)and o.GetEffectiveShape(layer).Collide(shape,149999)}
base=set()
for ref,pin,pt,net in captures:
 circle=k.SHAPE_SEGMENT(pt,pt,450000);stub=k.SHAPE_SEGMENT(pad(ref,pin).GetPosition(),pt,110000)
 for l in alllayers:base|=hits(circle,l,net)
 base|=hits(stub,k.B_Cu,net)
assert allowed(base),'Protected endpoint capture collision'
options={}
for i,path in enumerate(paths):
 for l in layers:
  found=set()
  for a,z in zip(path,path[1:]):found|=hits(k.SHAPE_SEGMENT(vec(*a),vec(*z),150000),l,'SCLK')
  options[i,l]=found if allowed(found)else None
floor={}
for i,path in enumerate(paths[:-1]):
 pt=vec(*path[-1]);found=set()
 for l in alllayers:found|=hits(k.SHAPE_SEGMENT(pt,pt,450000),l,'SCLK')
 floor[i]=found if allowed(found)else None
best=None
for choice in itertools.product(layers,repeat=6):
 if any(options[i,l]is None for i,l in enumerate(choice)):continue
 found=set(base);extra=[];valid=True
 for i,l in enumerate(choice):found|=options[i,l]
 for i,l in enumerate(choice[:-1]):
  if l!=choice[-1]:
   if floor[i]is None:valid=False;break
   found|=floor[i];extra.append(i)
 if not valid:continue
 nets={ids[i].GetNetname()for i in found};score=(len(nets),len(found),len(extra))
 if best is None or score<best[0]:best=(score,choice,found,extra)
assert best;score,choice,found,extra=best;remove=owned|found
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),remove));b=k.LoadBoard(str(dest))
def via(pt,net):
 v=k.PCB_VIA(b);v.SetPosition(pt);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)
for ref,pin,pt,net in captures:
 p=pad(ref,pin)
 if p.GetPosition()!=pt:
  t=k.PCB_TRACK(b);t.SetStart(p.GetPosition());t.SetEnd(pt);t.SetWidth(110000);t.SetLayer(k.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 via(pt,net)
for i,path in enumerate(paths):
 for a,z in zip(path,path[1:]):
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(150000);t.SetLayer(choice[i]);t.SetNet(b.FindNet('SCLK'));t.SetLocked(True);b.Add(t)
for i in extra:via(vec(*paths[i][-1]),'SCLK')
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
report={'score':score,'clock_path_layers':[b.GetLayerName(l)for l in choice],'extra_layer_transfer_vias':len(extra),'ripped_foreign_nets':sorted({ids[i].GetNetname()for i in found}),'ripped_foreign_objects':len(found),'source_clock_CT_objects_removed':len(owned),'paths':paths}
(P/'clock-optimized-actions.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
