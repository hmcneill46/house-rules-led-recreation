import json,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
B2=Path(__file__).resolve().parents[1];OUT=Path(__file__).parent
source=B2/'kicad/house-rules-main-B2.kicad_pcb'
b=k.LoadBoard(str(source))
assert k.ImportSpecctraSES(b,str(B2/'kicad/house-rules-main-B2.ses'))
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());dest=OUT/'routed4.kicad_pcb';k.SaveBoard(str(dest),b)
for ext in ('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
pads=[]
for f in b.GetFootprints():
 if f.GetReference()in ('U1','U2','U3','U4','DS1','DS2','C1','R1'):
  for p in f.Pads():
   pads.append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'xy':[k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)],'size':[k.ToMM(p.GetSize().x),k.ToMM(p.GetSize().y)],'shape':p.GetShape(),'orientation':p.GetOrientationDegrees()})
(OUT/'pads.json').write_text(json.dumps(pads,indent=2))
print(len(list(b.GetTracks())),'tracks/vias imported')
