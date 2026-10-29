import hashlib,json,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;B2=P.parent;source=P/'ready6-BC.kicad_pcb';dest=P/'quote-snapshot-55.kicad_pcb';spec=json.loads((B2/'electrical-spec.json').read_text());parts={p['ref']:p for p in spec['parts']};b=k.LoadBoard(str(source));assert len(list(b.GetFootprints()))==82
for f in b.GetFootprints():
 p=parts[f.GetReference()];f.SetValue(p['value'])
 for key,value in [('MPN',p.get('mpn','')),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:f.SetField(key,value);f.GetField(key).SetVisible(False)
k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
metadata={'status':'UNRELEASED INCOMPLETE ROUTING; COST STUDY ONLY','factory':55,'footprints':82,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'electrical_spec_sha256':hashlib.sha256((B2/'electrical-spec.json').read_bytes()).hexdigest(),'known_unconnected_items':59,'new_basic_caps':'C5/C6/C7/C14/C16 C15849 SamsungCL10A105KB8NNNC'}
dest.with_suffix('.json').write_text(json.dumps(metadata,indent=2));print(dest);print(metadata['snapshot_sha256'])
