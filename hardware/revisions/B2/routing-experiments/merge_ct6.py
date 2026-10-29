import json,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'captured-last6.kicad_pcb';dest=P/'ct-merged6.kicad_pcb';b=k.LoadBoard(str(source));plan=json.loads((P/'ct-independent/ct-route-in2-plan.json').read_text());assert plan['net']=='CT_5V'and plan['trace_length_mm']<=12 and plan['vias']==0
renames={}
for uid,row in zip(plan['new_object_ids'],plan['polyline']):
 x,y,layer,xx,yy=row;assert layer=='In2.Cu';t=k.PCB_TRACK(b);t.SetStart(k.VECTOR2I(k.FromMM(x),k.FromMM(y)));t.SetEnd(k.VECTOR2I(k.FromMM(xx),k.FromMM(yy)));t.SetWidth(110000);t.SetLayer(k.In2_Cu);t.SetNet(b.FindNet('CT_5V'));renames[str(t.m_Uuid.AsString())]=uid;t.SetLocked(True);b.Add(t)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
raw=dest.read_text()
for new,old in renames.items():
 assert old not in raw
 raw=raw.replace(new,old)
dest.write_text(raw);b=k.LoadBoard(str(dest));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
print('Merged19CT-onlyIn2segments;',plan['trace_length_mm'],'mm; no new vias')
