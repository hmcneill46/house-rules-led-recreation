"""Isolated CT-only scratch route; does not touch active candidates."""
import ast,collections,heapq,json,math,shutil,subprocess,time
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).resolve().parent;S=P.parent/'ct-help6.kicad_pcb'
O=P/'ct-route-in2.kicad_pcb'
b=k.LoadBoard(str(S));LAYERS=[k.In2_Cu]
STEP=25000;MINX=110000000;MAXX=123000000;MINY=55000000;MAXY=62500000
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(S.with_suffix(ext),O.with_suffix(ext))
module=ast.parse((P.parent/'grid_finish.py').read_text())
functions=[n for n in module.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
route_node=next(n for n in functions if n.name=='route')
for n in ast.walk(route_node):
 if isinstance(n,ast.Constant) and n.value==55:n.value=150
exec(compile(ast.Module(body=functions,type_ignores=[]),str(P.parent/'grid_finish.py'),'exec'),globals())
parts={f.GetReference():f for f in b.GetFootprints()}
a=next(p for p in parts['C10'].Pads() if p.GetNumber()=='1')
z=next(p for p in parts['U6'].Pads() if p.GetNumber()=='4')
b.BuildConnectivity();res=route(a,z)
print(json.dumps(res,indent=2),flush=True)
(P/'ct-route-in2-plan.json').write_text(json.dumps(res,indent=2)+'\n')
if res['result']=='connected':
 for v in b.GetTracks():
  if isinstance(v,k.PCB_VIA) and ident(v) in res['new_object_ids']:
   v.SetFillingMode(k.FILLING_MODE_FILLED);v.SetCappingMode(k.CAPPING_MODE_CAPPED)
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(O),b)
 cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
 subprocess.run([cli,'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(P/'ct-route-in2-drc.json'),str(O)],check=True)
