import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'control6-BC.kicad_pcb';dest=P/'captured6-BC.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu];rip=set();plans=[]
for ref,pin in[('R21','2'),('R22','1'),('J19','1')]:
 f=next(f for f in b.GetFootprints()if f.GetReference()==ref);p=next(p for p in f.Pads()if p.GetNumber()==pin);point=p.GetPosition();shape=k.SHAPE_SEGMENT(point,point,450000);blocked=[]
 for o in[pp for ff in b.GetFootprints()for pp in ff.Pads()]+list(b.GetTracks()):
  if o.GetNetname()!=p.GetNetname()and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):blocked.append(o)
 if any(isinstance(o,k.PAD)or o.IsLocked()for o in blocked):raise RuntimeError('Protected capture conflict '+ref+'.'+pin+' '+str([(o.GetClass(),o.GetNetname())for o in blocked]))
 rip.update(str(o.m_Uuid.AsString())for o in blocked);plans.append({'ref':ref,'pin':pin,'xy':[point.x,point.y],'net':p.GetNetname(),'ripped':[(str(o.m_Uuid.AsString()),o.GetNetname())for o in blocked]})
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),rip));b=k.LoadBoard(str(dest))
for p in plans:
 v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(*p['xy']));v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(p['net']));v.SetLocked(True);b.Add(v)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'control-capture-actions.json').write_text(json.dumps(plans,indent=2));print(json.dumps(plans,indent=2))
