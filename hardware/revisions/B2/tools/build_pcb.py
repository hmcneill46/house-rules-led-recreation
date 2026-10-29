#!/usr/bin/env python3
"""Create a B2 placement seed and ordinary-via routing input, not final routing.

Rebuilding an existing board requires --rebuild-placement, since this deliberately
replaces routing. Electrical source is owned independently by electrical-spec.json.
"""
import argparse, hashlib, json, re, shutil, uuid
from pathlib import Path
from xml.etree import ElementTree as ET
import wx, pcbnew as k
B2=Path(__file__).resolve().parents[1];ROOT=B2.parents[2];OUT=B2/'kicad'
STD=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
CLI=Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
app=wx.App(False)
def mm(x):return k.FromMM(x)
def xy(x,y):return k.VECTOR2I(mm(x),mm(y))
def pos(x,y):return xy(x+50,y+50)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,s))
def place_spec():
 p={}
 def put(ref,x,y,a=0):p[ref]={'x':x,'y':y,'angle':a}
 for i in range(7):put('DS'+str(i+1),6.1+12.7*i,8.65)
 for i,x in enumerate((6.1,31.5,56.9,82.3),1):
  put('U'+str(i),x,8.65 if i<4 else 7.0)
  put('C'+str(i),x,4.3 if i<4 else 3.0)
  put('R'+str(i),x,13.0 if i<4 else 11.0)
 for i,(x,y) in enumerate(((18.8,4.0),(18.8,8.65),(18.8,13.3),(44.2,4.0),(44.2,8.65)),1):put('Q'+str(i),x,y)
 for ref,x,y,a in [('U5',44.2,13.3,0),('U6',69.6,8.0,0),('U8',69.6,3.6,0),('U7',69.6,12.7,90),
 ('F1',75.95,5,90),('D1',75.95,13.6,90),('C14',75.95,8.5,0),('C13',63.25,3.6,0),
 ('C5',37.85,13.3,0),('C6',63.25,6.1,0),('C7',50.55,13.3,0),('C8',75.95,10.3,0),
 ('C9',44.2,16.1,0),('C10',63.25,8.5,0),('R15',12.45,6.1,0),('R16',37.85,16.1,0),
 ('R17',82.3,13.4,0),('R18',82.3,15.7,0),('R19',69.6,15.3,0),('R20',63.25,14.0,0),
 ('C11',50.55,16.1,0),('C12',56.9,16.0,0)]:put(ref,x,y,a)
 for i,(x,y) in enumerate(((25.15,3.6),(25.15,8.65),(25.15,13.3),(37.85,3.6),(37.85,8.65)),5):put('R'+str(i),x,y)
 for i,(x,y) in enumerate(((12.45,3.6),(12.45,8.65),(12.45,13.3),(50.55,3.6),(50.55,8.65)),10):put('R'+str(i),x,y)
 for i in range(12):put('J'+str(i+1),34.04+2.54*i,.85)
 for i in range(6):put('J'+str(i+13),69.6+2.54*i,.85)
 # BC1.2 addition: placement only; existing routed boards are not rebuilt here.
 for ref,x,y in [('U9',63.25,11.3),('C15',68.0,10.7),('C16',71.2,10.7),
                 ('R21',25.15,6.1),('R22',25.15,11.0),('R23',12.45,11.0),
                 ('J19',23.88,.85),('J20',26.42,.85)]:put(ref,x,y)
 return p

