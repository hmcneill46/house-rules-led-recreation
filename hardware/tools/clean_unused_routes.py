#!/usr/bin/env python3
"""Remove unused tails only when every component pad stays connected.

Uses native connectivity for each proposed deletion, never API Remove().
A fresh native DRC is still required. Does not waive any fabrication rule.
"""
import argparse,json,re,shutil,tempfile
from pathlib import Path
import wx,pcbnew as k
from clear_route_conflicts import blocks
app=wx.App(False)
ap=argparse.ArgumentParser();ap.add_argument('pcb',type=Path);ap.add_argument('report',type=Path);a=ap.parse_args()
source=a.pcb.read_text();report=json.loads(a.report.read_text());scratch=Path(tempfile.mkdtemp(prefix='house-rules-route-cleanup-'));test=scratch/a.pcb.name
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(a.pcb.with_suffix(ext),test.with_suffix(ext))
keepalive=[]
def pads_connected(text):
 test.write_text(text);b=k.LoadBoard(str(test));keepalive.append(b);b.BuildConnectivity();c=b.GetConnectivity();by_net={}
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetCode()>0 and p.GetNumber() and any(p.IsOnLayer(l)for l in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]):by_net.setdefault(p.GetNetCode(),set()).add(str(p.m_Uuid.AsString()))
 byid={str(p.m_Uuid.AsString()):p for f in b.GetFootprints()for p in f.Pads()}
 for net,ids in by_net.items():
  if len(ids)<2:continue
  p=byid[next(iter(ids))];reached={str(o.m_Uuid.AsString())for o in c.GetConnectedItems(p)}
  if not ids.issubset(reached):return False
 return True
if not pads_connected(source):raise SystemExit('Physical component pads are not yet fully connected; finish them before cleanup.')
index={}
for start,end,block in blocks(source):
 u=re.search(r'\(uuid "?([a-f0-9-]+)"?\)',block)
 if u and block.startswith(('(segment','(via')):index[u[1]]=block
candidates=[]
for v in report['violations']:
 if v['type']not in ['track_dangling','via_dangling']:continue
 for item in v['items']:
  uid=item['uuid']
  if uid in index and uid not in candidates:candidates.append(uid)
removed=[];retained=[]
for uid in candidates:
 block=index[uid]
 # Keep deliberate thermal and supply plane escapes.
 if block.startswith('(via')and '(locked yes)'in block and any(f'(net "{n}")'in block for n in ['GND','+5V']):retained.append(uid);continue
 trial=source.replace(block,'',1)
 if pads_connected(trial):source=trial;removed.append(uid)
 else:retained.append(uid)
 print('cleanup',len(removed),'removed;',len(retained),'retained',flush=True)
# The temp project is a byte-for-byte settings copy; SaveBoard cannot introduce
# unrelated default design rules when writing the actual source path.
test.write_text(source);b=k.LoadBoard(str(test));b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.pcb),b)
(a.report.parent/'main-unused-route-cleanup.json').write_text(json.dumps({'removed':removed,'retained':retained,'all_component_pad_connectivity_preserved':True,'temporary_directory':str(scratch)},indent=2)+'\n')
print('Removed',len(removed),'unused objects; retained',len(retained),'; rerun native DRC.',flush=True)
