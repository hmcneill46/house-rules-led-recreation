import argparse,hashlib,json,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('dest',type=Path);a=ap.parse_args();spec=json.loads((P.parent/'electrical-spec.json').read_text());parts={p['ref']:p for p in spec['parts']};b=k.LoadBoard(str(a.source))
for f in b.GetFootprints():
 p=parts[f.GetReference()];f.SetValue(p['value'])
 for key,value in [('MPN',p.get('mpn','')),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:f.SetField(key,value);f.GetField(key).SetVisible(False)
k.SaveBoard(str(a.dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(a.source.with_suffix('.'+ext),a.dest.with_suffix('.'+ext))
print(a.dest,hashlib.sha256(a.dest.read_bytes()).hexdigest())
