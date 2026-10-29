#!/usr/bin/env python3
"""Build editable KiCad PCB placement from circuit-spec.json.

Run with KiCad's bundled Python. Routing is subsequently imported from Specctra
and checked by native KiCad DRC; regeneration deliberately recreates placement.
"""
import json
import argparse
import math
import re
import shutil
import uuid
from xml.etree import ElementTree as ET
from pathlib import Path
import wx
import pcbnew as k

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/kicad'
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
ORIGIN=(50,50)
app=wx.App(False)

def mm(v): return k.FromMM(v)
def xy(x,y): return k.VECTOR2I(mm(x),mm(y))
def pos(x,y): return xy(x+ORIGIN[0],y+ORIGIN[1])

def line(parent,a,b,layer,width=.12):
    s=k.PCB_SHAPE(parent);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*b));s.SetLayer(layer);s.SetWidth(mm(width));parent.Add(s)
    return s

def text(board,value,x,y,layer=k.B_SilkS,size=.65):
    t=k.PCB_TEXT(board);t.SetText(value);t.SetPosition(pos(x,y));t.SetTextSize(xy(size,size));t.SetTextThickness(mm(.12));t.SetLayer(layer)
    if layer==k.B_SilkS:t.SetMirrored(True)
    board.Add(t)
    return t

def led_footprint():
    f=k.FOOTPRINT(None); f.SetFPID(k.LIB_ID('HouseRules','LMD07057AUE-101B'))
    f.SetAttributes(k.FP_THROUGH_HOLE)
    for side in [-1,1]:
        for i in range(6):
            number=i+1 if side<0 else 12-i
            p=k.PAD(f);p.SetNumber(str(number));p.SetAttribute(k.PAD_ATTRIB_PTH)
            p.SetShape(k.PAD_SHAPE_RECT if number==1 else k.PAD_SHAPE_CIRCLE)
            p.SetSize(xy(1.4,1.4));p.SetDrillSize(xy(.9,.9));p.SetLayerSet(k.LSET.AllCuMask())
            layers=p.GetLayerSet();layers.AddLayer(k.F_Mask);layers.AddLayer(k.B_Mask);p.SetLayerSet(layers)
            p.SetPosition(xy(side*3.81,-6.35+2.54*i));f.Add(p)
    for a,b in [((-6.35,-8.9),(6.35,-8.9)),((6.35,-8.9),(6.35,8.9)),((6.35,8.9),(-6.35,8.9)),((-6.35,8.9),(-6.35,-8.9))]:
        line(f,a,b,k.F_Fab,.1)
        line(f,a,b,k.F_CrtYd,.05)
    # Pin-1 marker is inside the LED footprint and remains visible before fitting.
    line(f,(-3.81,-7.8),(-3.3,-7.8),k.F_SilkS)
    model=k.FP_3DMODEL();model.m_Filename='${KIPRJMOD}/3d/LMD07057AUE-101B.wrl'
    f.Models().push_back(model)
    return f

