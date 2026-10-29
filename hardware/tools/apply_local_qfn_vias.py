#!/usr/bin/env python3
"""Authorised local 0.10 mm QFN via-pad clearance and eight inner-land escapes.

No via-via, via-track, pad-pad, hole or annular-ring constraint is relaxed.
Run with KiCad Python only while holding exclusive edit ownership of main PCB.
"""
import hashlib,json,math,re,shutil
from pathlib import Path
import apply_checked_fanout_batch as base
k=base.k;ROOT=base.ROOT;CAD=base.CAD;P=base.P;REPORTS=base.REPORTS;LAYERS=base.LAYERS
RULE='''
# Approved JLC 1oz six-layer QFN via-in-pad escape. Only VIA-to-PAD pairs
# intersecting the SAME U1-U4 courtyard qualify; other clearance stays 0.15.
(rule "QFN local via-pad 100um"
 (condition "((A.Type == 'Via' && B.Type == 'Pad') || (A.Type == 'Pad' && B.Type == 'Via')) && ((A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1')) || (A.intersectsCourtyard('U2') && B.intersectsCourtyard('U2')) || (A.intersectsCourtyard('U3') && B.intersectsCourtyard('U3')) || (A.intersectsCourtyard('U4') && B.intersectsCourtyard('U4')))")
 (constraint clearance (min 0.10mm)))
'''
CONTACTS=[('U1','20',(54.4,58.85)),('U2','20',(79.8,58.85)),('U4','20',(130.6,58.85)),('U1','5',(57.8,58.85)),('U2','5',(83.2,58.85)),('U3','21',(105.2,58.45)),('U3','6',(108.6,59.25)),('U3','3',(108.6,58.05))]
def main():
 d=json.loads((REPORTS/'main-grid2-drc.json').read_text());needed={re.search(r'\[([^]]+)\]',i['description'])[1]for x in d['unconnected_items']for i in x['items']if '['in i['description']}
 backup=CAD/'backups/local-innerland-before';backup.mkdir(parents=True,exist_ok=False)
 for ext in ['kicad_pcb','kicad_pro','kicad_dru']:shutil.copy2(CAD/f'house-rules-main.{ext}',backup/f'house-rules-main.{ext}')
 pro=CAD/'house-rules-main.kicad_pro';old=json.loads(pro.read_text());new=json.loads(pro.read_text());new['board']['design_settings']['rules']['min_clearance']=.1
 assert all(c['clearance']==.15 for c in new['net_settings']['classes'])
 assert new['board']['design_settings']['rules']['min_via_annular_width']==.1
 pro.write_text(json.dumps(new,indent=2)+'\n');dru=CAD/'house-rules-main.kicad_dru';dru.write_text(dru.read_text().replace('(min 0.15)', '(min 0.15mm)')+RULE)
 preserved={pro:pro.read_bytes(),dru:dru.read_bytes()};log={'status':'exclusive authorised local QFN via-pad fanout','board_sha256_before':hashlib.sha256(P.read_bytes()).hexdigest(),'actions':[]}
 for ref,pin,where in CONTACTS:
  b=k.LoadBoard(str(P));fp={f.GetReference():f for f in b.GetFootprints()};pad=next(p for p in fp[ref].Pads()if p.GetNumber()==pin);net=pad.GetNetname()
  if net not in needed:print(net,'not remaining, skip',flush=True);continue
  for name in ['U1','U2','U3','U4']:fp[name].BuildCourtyardCaches()
  yards=[fp[name].GetCourtyard(k.B_CrtYd)for name in ['U1','U2','U3','U4']]
  start=k.VECTOR2I(pad.GetPosition());vp=base.v(where);vs=k.SHAPE_SEGMENT(vp,vp,400000);stub=k.SHAPE_SEGMENT(start,vp,100000);remove={};eligible=[]
  for o in [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
   if o.GetNetname()==net:continue
   if o.IsOnLayer(k.B_Cu)and o.GetEffectiveShape(k.B_Cu).Collide(stub,149999):remove[base.ident(o)]=o
   for l in LAYERS:
    if not o.IsOnLayer(l):continue
    shape=o.GetEffectiveShape(l);local=isinstance(o,k.PAD)and any(y.Collide(vs)and y.Collide(shape)for y in yards)
    if local:eligible.append({'pad':o.GetParentFootprint().GetReference()+'.'+o.GetNumber(),'net':o.GetNetname()})
    if shape.Collide(vs,99999 if local else 149999):remove[base.ident(o)]=o
  blocked=[o for o in remove.values()if isinstance(o,k.PAD)or o.IsLocked()]
  if blocked:raise RuntimeError(f'{ref}.{pin} candidate hits protected/pad copper: '+str([(base.ident(o),o.GetNetname())for o in blocked]))
  for o in [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
   if base.ident(o)in remove:continue
   if isinstance(o,k.PAD):drill=max(o.GetDrillSize().x,o.GetDrillSize().y)
   elif isinstance(o,k.PCB_VIA):drill=o.GetDrill()
   else:continue
   if drill and(vp-o.GetPosition()).EuclideanNorm()<(200000+drill)/2+250000:raise RuntimeError(f'{ref}.{pin} hole-spacing conflict '+base.ident(o))
  ripped=[{'uuid':base.ident(o),'net':o.GetNetname(),'type':'via'if isinstance(o,k.PCB_VIA)else'track'}for o in remove.values()]
  P.write_text(base.filter_objects(P.read_text(),set(remove)));b=k.LoadBoard(str(P));ni=b.FindNet(net)
  t=k.PCB_TRACK(b);t.SetStart(start);t.SetEnd(vp);t.SetWidth(100000);t.SetLayer(k.B_Cu);t.SetNet(ni);t.SetLocked(True);b.Add(t)
  via=k.PCB_VIA(b);via.SetPosition(vp);via.SetWidth(400000);via.SetDrill(200000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(ni);via.SetLocked(True);b.Add(via)
  b.GetDesignSettings().m_MinClearance=100000
  b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(P),b)
  for path,raw in preserved.items():path.write_bytes(raw)
  log['actions'].append({'ref':ref,'pin':pin,'net':net,'via_absolute_mm':where,'via_diameter_mm':.4,'via_drill_mm':.2,'stub_width_mm':.1,'eligible_local_via_pad_pairs':eligible,'removed':ripped});print(net,'APPLIED, removed',len(remove),'unlocked objects',flush=True)
 # Explicitly prove that no other project setting changed.
 check=json.loads(pro.read_text());check['board']['design_settings']['rules']['min_clearance']=old['board']['design_settings']['rules']['min_clearance'];assert check==old
 log['board_sha256_after']=hashlib.sha256(P.read_bytes()).hexdigest();log['project_change']='Only global minimum clearance 0.15 ->0.10; netclasses0.15 and all other constraints unchanged.'
 (REPORTS/'main-innerland-actions.json').write_text(json.dumps(log,indent=2)+'\n')
 print('Batch complete. Native DRC and negative control required.',flush=True)
if __name__=='__main__':main()
