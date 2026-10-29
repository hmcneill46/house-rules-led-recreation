"""Merge approved BC parts into routed scratch; never rebuild the routed board."""
import ast,hashlib,json,re,shutil,uuid
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;B2=P.parent;CAD=B2/'kicad';source=P/'candidate6-preBC.kicad_pcb';dest=P/'candidate6-BC.kicad_pcb';spec=json.loads((B2/'electrical-spec.json').read_text());placement=json.loads((B2/'placement.json').read_text())
assert len(spec['parts'])==82 and sum(p['assembly']=='factory'for p in spec['parts'])==55
old=k.LoadBoard(str(source));remove={str(t.m_Uuid.AsString())for t in old.GetTracks()if t.GetNetname()in('USB_DM','USB_DP','USB_DM_HOST','USB_DP_HOST')}
node=next(n for n in ast.parse(Path('hardware/tools/apply_checked_fanout_batch.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='filter_objects');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'local_filter','exec'),ns);dest.write_text(ns['filter_objects'](source.read_text(),remove));b=k.LoadBoard(str(dest));existing={f.GetReference():f for f in b.GetFootprints()};nets={ni.GetNetname():ni for ni in b.GetNetsByNetcode().values()};log=[]
for name in sorted({name for p in spec['parts']for name in p['pins'].values()if name}):
 if name not in nets:n=k.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
for p in spec['parts']:
 ref=p['ref'];pp=placement[ref]
 if ref not in existing:
  lib,name=p['footprint'].split(':');f=k.FootprintLoad(str(CAD/'footprints'/(lib+'.pretty')),name);assert f is not None,p['footprint'];b.Add(f);f.SetFPID(k.LIB_ID(lib,name));f.SetReference(ref);f.SetValue(p['value']);f.Flip(k.VECTOR2I(0,0),k.FLIP_DIRECTION_LEFT_RIGHT);f.Value().SetVisible(False);f.Reference().SetVisible(False)
  path=k.KIID_PATH();path.push_back(k.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:B2:main:sheet'))));path.push_back(k.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:main:'+ref))));f.SetPath(path)
  for key,value in [('MPN',p.get('mpn','')),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:f.SetField(key,value);f.GetField(key).SetVisible(False)
  f.SetOrientationDegrees(pp['angle']);f.SetPosition(k.VECTOR2I(k.FromMM(pp['x']+50),k.FromMM(pp['y']+50)));log.append({'ref':ref,'action':'added','xy_relative':[pp['x'],pp['y']]})
 else:
  f=existing[ref]
  if ref=='R15':f.SetPosition(k.VECTOR2I(k.FromMM(pp['x']+50),k.FromMM(pp['y']+50)));f.SetOrientationDegrees(pp['angle']);log.append({'ref':ref,'action':'moved','xy_relative':[pp['x'],pp['y']]})
 for pad in f.Pads():
  name=p['pins'].get(pad.GetNumber())
  if name:pad.SetNet(nets[name])
# Root-approved wider high-current buses, including the shared anode phases.
power={'VBUS','FUSED_VBUS','+5V','VLED_5V','+3V3','SW_3V3',*[f'COL{i}_A'for i in range(1,6)]};widened=[]
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA)and t.GetNetname()in power and t.GetWidth()<150000:widened.append({'uuid':str(t.m_Uuid.AsString()),'net':t.GetNetname(),'old_mm':k.ToMM(t.GetWidth())});t.SetWidth(150000)
# Protect the ESD flow-through joins. Upstream/downstream routing will meet the pads.
u7=next(f for f in b.GetFootprints()if f.GetReference()=='U7');esd={p.GetNumber():p for p in u7.Pads()}
for first,second in [('1','10'),('2','9')]:
 t=k.PCB_TRACK(b);t.SetStart(esd[first].GetPosition());t.SetEnd(esd[second].GetPosition());t.SetWidth(150000);t.SetLayer(k.B_Cu);t.SetNet(esd[first].GetNet());t.SetLocked(True);b.Add(t)
b.GetDesignSettings().m_TrackMinWidth=110000;b.GetDesignSettings().m_ViasMinSize=450000;b.GetDesignSettings().m_ViasMinAnnularWidth=75000
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b)
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
dru=dest.with_suffix('.kicad_dru');condition=' || '.join("A.NetName == '"+n+"'"for n in sorted(power));dru.write_text(dru.read_text()+'\n(rule "B2 power minimum150um" (condition "'+condition+'") (constraint track_width (min0.15mm)))\n'.replace('(min0.15mm)','(min 0.15mm)'))
(P/'fp-lib-table').write_text((CAD/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(CAD.resolve())))
(P/'bc-merge-actions.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'electrical_spec_sha256':hashlib.sha256((B2/'electrical-spec.json').read_bytes()).hexdigest(),'removed_old_USB_objects':len(remove),'parts':log,'widened_power':widened,'counts':{'footprints':len(list(b.GetFootprints())),'factory':55}},indent=2));print(len(list(b.GetFootprints())),'footprints;55 factory; widened',len(widened),'power segments')