def model_wrl():
    """Simple measured-envelope LED model, pins trimmed to 1 mm below PCB.

    VRML model coordinates are in KiCad's historical 0.1-inch units.
    """
    s=['#VRML V2.0 utf8']
    def box(center,size,color):
        a=' '.join(str(v/2.54) for v in center);b=' '.join(str(v/2.54) for v in size)
        s.append(f'Transform {{ translation {a} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} geometry Box {{ size {b} }} }} ] }}')
    def cylinder(x,y,z,r,h,color):
        # Explicit triangles keep the round dots and leads visible to KiCad's
        # VRML importer; Cylinder primitives were omitted by the native render.
        n=24
        points=[]
        for dz in [-h/2,h/2]:
            for i in range(n):
                a=2*math.pi*i/n
                points.append(((x+r*math.cos(a))/2.54,
                               (y+r*math.sin(a))/2.54,(z+dz)/2.54))
        points.extend([(x/2.54,y/2.54,(z-h/2)/2.54),
                       (x/2.54,y/2.54,(z+h/2)/2.54)])
        faces=[]
        for i in range(n):
            j=(i+1)%n
            faces.extend([(i,j,j+n),(i,j+n,i+n),
                          (j,i,2*n),(i+n,j+n,2*n+1)])
        coords=', '.join(' '.join(f'{v:.9f}' for v in p) for p in points)
        indices=', '.join(' '.join(str(v) for v in f)+ ' -1' for f in faces)
        s.append('Shape { appearance Appearance { material Material { '
                 f'diffuseColor {color} }} }} geometry IndexedFaceSet {{ '
                 f'coord Coordinate {{ point [ {coords} ] }} '
                 f'coordIndex [ {indices} ] solid TRUE creaseAngle 0.5 }} }}')
    box((0,0,6.15),(12.7,17.8,6.3),'0.82 0.8 0.72')
    box((0,0,9.305),(12.68,17.78,.05),'0.015 0.015 0.018')
    for c in range(5):
        for r in range(7):cylinder(-5.08+c*2.54,7.62-r*2.54,9.345,.95,.04,'0.8 0.8 0.76')
    for x in [-3.81,3.81]:
        for i in range(6):cylinder(x,6.35-i*2.54,.2,.25,5.6,'0.55 0.57 0.59')
    (OUT/'3d').mkdir(exist_ok=True)
    (OUT/'3d/LMD07057AUE-101B.wrl').write_text('\n'.join(s)+'\n')

