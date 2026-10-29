#!/usr/bin/env python3
"""Trim dangling route ends to real junctions; require full native pad connectivity.

This cleanup uses textual segment edits, not pcbnew ownership-changing Remove().
It is a recorded final-layout repair and refuses to run against a changed layout.
Fresh native DRC remains required after its connectivity invariant passes.
"""
import json,re,shutil,tempfile
from pathlib import Path
import wx,pcbnew as k
from clear_route_conflicts import blocks
wx.Log.EnableLogging(False);app=wx.App(False)
ROOT=Path(__file__).resolve().parents[2];pcb=ROOT/'hardware/kicad/house-rules-main.kicad_pcb';reports=ROOT/'hardware/reports'
source=pcb.read_text();scratch=Path(tempfile.mkdtemp(prefix='house-rules-trim-tails-'));test=scratch/pcb.name
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(pcb.with_suffix(ext),test.with_suffix(ext))
backup=pcb.parent/'backups'/('tail-trim-'+scratch.name.rsplit('-',1)[-1]);backup.mkdir(parents=True)
shutil.copy2(pcb,backup/pcb.name)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(pcb.with_suffix(ext),backup/pcb.with_suffix(ext).name)

def check(text):
 test.write_text(text);b=k.LoadBoard(str(test));b.BuildConnectivity();conn=b.GetConnectivity();nets={};labels={}
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetCode()>0 and p.GetNumber() and any(p.IsOnLayer(l) for l in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]):
    nets.setdefault(p.GetNetCode(),[]).append(p);labels[str(p.m_Uuid.AsString())]=f.GetReference()+':'+p.GetNumber()
 missing=[]
 for _,ps in nets.items():
  if len(ps)<2:continue
  ids={str(p.m_Uuid.AsString())for p in ps};got={str(o.m_Uuid.AsString())for o in conn.GetConnectedItems(ps[0])}
  if not ids<=got:missing.append([ps[0].GetNetname(),[labels[u]for u in ids-got]])
 return not missing,missing
if not check(source)[0]:raise RuntimeError('Input component pads are not fully connected')

def intersection(a,b,c,d):
 ax,ay=a;bx,by=b;cx,cy=c;dx,dy=d
 det=(ax-bx)*(cy-dy)-(ay-by)*(cx-dx)
 return [round(((ax*by-ay*bx)*(cx-dx)-(ax-bx)*(cx*dy-cy*dx))/det,6),round(((ax*by-ay*bx)*(cy-dy)-(ay-by)*(cx*dy-cy*dx))/det,6)]
plans={
 '2e5cf004-2b61-4b07-89d2-922d8f91226f':('end',[58.85,59.25]),
 '2509e9dc-be86-4953-9af2-47cd66a5e037':('end',intersection((79,58.45),(78.4,58.9),(78.5,58.7),(78.55,58.75))),
 'c2ba5dba-20af-4cd6-ac81-e558a5e027df':('end',[81.1,57]),
 '7bbd7842-2237-4771-9058-44c377effacb':('end',[129.4,58.75]),
 'ed9e4082-6e9e-47f5-92dd-b799047d134d':('end',intersection((86.3386,57.7226),(85.2154,58.8458),(85.4,58.65),(86.3,59.55))),
 '145d100f-391c-4859-9b6f-e3f053b9e724':('start',[102.077,61.313]),
 '7fff47a1-930a-4a12-9a11-2466ea741fe3':('start',[105.107333,57.836566]),
 'aa9dd10f-614b-4a43-b27b-524b43dcf08f':('start',[117.725,62.75]),
 '41b474c8-f511-4e0b-9853-f5e23fc619ab':('end',intersection((105.381,55.9107),(105.856,55.4362),(105.6,55.65),(105.85,55.9))),
}
report=json.loads((reports/'main-cleanup5-drc.json').read_text());done=[]
for v in report['violations']:
 if v['type']!='track_dangling':continue
 uid=v['items'][0]['uuid'];block=next((s for _,_,s in blocks(source)if s.startswith('(segment') and uid in s),None)
 if not block:continue
 # First remove a true leaf. The preceding cleanup pass can create new leaves.
 trial=source.replace(block,'',1);okay,missing=check(trial)
 if okay:source=trial;done.append({'uuid':uid,'action':'delete_leaf'});continue
 if uid not in plans:raise RuntimeError('Need junction plan for '+uid)
 end,xy=plans[uid];replacement=re.sub(r'\('+end+r'\s+[-\d.]+\s+[-\d.]+\)',f'({end} {xy[0]:.6f} {xy[1]:.6f})',block,count=1)
 trial=source.replace(block,replacement,1);okay,missing=check(trial)
 if not okay:raise RuntimeError('Trim broke component connectivity '+uid+': '+repr(missing))
 source=trial;done.append({'uuid':uid,'action':'trim_'+end,'new_junction_mm':xy})
 print(uid,done[-1],flush=True)
assert check(source)[0]
test.write_text(source);b=k.LoadBoard(str(test));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(pcb),b)
(reports/'main-tail-trim-actions.json').write_text(json.dumps({'actions':done,'all_component_pad_connectivity_preserved':True,'backup':str(backup)},indent=2)+'\n')
print('Saved',len(done),'guarded changes',flush=True)
