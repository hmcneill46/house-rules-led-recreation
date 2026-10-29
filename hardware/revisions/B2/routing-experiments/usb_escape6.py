"""Explicit, staggered USB escapes for the filled/capped6L process."""
import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'controls-done6.kicad_pcb';dest=P/'usb-escaped6.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]
def uid(o):return str(o.m_Uuid.AsString())
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def pad(ref,pin):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin)
old=vec(119.807055,63.857741);rip={uid(t)for t in b.GetTracks()if t.GetNetname()=='GND'and((isinstance(t,k.PCB_VIA)and(t.GetPosition()-old).EuclideanNorm()<2000)or(not isinstance(t,k.PCB_VIA)and((t.GetStart()-old).EuclideanNorm()<2000 or(t.GetEnd()-old).EuclideanNorm()<2000)))}
# New geometry is checked sequentially against both pads and previously planned shapes.
plans=[('GND_ESD','U7','3',119.6,63.515,240000),('DM_WIRE','J17','1',129.76,50.85,150000),('DP_WIRE','J18','1',132.3,50.85,150000),('DM_ESD_TOP','U7','10',120.6,61.965,150000),('DP_ESD_TOP','U7','9',120.1,61.565,150000),('DM_ESD_BOTTOM','U7','1',120.6,63.515,150000),('DP_ESD_BOTTOM','U7','2',120.1,63.915,150000),('DM_BC_CON','U9','8',113.65,61.55,150000),('DP_BC_CON','U9','7',114.3,61.05,150000),('DM_BC_HOST','U9','2',112.2,61.55,150000),('DP_BC_HOST','U9','3',113.0,61.1,150000),('DM_MCU','J11','1',109.44,50.85,150000),('DP_MCU','J12','1',111.98,50.85,150000)]
log=[];new=[]
for label,ref,pin,x,y,width in plans:
 pp=pad(ref,pin);point=vec(x,y);circle=k.SHAPE_SEGMENT(point,point,450000);stub=k.SHAPE_SEGMENT(pp.GetPosition(),point,width);blocked=[]
 for o in[p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
  if uid(o)in rip or o.GetNetname()==pp.GetNetname():continue
  if(o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999))or any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(circle,149999)for l in layers):blocked.append(o)
 if any(isinstance(o,k.PAD)or o.IsLocked()for o in blocked):raise RuntimeError(label+' protected collision '+str([(o.GetClass(),o.GetNetname())for o in blocked]))
 rip.update(uid(o)for o in blocked)
 stub_id=None
 if pp.GetPosition()!=point:
  t=k.PCB_TRACK(b);t.SetStart(pp.GetPosition());t.SetEnd(point);t.SetWidth(width);t.SetLayer(k.B_Cu);t.SetNet(pp.GetNet());t.SetLocked(True);b.Add(t);new.append(uid(t));stub_id=uid(t)
 v=k.PCB_VIA(b);v.SetPosition(point);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(pp.GetNet());v.SetLocked(True);b.Add(v);new.append(uid(v));log.append({'label':label,'ref':ref,'pin':pin,'net':pp.GetNetname(),'via_xy':[x,y],'stub_length_mm':(point-pp.GetPosition()).EuclideanNorm()/1e6,'via_uuid':uid(v),'stub_uuid':stub_id,'ripped':[(uid(o),o.GetNetname())for o in blocked]})
# Direct external ground join between the actual ground land and its opposite NC land.
t=k.PCB_TRACK(b);t.SetStart(pad('U7','3').GetPosition());t.SetEnd(pad('U7','8').GetPosition());t.SetWidth(240000);t.SetLayer(k.B_Cu);t.SetNet(pad('U7','3').GetNet());t.SetLocked(True);b.Add(t)
k.SaveBoard(str(dest),b);node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](dest.read_text(),rip));b=k.LoadBoard(str(dest));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'usb-escape-plan.json').write_text(json.dumps(log,indent=2));print('Added',len(plans),'staggered capture barrels; ripped',len(rip),'old objects including relocated ESD return')
