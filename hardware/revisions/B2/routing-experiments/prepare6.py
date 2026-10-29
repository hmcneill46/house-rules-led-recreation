import json,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'escaped-final4.kicad_pcb';dest=P/'candidate6-preBC.kicad_pcb';b=k.LoadBoard(str(source));b.SetCopperLayerCount(6)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
ds=b.GetDesignSettings();ds.m_ViasMinAnnularWidth=75000;ds.m_ViasMinSize=450000;ds.m_TrackMinWidth=110000
pads=[p for f in b.GetFootprints()for p in f.Pads()];tracks=list(b.GetTracks());layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]
log=[]
for ref,pin in [('U2','4'),('U3','5'),('U4','8')]:
 p=next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==pin);point=p.GetPosition();circle=k.SHAPE_SEGMENT(point,point,450000);conflicts=[]
 for o in pads+tracks:
  if o.GetNetname()==p.GetNetname():continue
  if any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(circle,149999)for l in layers):conflicts.append(o)
 if any(isinstance(o,k.PAD)or o.IsLocked()for o in conflicts):raise RuntimeError('Protected collision '+ref+'.'+pin+' '+str([(o.GetClass(),o.GetNetname())for o in conflicts]))
 for o in conflicts:b.Remove(o)
 v=k.PCB_VIA(b);v.SetPosition(point);v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(p.GetNet());v.SetLocked(True);b.Add(v)
 log.append({'ref':ref,'pin':pin,'xy':[k.ToMM(point.x),k.ToMM(point.y)],'via':'.45/.30 filled/capped','ripped':[{'uuid':str(o.m_Uuid.AsString()),'net':o.GetNetname()}for o in conflicts]})
for f in b.GetFootprints():
 if f.GetReference()not in('U1','U2','U3','U4'):continue
 ep=next(p for p in f.Pads()if p.GetNumber()=='25');center=ep.GetPosition()
 for x,y in[(-.55,0),(.55,0),(0,.55)]:
  point=k.VECTOR2I(center.x+k.FromMM(x),center.y+k.FromMM(y));circle=k.SHAPE_SEGMENT(point,point,600000)
  conflicts=[o for o in pads+list(b.GetTracks())if o.GetNetname()!='GND'and any(o.IsOnLayer(l)and o.GetEffectiveShape(l).Collide(circle,149999)for l in layers)]
  if conflicts:
   log.append({'ref':f.GetReference(),'EP_offset':[x,y],'status':'thermal blocked','obstacles':[(o.GetClass(),o.GetNetname())for o in conflicts]});continue
  v=k.PCB_VIA(b);v.SetPosition(point);v.SetWidth(600000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(ep.GetNet());v.SetLocked(True);b.Add(v);log.append({'ref':f.GetReference(),'EP_offset':[x,y],'status':'thermal added'})
for layer in(k.In3_Cu,k.In4_Cu):
 z=k.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(150000);z.SetThermalReliefGap(250000);z.SetThermalReliefSpokeWidth(250000);poly=z.Outline();poly.NewOutline()
 for x,y in[(50.3,50.3),(138.1,50.3),(138.1,67.0),(50.3,67.0)]:poly.Append(k.FromMM(x),k.FromMM(y))
 b.Add(z)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
p=json.loads(dest.with_suffix('.kicad_pro').read_text());rules=p['board']['design_settings']['rules'];rules.update(min_track_width=.11,min_via_diameter=.45,min_via_annular_width=.075);dest.with_suffix('.kicad_pro').write_text(json.dumps(p,indent=2))
(P/'prepare6-actions.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