def make_project(name):
    # 0.15 mm inter-net clearance; 0.10 mm minimum fanout, 0.15 mm default traces.
    default={'bus_width':12,'clearance':.15,'diff_pair_gap':.15,'diff_pair_via_gap':.25,'diff_pair_width':.15,
             'line_style':0,'microvia_diameter':.3,'microvia_drill':.1,'name':'Default','pcb_color':'rgba(0, 0, 0, 0.000)',
             'schematic_color':'rgba(0, 0, 0, 0.000)','track_width':.15,'via_diameter':.4,'via_drill':.2,'wire_width':6}
    project={'meta':{'filename':name+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{
        'min_clearance':(.1 if name=='house-rules-main' else .15),'min_track_width':.1,'min_via_diameter':.4,'min_through_hole_diameter':.2,
        'min_via_annular_width':.1,'min_copper_edge_clearance':.25,'min_hole_to_hole':.25,
        'min_hole_clearance':.15,'min_silk_clearance':.1,'min_text_height':.6,'min_text_thickness':.1},
        'defaults':{'board_outline_line_width':.05,'copper_line_width':.15},'rule_severities':{}}},
        'net_settings':{'classes':[default,dict(default,name='Power',track_width=.35)],'meta':{'version':4},'netclass_assignments':{},'netclass_patterns':[{'netclass':'Power','pattern':'+5V'},{'netclass':'Power','pattern':'VBUS'}]},
        'text_variables':{'REV':'A1','PROJECT':'House Rules'}}
    (OUT/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
    rules = '(version 1)\n(rule \"Power trunk width\" (condition \"A.Type == \'Track\' && (A.NetName == \'+5V\' || A.NetName == \'VBUS\')\") (constraint track_width (min 0.15mm)))\n'
    if name=='house-rules-main':
        groups=' || '.join(f"(A.intersectsCourtyard('{ref}') && B.intersectsCourtyard('{ref}'))" for ref in ['U1','U2','U3','U4'])
        condition="((A.Type == 'Via' && B.Type == 'Pad') || (A.Type == 'Pad' && B.Type == 'Via')) && ("+groups+")"
        rules += '\n# Only same-QFN courtyard via-to-pad pairs use the 0.10 mm fabrication allowance.\n'
        rules += f'(rule \"QFN local via-pad 100um\" (condition \"{condition}\") (constraint clearance (min 0.10mm)))\n'
    (OUT/(name+'.kicad_dru')).write_text(rules)

def build(board_key,spec):
    info=spec['boards'][board_key];name='house-rules-'+board_key
    b=k.BOARD();b.SetCopperLayerCount(info['layers'])
    s=b.GetDesignSettings();s.SetAuxOrigin(pos(0,0));s.SetGridOrigin(pos(0,0))
    s.m_MinClearance=mm(.1 if board_key=='main' else .15);s.m_TrackMinWidth=mm(.1);s.m_CopperEdgeClearance=mm(.25)
    s.m_ViasMinAnnularWidth=mm(.1);s.m_ViasMinSize=mm(.4);s.m_HoleClearance=mm(.15)
    nc=s.m_NetSettings.GetDefaultNetclass();nc.SetClearance(mm(.15));nc.SetTrackWidth(mm(.15));nc.SetViaDiameter(mm(.4));nc.SetViaDrill(mm(.2))
    nc.SetDiffPairWidth(mm(.15));nc.SetDiffPairGap(mm(.15))
    s.SetBoardThickness(mm(info['thickness']))
    nc_nodes={}
    xmlpath=ROOT/f'hardware/reports/schematic-verification-{board_key}.net.xml'
    if xmlpath.exists():
        for netnode in ET.parse(xmlpath).findall('.//nets/net'):
            if netnode.attrib['name'].startswith('unconnected-'):
                for node in netnode.findall('node'):nc_nodes[(node.attrib['ref'],node.attrib['pin'])]=netnode.attrib['name']
    nets={}
    netnames={n for p in spec['parts'] if p['board']==board_key for n in p['pins'].values() if n}|set(nc_nodes.values())
    for net in sorted(netnames):
        ni=k.NETINFO_ITEM(b,net);b.Add(ni);nets[net]=ni
    rect=k.PCB_SHAPE(b);rect.SetShape(k.SHAPE_T_RECT);rect.SetStart(pos(0,0));rect.SetEnd(pos(info['width'],info['height']));rect.SetLayer(k.Edge_Cuts);rect.SetWidth(mm(.05));b.Add(rect)
    ids={}
    for p in [p for p in spec['parts'] if p['board']==board_key]:
        if p['footprint'].startswith('HouseRules:'):
            f=led_footprint()
        else:
            lib,fp=p['footprint'].split(':');f=k.FootprintLoad(str(LIB/(lib+'.pretty')),fp)
            if f is None:raise ValueError(p['footprint'])
            f.SetFPID(k.LIB_ID(lib,fp))
            for model in f.Models():
                source=model.m_Filename.replace('${KICAD10_3DMODEL_DIR}','/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
                if Path(source).is_file():
                    target=OUT/'3d'/(lib+'__'+Path(source).name)
                    shutil.copy2(source,target);model.m_Filename='${KIPRJMOD}/3d/'+target.name
            vend=OUT/'footprints'/(lib+'.pretty');vend.mkdir(parents=True,exist_ok=True)
            k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(vend),f)
        b.Add(f)
        f.SetReference(p['ref']);f.SetValue(p['value']);f.Value().SetVisible(False)
        for key,value in [('MPN',p['mpn']),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:
            f.SetField(key,value);f.GetField(key).SetVisible(False)
        f.SetOrientationDegrees(p['angle'])
        if p['side']=='B':f.Flip(xy(0,0),k.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pos(p['x'],p['y']));f.Reference().SetTextSize(xy(.6,.6));f.Reference().SetTextThickness(mm(.1))
        # Position references in free board-edge strips, reviewed after rendering.
        f.Reference().SetVisible(False)
        uid=uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:'+board_key+':'+p['ref'])
        rootuid=uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:'+board_key+':sheet')
        path=k.KIID_PATH();path.push_back(k.KIID(str(rootuid)));path.push_back(k.KIID(str(uid)));f.SetPath(path)
        for pad in f.Pads():
            n=pad.GetNumber()
            if n and n not in p['pins']:raise ValueError(f"Missing {p['ref']}.{n} in circuit spec")
            if n and p['pins'].get(n):pad.SetNet(nets[p['pins'][n]])
            elif (p['ref'],n) in nc_nodes:pad.SetNet(nets[nc_nodes[(p['ref'],n)]])
        ids[p['ref']]=f
    # Explicit reference and polarity legend; no text is hidden underneath a solder pad.
    if board_key=='main':
        for i in range(7):text(b,'DS'+str(i+1),6.1+12.7*i,1.0,k.F_SilkS,.65)
        for i,x in enumerate([6.1,31.5,56.9,82.3],1):text(b,'U'+str(i),x,11.55,size=.6)
        text(b,'HOUSE RULES A1',52.0,16.2,size=.65)
        text(b,'BOOT',12.45,2.1,size=.6);text(b,'RESET',12.45,15.2,size=.6)
        text(b,'USB',69.6,3.1,size=.65)
        for i,label in enumerate(['G','V','D','C','R']):text(b,label,64.6,3.0+i*2.54,size=.6)
    else:
        text(b,'USB 5V',10,1.0,k.B_SilkS,.8);text(b,'A1',8,13.0,k.B_SilkS,.65)
        text(b,'1:5V 2:D- 3:D+',8,3.0,k.B_SilkS,.65)
        text(b,'4:G 5:C1 6:C2',8,4.5,k.B_SilkS,.65)
    def track(net,points,layer,width=.15):
        for a,c in zip(points,points[1:]):
            t=k.PCB_TRACK(b);t.SetStart(pos(*a));t.SetEnd(pos(*c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
    def via(net,x,y,diameter=.4,drill=.2):
        v=k.PCB_VIA(b);v.SetPosition(pos(x,y));v.SetWidth(mm(diameter));v.SetDrill(mm(drill));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[net]);v.SetLocked(True);b.Add(v)
        if board_key=='main':
            v.SetFillingMode(k.FILLING_MODE_FILLED);v.SetCappingMode(k.CAPPING_MODE_CAPPED)
    # Hand-routed, locked USB data paths. The main pair runs on F.Cu over In1 GND.
    # Brief connector fanout stubs are B.Cu; all dimensions are audited after routing.
    if board_key=='main':
        track('USB_DM',[(44.95,6.2125),(44.95,5.65),(44.55,5.25)],k.B_Cu)
        track('USB_DP',[(45.45,6.2125),(45.45,5.25),(45.2,5.0)],k.B_Cu)
        for net,x,y in [('USB_DM',44.55,5.25),('USB_DP',45.2,5.0),('USB_DM',71.8,10.7),('USB_DP',71.15,11.7)]:via(net,x,y)
        # Upper margin avoids the driver's fanout and stays over In1 GND.
        track('USB_DM',[(44.55,5.25),(44.55,.8),(68.75,.8),(71.8,3.85),(71.8,10.7)],k.F_Cu)
        track('USB_DP',[(45.2,5.0),(45.2,1.15),(68.6,1.15),(71.15,3.7),(71.15,11.7)],k.F_Cu)
        track('USB_DM',[(71.8,10.7),(70.325,10.7)],k.B_Cu)
        track('USB_DP',[(71.15,11.7),(70.325,11.7)],k.B_Cu)
    else:
        # Explicit copper across the ESD's otherwise unbonded NC pads.
        for net,x in [('USB_DM',9.0),('USB_DP',8.5),('GND',8.0),('CC1',7.5),('CC2',7.0)]:
            track(net,[(x,7.2125),(x,7.9875)],k.F_Cu)
        track('USB_DM',[(5.1,3.5),(6.0,3.5),(9.0,6.5),(9.0,7.2125)],k.F_Cu)
        track('USB_DP',[(5.1,4.5),(6.0,4.5),(8.5,7.0),(8.5,7.2125)],k.F_Cu)
        track('USB_DP',[(8.5,7.9875),(8.5,8.8),(8.85,9.15),(10.45,9.15),(10.45,10.025)],k.F_Cu)
        track('USB_DP',[(10.45,9.15),(11.45,9.15),(11.45,10.025)],k.F_Cu)
        track('USB_DM',[(9.0,7.9875),(9.9875,7.9875),(10.3,8.3)],k.F_Cu)
        for x,y in [(10.3,8.3),(9.95,11.2),(10.95,11.2)]:via('USB_DM',x,y)
        track('USB_DM',[(9.95,10.025),(9.95,11.2)],k.F_Cu)
        track('USB_DM',[(10.95,10.025),(10.95,11.2)],k.F_Cu)
        track('USB_DM',[(9.95,11.2),(10.95,11.2),(10.95,8.95),(10.3,8.3)],k.B_Cu)
        track('GND',[(8.0,7.9875),(8.0,8.6)],k.F_Cu);via('GND',8.0,8.6)
    # Ground planes give thermal paths and USB reference copper. All ground pads
    # receive vias in the post-routing step; do not rely on modelled body contact.
    for layer in [k.In1_Cu]:
        z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets['GND']);z.SetLocalClearance(mm(.2));z.SetThermalReliefGap(mm(.25));z.SetThermalReliefSpokeWidth(mm(.25))
        poly=z.Outline();poly.NewOutline()
        for x,y in [(.3,.3),(info['width']-.3,.3),(info['width']-.3,info['height']-.3),(.3,info['height']-.3)]:poly.Append(mm(x+50),mm(y+50))
        b.Add(z)
    b.BuildConnectivity();k.SaveBoard(str(OUT/(name+'.kicad_pcb')),b)
    make_project(name)
    dsn=OUT/(name+'.dsn')
    if not k.ExportSpecctraDSN(b,str(dsn)):raise RuntimeError('DSN export failed')
    # KiCad's exporter inserts a special 0.05 mm SMD rule. Retain the real
    # project clearance rather than letting the router use that loose override.
    content=re.sub(r'\(clearance [0-9.]+ \(type smd_smd\)\)','(clearance 150 (type smd_smd))',dsn.read_text())
    # Give VBUS and +5V real trunk width, retaining automatic pad neck-down.
    start=content.index('    (class kicad_default ');end=content.index('      (circuit',start)
    head=content[start:end].replace(' +5V ',' ').replace(' VBUS\n','\n').replace(' VBUS ',' ')
    content=content[:start]+head+content[end:]
    point=content.index('\n  (wiring')
    # Insert before the network's closing parenthesis (immediately before wiring).
    close=content.rfind('\n  )',0,point)
    powernets=' '.join(n for n in ['+5V','VBUS'] if n in nets)
    via_name=f'Via[0-{info["layers"]-1}]_400:200_um'
    content=content[:close]+f'\n    (class Power {powernets} (circuit (use_via "{via_name}")) (rule (width 350) (clearance 150)))'+content[close:]
    dsn.write_text(content)
    print(name,len(ids),'footprints',len(nets),'nets')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--board',choices=['main','usb']);args=parser.parse_args()
    spec=json.loads((OUT/'circuit-spec.json').read_text());model_wrl()
    (OUT/'HouseRules.pretty').mkdir(exist_ok=True)
    k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(OUT/'HouseRules.pretty'),led_footprint())
    for key in spec['boards']:
        if not args.board or args.board==key:build(key,spec)
    libs=sorted({p['footprint'].split(':')[0] for p in spec['parts'] if not p['footprint'].startswith('HouseRules:')})
    rows=['(fp_lib_table (version 7)','(lib (name "HouseRules")(type "KiCad")(uri "${KIPRJMOD}/HouseRules.pretty")(options "")(descr "Matrix lattice"))']
    rows += [f'(lib (name "{lib}")(type "KiCad")(uri "${{KIPRJMOD}}/footprints/{lib}.pretty")(options "")(descr "Vendored KiCad10 footprint"))' for lib in libs]
    (OUT/'fp-lib-table').write_text('\n'.join(rows)+')\n')

if __name__=='__main__':main()
