import ast,json,math,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'captured6-BC.kicad_pcb';dest=P/'power6-BC.kicad_pcb';b=k.LoadBoard(str(source));power={'VBUS','FUSED_VBUS','+5V','VLED_5V'};remove=set();log=[]
def ident(o):return str(o.m_Uuid.AsString())
def clear(p,q,l,net):
 shape=k.SHAPE_SEGMENT(p,q,350000)
 return not any(o.GetNetname()!=net and o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()))
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA)or t.GetNetname()not in power or t.GetWidth()>=350000:continue
 p,q=t.GetStart(),t.GetEnd();length=(q-p).EuclideanNorm();net=t.GetNetname();layer=t.GetLayer()
 if clear(p,q,layer,net):t.SetWidth(350000);log.append({'net':net,'length_mm':length/1e6,'action':'full_width350um'});continue
 if length<1800000:continue
 a=k.VECTOR2I(round(p.x+(q.x-p.x)*450000/length),round(p.y+(q.y-p.y)*450000/length));z=k.VECTOR2I(round(q.x-(q.x-p.x)*450000/length),round(q.y-(q.y-p.y)*450000/length))
 if not clear(a,z,layer,net):continue
 for v,w,width in[(p,a,t.GetWidth()),(a,z,350000),(z,q,t.GetWidth())]:
  n=k.PCB_TRACK(b);n.SetStart(v);n.SetEnd(w);n.SetWidth(width);n.SetLayer(layer);n.SetNet(t.GetNet());b.Add(n)
 remove.add(ident(t));log.append({'net':net,'length_mm':length/1e6,'action':'350um_middle_450um_necks'})
k.SaveBoard(str(dest),b);node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](dest.read_text(),remove));b=k.LoadBoard(str(dest));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'power-trunk-widening.json').write_text(json.dumps(log,indent=2));print('Widened',len(log),'high-current trunk sections without clearance changes')
