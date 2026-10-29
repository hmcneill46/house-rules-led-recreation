import json
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;b=k.LoadBoard(str(P/'routed4.kicad_pcb'))
nets=['D1_ROW1_K','D2_ROW2_K','D2_ROW4_K','D3_ROW2_K','D3_ROW5_K','D3_ROW7_K','D4_ROW6_K','CC1_ADC']
for net in nets:
 print('\n',net)
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==net:print('pad',f.GetReference(),p.GetNumber(),k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y))
 for t in b.GetTracks():
  if t.GetNetname()==net:
   if isinstance(t,k.PCB_VIA):print('via',k.ToMM(t.GetPosition().x),k.ToMM(t.GetPosition().y),k.ToMM(t.GetWidth(k.B_Cu)))
   else:print('track',b.GetLayerName(t.GetLayer()),[k.ToMM(v)for v in (t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)],k.ToMM(t.GetWidth()))