def project():
 default={'bus_width':12,'clearance':.15,'diff_pair_gap':.15,'diff_pair_via_gap':.25,'diff_pair_width':.15,'line_style':0,'microvia_diameter':.3,'microvia_drill':.1,'name':'Default','pcb_color':'rgba(0,0,0,0)','schematic_color':'rgba(0,0,0,0)','track_width':.15,'via_diameter':.6,'via_drill':.3,'wire_width':6}
 p=json.loads((OUT/'house-rules-main-B2.kicad_pro').read_text()) if (OUT/'house-rules-main-B2.kicad_pro').exists() else {}
 p.update({'meta':{'filename':'house-rules-main-B2.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.11,'min_via_diameter':.45,'min_through_hole_diameter':.3,'min_via_annular_width':.075,'min_copper_edge_clearance':.25,'min_hole_to_hole':.25,'min_hole_clearance':.20,'min_silk_clearance':.1,'min_text_height':.6,'min_text_thickness':.1},'defaults':{'board_outline_line_width':.05,'copper_line_width':.15},'rule_severities':{}}},'net_settings':{'classes':[default,dict(default,name='Power',track_width=.35)],'meta':{'version':4},'netclass_assignments':{},'netclass_patterns':[{'netclass':'Power','pattern':n}for n in ('VBUS','FUSED_VBUS','+5V','VLED_5V','+3V3','SW_3V3','COL1_A','COL2_A','COL3_A','COL4_A','COL5_A')]},'text_variables':{'REV':'B2','PROJECT':'House Rules'}})
 (OUT/'house-rules-main-B2.kicad_pro').write_text(json.dumps(p,indent=2)+'\n')
 (OUT/'house-rules-main-B2.kicad_dru').write_text('(version 1)\n# B2: ordinary 0.30mm drills; 0.60/0.45mm capture pads; no clearance exceptions.\n(rule "Power neck minimum" (condition "A.NetName == \'VBUS\' || A.NetName == \'FUSED_VBUS\' || A.NetName == \'+5V\' || A.NetName == \'+3V3\' || A.NetName == \'VLED_5V\' || A.NetName == \'SW_3V3\' || A.NetName == \'GND\' || A.NetName == \'COL1_A\' || A.NetName == \'COL2_A\' || A.NetName == \'COL3_A\' || A.NetName == \'COL4_A\' || A.NetName == \'COL5_A\'") (constraint track_width (min 0.15mm)))\n')

ap=argparse.ArgumentParser();ap.add_argument('--rebuild-placement',action='store_true');ap.add_argument('--placement',type=Path);a=ap.parse_args()
file=OUT/'house-rules-main-B2.kicad_pcb'
if file.exists() and not a.rebuild_placement:raise SystemExit('Refusing to discard routing without --rebuild-placement')
spec=json.loads((B2/'electrical-spec.json').read_text())
placement=json.loads(a.placement.read_text()) if a.placement else place_spec()
assert set(placement)=={p['ref']for p in spec['parts']}
(B2/'placement.json').write_text(json.dumps(placement,indent=2)+'\n')
layers=spec['boards']['main']['layers'];assert layers in (4,6)
b=k.BOARD();b.SetCopperLayerCount(layers)
ds=b.GetDesignSettings();ds.SetAuxOrigin(pos(0,0));ds.SetGridOrigin(pos(0,0));ds.SetBoardThickness(mm(1.6))
ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.11);ds.m_CopperEdgeClearance=mm(.25);ds.m_ViasMinAnnularWidth=mm(.075);ds.m_ViasMinSize=mm(.45);ds.m_HoleClearance=mm(.20)
nc=ds.m_NetSettings.GetDefaultNetclass();nc.SetClearance(mm(.15));nc.SetTrackWidth(mm(.15));nc.SetViaDiameter(mm(.6));nc.SetViaDrill(mm(.3))
nc.SetDiffPairWidth(mm(.15));nc.SetDiffPairGap(mm(.15))
nc_nodes={}
netxml=B2/'reports/schematic.net.xml'
if netxml.exists():
 for n in ET.parse(netxml).findall('.//nets/net'):
  if n.attrib['name'].startswith('unconnected-'):
   for node in n.findall('node'):nc_nodes[(node.attrib['ref'],node.attrib['pin'])]=n.attrib['name']
nets={}
for n in sorted({n for p in spec['parts']for n in p['pins'].values()if n}|set(nc_nodes.values())):
 ni=k.NETINFO_ITEM(b,n);b.Add(ni);nets[n]=ni
s=k.PCB_SHAPE(b);s.SetShape(k.SHAPE_T_RECT);s.SetStart(pos(0,0));s.SetEnd(pos(88.4,17.3));s.SetLayer(k.Edge_Cuts);s.SetWidth(mm(.05));b.Add(s)
(OUT/'3d').mkdir(exist_ok=True)
shutil.copy2(ROOT/'hardware/kicad/3d/LMD07057AUE-101B.wrl',OUT/'3d/LMD07057AUE-101B.wrl')
for p in spec['parts']:
 lib,name=p['footprint'].split(':');folder=OUT/'footprints'/(lib+'.pretty')
 f=k.FootprintLoad(str(folder if (folder/(name+'.kicad_mod')).exists() else STD/(lib+'.pretty')),name)
 if f is None:raise ValueError('Missing '+p['footprint'])
 f.SetFPID(k.LIB_ID(lib,name));b.Add(f)
 f.SetReference(p['ref']);f.SetValue(p['value']);f.Value().SetVisible(False);f.Reference().SetVisible(False)
 for key,val in [('MPN',p.get('mpn','')),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:
  f.SetField(key,val);f.GetField(key).SetVisible(False)
 side=p.get('side','B')
 if not p['ref'].startswith('DS'):f.Flip(xy(0,0),k.FLIP_DIRECTION_LEFT_RIGHT)
 pp=placement[p['ref']];f.SetOrientationDegrees(pp['angle']);f.SetPosition(pos(pp['x'],pp['y']))
 path=k.KIID_PATH();path.push_back(k.KIID(uid('house-rules:B2:main:sheet')));path.push_back(k.KIID(uid('house-rules:main:'+p['ref'])));f.SetPath(path)
 for pad in f.Pads():
  n=pad.GetNumber()
  if n and n not in p['pins']:raise ValueError(f'{p["ref"]}.{n} missing net spec')
  net=p['pins'].get(n) or nc_nodes.get((p['ref'],n))
  if net:pad.SetNet(nets[net])
 for m in f.Models():
  src=m.m_Filename.replace('${KICAD10_3DMODEL_DIR}','/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
  if Path(src).is_file():
   target=OUT/'3d'/(lib+'__'+Path(src).name);shutil.copy2(src,target);m.m_Filename='${KIPRJMOD}/3d/'+target.name
# Hand-route the exposed pad to its GND lead, then to an ordinary outside via.
# No hole lies in a solderable QFN land. In2.Cu is the near-side ground plane.
for f in list(b.GetFootprints()):
 if f.GetReference() not in ('U1','U2','U3','U4'):continue
 pads={p.GetNumber():p for p in f.Pads() if p.GetNumber()}
 ep=pads['25'].GetPosition();g=pads['22'].GetPosition()
 end=k.VECTOR2I(g.x,g.y+(mm(.85) if g.y>ep.y else -mm(.85)))
 for a0,b0 in ((ep,k.VECTOR2I(g.x,ep.y)),(k.VECTOR2I(g.x,ep.y),g),(g,end)):
  t=k.PCB_TRACK(b);t.SetStart(a0);t.SetEnd(b0);t.SetWidth(mm(.24));t.SetLayer(k.B_Cu);t.SetNet(nets['GND']);t.SetLocked(True);b.Add(t)
 via=k.PCB_VIA(b);via.SetPosition(end);via.SetWidth(mm(.6));via.SetDrill(mm(.3));via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(nets['GND']);via.SetLocked(True);b.Add(via)
if layers==6:
 for f in b.GetFootprints():
  if f.GetReference()not in ('U1','U2','U3','U4'):continue
  ep=next(p for p in f.Pads()if p.GetNumber()=='25');c=ep.GetPosition()
  for x,y in ((-.55,0),(.55,0),(0,.55)):
   v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(c.x+mm(x),c.y+mm(y)));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets['GND']);v.SetLocked(True);b.Add(v)
 for via in b.GetTracks():
  if isinstance(via,k.PCB_VIA):via.SetFillingMode(k.FILLING_MODE_FILLED);via.SetCappingMode(k.CAPPING_MODE_CAPPED)
# Two GND reference planes for the selected six-layer circuit.
ground_layers=(k.In2_Cu,k.In4_Cu)if layers==6 else(k.In2_Cu,)
for ground_layer in ground_layers:
 z=k.ZONE(b);z.SetLayer(ground_layer);z.SetNet(nets['GND']);z.SetLocalClearance(mm(.15));z.SetThermalReliefGap(mm(.25));z.SetThermalReliefSpokeWidth(mm(.25));poly=z.Outline();poly.NewOutline()
 for x,y in ((.3,.3),(88.1,.3),(88.1,17.0),(.3,17.0)):poly.Append(mm(x+50),mm(y+50))
 b.Add(z)
t=k.PCB_TEXT(b);t.SetText('HOUSE RULES B2');t.SetPosition(pos(16.0,16.4));t.SetLayer(k.B_SilkS);t.SetMirrored(True);t.SetTextSize(xy(.6,.6));t.SetTextThickness(mm(.1));b.Add(t)
b.BuildConnectivity();k.SaveBoard(str(file),b);project()
dsn=OUT/'house-rules-main-B2.dsn';assert k.ExportSpecctraDSN(b,str(dsn))
s=dsn.read_text();s=re.sub(r'\(clearance [0-9.]+ \(type smd_smd\)\)','(clearance 150 (type smd_smd))',s)
for layer in ground_layers:
 layer_name=k.LayerName(layer);s=s.replace(f'(layer {layer_name}\n      (type signal)',f'(layer {layer_name}\n      (type power)')
# Exported runtime board settings do not inherit the JSON Power-class patterns.
start=s.index('    (class kicad_default ');end=s.index('      (circuit',start)
head=s[start:end]
for n in ('VBUS','FUSED_VBUS','+5V','VLED_5V','+3V3','SW_3V3','COL1_A','COL2_A','COL3_A','COL4_A','COL5_A'):head=re.sub(r'(?<![^\s])'+re.escape(n)+r'(?=\s)', '', head)
s=s[:start]+head+s[end:]
point=s.index('\n  (wiring');close=s.rfind('\n  )',0,point)
s=s[:close]+f'\n    (class Power VBUS FUSED_VBUS +5V VLED_5V +3V3 SW_3V3 COL1_A COL2_A COL3_A COL4_A COL5_A (circuit (use_via "Via[0-{layers-1}]_600:300_um")) (rule (width 350) (clearance 150)))'+s[close:]
dsn.write_text(s)
print(file)
print(len(spec['parts']),'footprints',len(nets),'nets;',layers,'layers; ordinary 0.30mm drills; manual routing/DRC still required')
