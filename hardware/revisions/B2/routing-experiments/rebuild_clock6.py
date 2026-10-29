"""A direct In1 clock bus and clean CT endpoints, preserving USB/placement."""
import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'final-routed6.kicad_pcb';dest=P/'clock6.kicad_pcb';b=k.LoadBoard(str(source));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu];rip={str(t.m_Uuid.AsString())for t in b.GetTracks()if t.GetNetname()in('SCLK','CT_5V')};plans=[];paths=[]
def uid(o):return str(o.m_Uuid.AsString())
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def pad(ref,pin):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin)
for ref,pin in[('U1','24'),('U2','24'),('U3','24'),('U4','24'),('J5','1')]:
 p=pad(ref,pin);point=p.GetPosition();plans.append((ref,pin,point,p.GetNetname()))
 if ref.startswith('U'):
  x,y=k.ToMM(point.x),k.ToMM(point.y);paths.append(('SCLK',k.In1_Cu,[(x,y),(x-.45,y+.45),(x-.45,66.85)]))
 else:paths.append(('SCLK',k.In1_Cu,[(k.ToMM(point.x),k.ToMM(point.y)),(96.5,53.15),(96.5,66.85)]))
paths.append(('SCLK',k.In1_Cu,[(54.4,66.85),(130.6,66.85)]))
plans.append(('C10','1',vec(111.9,58.5),'CT_5V'));plans.append(('U6','4',pad('U6','4').GetPosition(),'CT_5V'))
# Check all planned copper before creating it; only unlocked nonUSB routes may move.
for ref,pin,point,net in plans:
 p=pad(ref,pin);circle=k.SHAPE_SEGMENT(point,point,450000);stub=k.SHAPE_SEGMENT(p.GetPosition(),point,110000)
 for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
  if uid(o)in rip or o.GetNetname()==net:continue
  if(o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999))or any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(circle,149999)for l in layers):
   if isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_'):raise RuntimeError(ref+'.'+pin+' protected clock/CT capture conflict '+o.GetClass()+' '+o.GetNetname())
   rip.add(uid(o))
for net,layer,path in paths:
 for a,z in zip(path,path[1:]):
  shape=k.SHAPE_SEGMENT(vec(*a),vec(*z),150000)
  for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
   if uid(o)in rip or o.GetNetname()==net or not o.IsOnLayer(layer):continue
   if o.GetEffectiveShape(layer).Collide(shape,149999):
    if isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_'):raise RuntimeError('Clock bus protected conflict '+o.GetClass()+' '+o.GetNetname()+' '+str(a)+str(z))
    rip.add(uid(o))
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),rip));b=k.LoadBoard(str(dest))
for ref,pin,point,net in plans:
 p=pad(ref,pin)
 if p.GetPosition()!=point:
  t=k.PCB_TRACK(b);t.SetStart(p.GetPosition());t.SetEnd(point);t.SetWidth(110000);t.SetLayer(k.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 v=k.PCB_VIA(b);v.SetPosition(point);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)
for net,layer,path in paths:
 for a,z in zip(path,path[1:]):
  t=k.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(150000);t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'clock-bus-actions.json').write_text(json.dumps({'removed_objects':sorted(rip),'captures':[{'ref':r,'pin':p,'xy':[v.x/1e6,v.y/1e6],'net':n}for r,p,v,n in plans],'paths':[{'net':n,'layer':b.GetLayerName(l),'polyline':p}for n,l,p in paths]},indent=2));print('Clock bus created; removed',len(rip),'old clock/CT or interfering unlocked objects')
