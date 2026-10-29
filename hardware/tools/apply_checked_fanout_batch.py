#!/usr/bin/env python3
"""Apply the explicitly authorised second fanout batch; preserves project rules."""
import hashlib,json,math,re,shutil
from pathlib import Path
import wx
wx.Log.EnableLogging(False)
import pcbnew as k
app=wx.App(False)
ROOT=Path(__file__).resolve().parents[2];CAD=ROOT/'hardware/kicad';P=CAD/'house-rules-main.kicad_pcb';REPORTS=ROOT/'hardware/reports'
LAYERS=[k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]
def v(p):return k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
def ident(o):return str(o.m_Uuid.AsString())
def filter_objects(source,ids):
 depth=0;quoted=False;escaped=False;start=None;blocks=[]
 for i,c in enumerate(source):
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
   continue
  if c=='"':quoted=True;continue
  if c=='(':
   if depth==1:start=i
   depth+=1
  elif c==')':
   depth-=1
   if depth==1 and start is not None:blocks.append((start,i+1));start=None
 for a,z in reversed(blocks):
  block=source[a:z]
  if block.startswith('(segment')or block.startswith('(via'):
   m=re.search(r'\(uuid "([^"]+)"\)',block)
   if m and m[1]in ids:source=source[:a]+source[z:]
 return source

def conflicts(b,plan):
 net=plan['net'];poly=plan['stub_polyline_absolute_mm'];via=plan['via_absolute_mm'];tests=[]
 for a,c in zip(poly,poly[1:]):tests.append((k.B_Cu,k.SHAPE_SEGMENT(v(a),v(c),100000)))
 for layer in LAYERS:tests.append((layer,k.SHAPE_SEGMENT(v(via),v(via),400000)))
 out={}
 for o in [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
  if o.GetNetname()==net:continue
  for layer,shape in tests:
   if o.IsOnLayer(layer)and o.GetEffectiveShape(layer).Collide(shape,152000):
    out[ident(o)]=o;break
 return out

def main():
 report=json.loads((REPORTS/'main-grid1-drc.json').read_text())
 needed={re.search(r'\[([^]]+)\]',i['description'])[1]for d in report['unconnected_items']for i in d['items']if '['in i['description']}
 plans=[]
 for filename in ['driver-cs-escape-plans.json','sw2-escape-plans.json']:
  plans.extend(p for p in json.loads((REPORTS/filename).read_text())['plans']if p['net']in needed)
 backup=CAD/'backups/fanout2-before';backup.mkdir(parents=True,exist_ok=False)
 immutable={}
 for suffix in ['kicad_pcb','kicad_pro','kicad_dru']:
  p=CAD/f'house-rules-main.{suffix}';shutil.copy2(p,backup/p.name)
  if suffix!='kicad_pcb':immutable[p]=p.read_bytes()
 log={'status':'authorised exclusive fanout batch','source_board_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'plans':[]}
 for plan in plans:
  b=k.LoadBoard(str(P));byref={f.GetReference():f for f in b.GetFootprints()};pad=next(p for p in byref[plan['driver']].Pads()if p.GetNumber()==plan['pad'])
  if pad.GetNetname()!=plan['net']:raise RuntimeError('Pad net changed')
  if (v(plan['stub_polyline_absolute_mm'][0])-pad.GetPosition()).EuclideanNorm()>5000:raise RuntimeError('Pad location changed')
  remove=conflicts(b,plan);bad=[o for o in remove.values()if isinstance(o,k.PAD)or o.IsLocked()]
  if bad:
   log['plans'].append({'net':plan['net'],'applied':False,'reason':'current pad/locked collision','uuids':[ident(o)for o in bad]});print(plan['net'],'SKIP protected/pad conflict',flush=True);continue
  vp=v(plan['via_absolute_mm']);holebad=[]
  for o in [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
   if ident(o)in remove:continue
   if isinstance(o,k.PAD):d=max(o.GetDrillSize().x,o.GetDrillSize().y)
   elif isinstance(o,k.PCB_VIA):d=o.GetDrill()
   else:continue
   if d and (vp-o.GetPosition()).EuclideanNorm()<(200000+d)/2+250000:holebad.append(ident(o))
  if holebad:
   log['plans'].append({'net':plan['net'],'applied':False,'reason':'hole-spacing conflict','uuids':holebad});print(plan['net'],'SKIP hole conflict',flush=True);continue
  removed=[{'uuid':ident(o),'net':o.GetNetname(),'type':'via'if isinstance(o,k.PCB_VIA)else'track'}for o in remove.values()]
  P.write_text(filter_objects(P.read_text(),set(remove)))
  b=k.LoadBoard(str(P));net=b.FindNet(plan['net']);poly=plan['stub_polyline_absolute_mm']
  for a,c in zip(poly,poly[1:]):
   t=k.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(100000);t.SetLayer(k.B_Cu);t.SetNet(net);t.SetLocked(True);b.Add(t)
  via=k.PCB_VIA(b);via.SetPosition(vp);via.SetWidth(400000);via.SetDrill(200000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(net);via.SetLocked(True);b.Add(via)
  b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(P),b)
  # No design-rule changes are authorised by this script.
  for path,raw in immutable.items():path.write_bytes(raw)
  log['plans'].append({'net':plan['net'],'applied':True,'via':plan['via_absolute_mm'],'stub':poly,'removed':removed})
  print(plan['net'],'APPLIED;removed',len(remove),'unlocked objects',flush=True)
 b=k.LoadBoard(str(P));widened=[]
 for t in b.GetTracks():
  if not isinstance(t,k.PCB_VIA)and t.GetNetname()in ['+5V','VBUS']and t.GetWidth()<150000:
   widened.append({'uuid':ident(t),'net':t.GetNetname(),'old_width_mm':k.ToMM(t.GetWidth())});t.SetWidth(150000)
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(P),b)
 for path,raw in immutable.items():path.write_bytes(raw)
 log['power_tracks_widened_to_0.15_mm']=widened;log['final_board_sha256']=hashlib.sha256(P.read_bytes()).hexdigest()
 (REPORTS/'main-fanout2-actions.json').write_text(json.dumps(log,indent=2)+'\n');print('Widened',len(widened),'power tracks. Native DRC required.',flush=True)
if __name__=='__main__':main()
