#!/usr/bin/env python3
"""Export explicitly UNROUTED, quotation-only inputs. Never a production package."""
import collections,csv,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
import wx,pcbnew as k
B2=Path(__file__).resolve().parents[1];CLI=Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli');app=wx.App(False)
spec=json.loads((B2/'electrical-spec.json').read_text());factory={p['ref']:p for p in spec['parts']if p.get('assembly')=='factory'}
assert len(factory)==49
out=B2/'quotes/cost-study-2026-10-29';out.mkdir(parents=True,exist_ok=True)
def run(a):
 r=subprocess.run([str(x)for x in a],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 return r.stdout
for layers,suffix in [(4,''),(6,'-6L')]:
 source=B2/f'kicad/house-rules-main-B2{suffix}.kicad_pcb';target=out/f'{layers}L';target.mkdir(exist_ok=True)
 pcb=target/f'B2-{layers}L-UNROUTED-COST-STUDY-DO-NOT-ORDER.kicad_pcb';shutil.copy2(source,pcb)
 b=k.LoadBoard(str(pcb));actual={f.GetReference():f for f in b.GetFootprints()}
 for ref,p in factory.items():
  f=actual[ref]
  assert f.GetField('MPN').GetText()==p['mpn'] and f.GetField('LCSC').GetText()==p['lcsc']
  assert f.GetLayer()==k.B_Cu
 fab=target/'fabrication';fab.mkdir(exist_ok=True)
 copper=['F.Cu']+[f'In{i}.Cu'for i in range(1,layers-1)]+['B.Cu']
 run([CLI,'pcb','export','gerbers','--layers',','.join(copper+['F.Mask','B.Mask','F.SilkS','B.SilkS','Edge.Cuts']),'--use-drill-file-origin','--subtract-soldermask','--check-zones','--output',str(fab)+'/',pcb])
 run([CLI,'pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--excellon-oval-format','route','--output',str(fab)+'/',pcb])
 raw=target/'native-all.csv';run([CLI,'pcb','export','pos','--format','csv','--units','mm','--side','both','--use-drill-file-origin','--smd-only','--exclude-dnp','--output',raw,pcb])
 with raw.open(newline='')as f:positions=[r for r in csv.DictReader(f)if r['Ref']in factory]
 assert len(positions)==49 and {r['Ref']for r in positions}==set(factory)
 with (target/'B2-UNROUTED-COST-STUDY-CPL.csv').open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=['Designator','Mid X','Mid Y','Layer','Rotation']);w.writeheader()
  for p in positions:w.writerow({'Designator':p['Ref'],'Mid X':p['PosX']+'mm','Mid Y':p['PosY']+'mm','Layer':p['Side'],'Rotation':p['Rot']})
 groups=collections.defaultdict(list)
 for ref,p in factory.items():groups[(p['mpn'],p['lcsc'],p['footprint'].split(':')[1])].append(ref)
 with (target/'B2-UNROUTED-COST-STUDY-BOM.csv').open('w',newline='')as f:
  w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
  for (mpn,code,fp),refs in sorted(groups.items()):w.writerow([mpn,','.join(refs),fp,code])
 note='UNROUTED COST STUDY ONLY. DO NOT ORDER OR MANUFACTURE. This is an incomplete placement used only to estimate costs. It has not passed connectivity DRC. Board outline/stack/part count are actual candidate values. Final routing/drill count/rotations/process must be re-exported and reviewed before production.\n'
 (target/'README-DO-NOT-ORDER.txt').write_text(note)
 with zipfile.ZipFile(target/f'B2-{layers}L-UNROUTED-COST-STUDY-GERBERS.zip','w',zipfile.ZIP_DEFLATED)as z:
  for p in sorted(fab.iterdir()):z.write(p,p.name)
 (target/'manifest.json').write_text(json.dumps({'status':'UNROUTED COST STUDY ONLY - NEVER PRODUCTION','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'spec_sha256':hashlib.sha256((B2/'electrical-spec.json').read_bytes()).hexdigest(),'layers':layers,'size_mm':[88.4,17.3],'thickness_mm':1.6,'ordinary_via_mm':[.6,.3],'finish':'ENIG','assembly':'49 bottom factory components; seven owned LEDs and 18 wire pads excluded','via_cover': 'standard tented, no filled/capped' if layers==4 else 'all ordinary 0.3mm via drills resin filled and copper capped; 84 LED 0.9mm PTH holes stay open','warnings':['Unrouted: no fabrication approval','49 factory CPL entries, native bottom angles not manually corrected','Requote completed routing and actual via count before payment']},indent=2)+'\n')
 print(target.resolve())
