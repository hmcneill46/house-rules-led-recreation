"""Local filled/capped escapes for the remaining control endpoints."""
import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'trimmed-final6.kicad_pcb';dest=P/'captured-last6.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu];plans=[('U3','14',108.45,57.9),('U3','19',108.15,60.2),('U4','23',131.55,58.55),('R21','1',None,None),('U9','10',113.25,62.55)];rip=set();log=[]
def uid(o):return str(o.m_Uuid.AsString())
def pad(ref,pin):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin)
for ref,pin,x,y in plans:
 p=pad(ref,pin);point=p.GetPosition()if x is None else k.VECTOR2I(k.FromMM(x),k.FromMM(y));shape=k.SHAPE_SEGMENT(point,point,450000);stub=k.SHAPE_SEGMENT(p.GetPosition(),point,110000);blocked=[]
 for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
  if uid(o)in rip:continue
  if isinstance(o,k.PCB_VIA)and o.GetNetname()==p.GetNetname()and(point-o.GetPosition()).EuclideanNorm()<550000:rip.add(uid(o));continue
  if o.GetNetname()==p.GetNetname():continue
  if(o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999))or any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):blocked.append(o)
 if any(isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_')for o in blocked):raise RuntimeError(ref+'.'+pin+' protected capture conflict '+str([(o.GetClass(),o.GetNetname())for o in blocked]))
 rip.update(uid(o)for o in blocked);log.append({'ref':ref,'pin':pin,'xy':[point.x,point.y],'net':p.GetNetname(),'ripped':[(uid(o),o.GetNetname())for o in blocked]})
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),rip));b=k.LoadBoard(str(dest))
for item in log:
 p=pad(item['ref'],item['pin']);point=k.VECTOR2I(*item['xy'])
 if p.GetPosition()!=point:
  t=k.PCB_TRACK(b);t.SetStart(p.GetPosition());t.SetEnd(point);t.SetWidth(110000);t.SetLayer(k.B_Cu);t.SetNet(p.GetNet());t.SetLocked(True);b.Add(t)
 v=k.PCB_VIA(b);v.SetPosition(point);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(p.GetNet());v.SetLocked(True);b.Add(v)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'last-capture-actions.json').write_text(json.dumps({'plans':log,'removed_objects':sorted(rip)},indent=2));print(json.dumps(log,indent=2))
