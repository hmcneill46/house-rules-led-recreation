#!/usr/bin/env python3
"""Import a session to a separate candidate, normalize sub-fabrication necks."""
import argparse,json,shutil
from pathlib import Path
import wx,pcbnew as k
app=wx.App(False);B2=Path(__file__).resolve().parents[1];D=B2/'kicad'
a=argparse.ArgumentParser();a.add_argument('--six',action='store_true');args=a.parse_args()
base='house-rules-main-B2'+('-6L'if args.six else '')
b=k.LoadBoard(str(D/(base+'.kicad_pcb')))
assert b.GetCopperLayerCount()==(6 if args.six else 4), 'Historical routing import only: source/session layer counts must match'
assert k.ImportSpecctraSES(b,str(D/(base+'.ses')))
changes=[]
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):

  assert abs(k.ToMM(t.GetWidth(k.F_Cu))-.6)<.001
  assert abs(k.ToMM(t.GetDrillValue())-.3)<.001
  t.SetDrill(k.FromMM(.3))
  if args.six:t.SetFillingMode(k.FILLING_MODE_FILLED);t.SetCappingMode(k.CAPPING_MODE_CAPPED)
 elif k.ToMM(t.GetWidth())<.1016:
  changes.append({'net':t.GetNetname(),'before_mm':k.ToMM(t.GetWidth()),'after_mm':.11});t.SetWidth(k.FromMM(.11))
name=base+'-routed-pass1';file=D/(name+'.kicad_pcb');b.BuildConnectivity();k.SaveBoard(str(file),b)
shutil.copy2(D/'house-rules-main-B2.kicad_pro',D/(name+'.kicad_pro'));shutil.copy2(D/'house-rules-main-B2.kicad_dru',D/(name+'.kicad_dru'))
(B2/'reports'/(name+'-width-actions.json')).write_text(json.dumps(changes,indent=2)+'\n')
print(file, 'widened',len(changes),'sub-.1016mm necks to .11mm')
