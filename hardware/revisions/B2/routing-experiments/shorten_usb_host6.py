"""Replace long autorouter host detours with a short paired In3 corridor."""
import ast,json,re,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'usb-done6.kicad_pcb';dest=P/'usb-short6.kicad_pcb';b=k.LoadBoard(str(source));plans={x['label']:x for x in json.loads((P/'usb-escape-plan.json').read_text())};log=json.loads((P/'usb-route-actions.json').read_text());keep={x[key]for label,x in plans.items()if label.endswith(('_BC_HOST','_MCU'))for key in('via_uuid','stub_uuid')if x.get(key)}
def ident(o):return str(o.m_Uuid.AsString())
def vec(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def pad(ref,pin):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin)
remove={ident(t)for t in b.GetTracks()if t.GetNetname()in('USB_DM_HOST','USB_DP_HOST')and ident(t)not in keep}
# Move only the BQ AL source escape; the GPIO/divider parts remain fixed.
for t in b.GetTracks():
 if t.GetNetname()!='BC_AL_N':continue
 if isinstance(t,k.PCB_VIA)and 111500000<=t.GetPosition().x<=114500000 and 59500000<=t.GetPosition().y<=61500000:remove.add(ident(t))
 if not isinstance(t,k.PCB_VIA)and t.GetLayer()==k.B_Cu and all(111500000<=p.x<=114500000 and 59500000<=p.y<=61500000 for p in(t.GetStart(),t.GetEnd())):remove.add(ident(t))
paths={'DM':[(112.2,61.55),(112.4,61.35),(112.4,51.8),(109.44,50.85)],'DP':[(113.0,61.1),(112.75,60.85),(112.75,51.6),(111.98,50.85)]};blocked=[]
for channel,path in paths.items():
 net='USB_'+channel+'_HOST'
 for p,q in zip(path,path[1:]):
  shape=k.SHAPE_SEGMENT(vec(*p),vec(*q),150000)
  for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
   if ident(o)in remove or o.GetNetname()==net or not o.IsOnLayer(k.In3_Cu):continue
   if o.GetEffectiveShape(k.In3_Cu).Collide(shape,149999):
    if isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_'):raise RuntimeError('Protected USB corridor conflict '+o.GetClass()+' '+o.GetNetname())
    remove.add(ident(o));blocked.append((ident(o),o.GetNetname()))
# New AL capture and the short external B-side neck.
al=vec(111.9,60.55);shape=k.SHAPE_SEGMENT(al,al,450000);stub=k.SHAPE_SEGMENT(pad('U9','4').GetPosition(),al,110000);layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]
for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
 if ident(o)in remove or o.GetNetname()=='BC_AL_N':continue
 if(o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999))or any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(shape,149999)for l in layers):
  if isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_'):raise RuntimeError('Protected AL escape collision '+o.GetClass()+' '+o.GetNetname())
  remove.add(ident(o));blocked.append((ident(o),o.GetNetname()))
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),remove));b=k.LoadBoard(str(dest))
for channel,path in paths.items():
 ids=[];poly=[];length=0;net=b.FindNet('USB_'+channel+'_HOST')
 for p,q in zip(path,path[1:]):
  a,z=vec(*p),vec(*q);t=k.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetWidth(150000);t.SetLayer(k.In3_Cu);t.SetNet(net);t.SetLocked(True);b.Add(t);ids.append(ident(t));poly.append([*p,'In3.Cu',*q]);length+=(z-a).EuclideanNorm()/1e6
 row=next(r for r in log if r['label']==channel+'_BC_HOST_to_MCU');row.update(segments=len(poly),vias=0,trace_length_mm=length,new_object_ids=ids,polyline=poly,result='connected',method='explicit short coupled In3 corridor')
t=k.PCB_TRACK(b);t.SetStart(pad('U9','4').GetPosition());t.SetEnd(al);t.SetWidth(110000);t.SetLayer(k.B_Cu);t.SetNet(b.FindNet('BC_AL_N'));t.SetLocked(True);b.Add(t);v=k.PCB_VIA(b);v.SetPosition(al);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('BC_AL_N'));v.SetLocked(True);b.Add(v)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
(P/'usb-shortening-actions.json').write_text(json.dumps({'removed':sorted(remove),'corridor_conflicts_reroute':blocked,'moved_AL_capture':[111.9,60.55],'route_actions':log},indent=2));(P/'usb-route-actions.json').write_text(json.dumps(log,indent=2));print('Short HOST paths',[(r['label'],r['trace_length_mm'])for r in log if'HOST'in r['label']]);print('Removed',len(remove),'objects;',len(blocked),'nonUSB corridor conflicts torepair')
