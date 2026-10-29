import argparse,json,shutil,subprocess,re,ast
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli';ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('dest',type=Path);a=ap.parse_args();log=[]
source=Path('hardware/tools/apply_checked_fanout_batch.py');node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns);filter_objects=ns['filter_objects']
shutil.copy2(a.source,a.dest)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(a.source.with_suffix('.'+ext),a.dest.with_suffix('.'+ext))
for i in range(35):
 b=k.LoadBoard(str(a.dest));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.dest),b);report=a.dest.with_name(a.dest.stem+'-drc.json')
 subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','-o',str(report),str(a.dest)],check=True,stdout=subprocess.DEVNULL)
 d=json.loads(report.read_text());items={str(o.m_Uuid.AsString()):o for o in b.GetTracks()};ids={it['uuid']for v in d['violations']if v['type']in('track_dangling','via_dangling')for it in v['items']}
 remove=[items[x]for x in ids if x in items and not items[x].IsLocked()]
 if not remove:break
 log.append({'pass':i,'removed':[{'uuid':str(t.m_Uuid.AsString()),'net':t.GetNetname(),'kind':t.GetClass()}for t in remove]})
 a.dest.write_text(filter_objects(a.dest.read_text(),{str(t.m_Uuid.AsString())for t in remove}))
 print('prune',i,len(remove),flush=True)
(a.dest.with_name(a.dest.stem+'-pruning.json')).write_text(json.dumps(log,indent=2));print('final unconnected',len(d['unconnected_items']),'violations',len(d['violations']),flush=True)
