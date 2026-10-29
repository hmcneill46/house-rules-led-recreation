#!/usr/bin/env python3
"""Build/verify only B2 schematic; reuse pure symbol helpers, never A1 main()."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

DEST = Path(__file__).resolve().parents[1]
ROOT = DEST.parents[2]
CLI = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
helper_spec = importlib.util.spec_from_file_location('a1_pure_schematic_helpers', ROOT/'hardware/tools/build_schematics.py')
h = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(h)

def build(spec):
    target = DEST/'kicad'; target.mkdir(exist_ok=True)
    parts = spec['parts']; stem = 'house-rules-main-B2'; sheet = h.uid('house-rules:B2:main:sheet')
    rows = [
        ('BANK1 / DS1 + DS2', ['U1','DS1','DS2','R1','C1']),
        ('BANK2 / DS3 + DS4', ['U2','DS3','DS4','R2','C2']),
        ('BANK3 / DS5 + DS6', ['U3','DS5','DS6','R3','C3']),
        ('BANK4 / DS7 and gate sinks / USB INPUT SOFT START', ['U4','DS7','R4','C4','U8','C13','C14']),
        ('COLUMN1..3 / gate pullups and anode discharge', ['Q1','R5','R10','Q2','R6','R11','Q3','R7','R12']),
        ('COLUMN4..5 / gate pullups and anode discharge', ['Q4','R8','R13','Q5','R9','R14','R15','R16']),
        ('RAIL SWITCHES / common EN / quick discharge', ['U5','U6','C5','C6','C7','C8','C9','C10']),
        ('USB / CC current sensing and ESD', ['U7','F1','D1','R17','R18','R19','R20','C11','C12']),
        ('BC1.2 / automatic USB switch / GOOD_BAT uses always3V3', ['U9','C15','C16','R21','R22','R23']),
        ('MCU WIRES J1..J10 / external XIAO RP2040 Plus', [f'J{i}' for i in range(1,11)]),
        ('MCU DATA / BC STATUS + USB BREAKOUT WIRES / do not power both USB sockets', ['J11','J12']+[f'J{i}' for i in range(13,21)])
    ]
    positions = {ref:(66.04+110.49*c,72.39+60.96*r) for r,(_,refs) in enumerate(rows) for c,ref in enumerate(refs)}
    assert len(positions) == len(parts), 'Every component must occur exactly once in schematic layout'
    s=[f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0") (uuid {h.q(sheet)}) (paper "A0")',
       '(title_block (title "House Rules B2 / LED carrier, power and interface") (date "2026-10-29") (rev "B2") (company "House Rules recreation") (comment 1 "ENGINEERING PROTOTYPE / no manufacture release"))',
       '(lib_symbols', '\n'.join(h.symbol(p)[0] for p in parts),h.flag_symbol('main'),')']
    for p in parts: s.extend(h.instance(p,*positions[p['ref']],sheet,stem))
    for r,(title,_) in enumerate(rows): s.append(h.drawing_text(title,12.7,40.64+60.96*r,2.3))
    notes = [
        'Named labels connect matching nodes. Every package pin is explicit; crosses mark intentional no-connects. Owner-supplied LEDs and wire pads are excluded from factory assembly.',
        'IREF=6.8k: 7.42493mA nominal per LED. U4 OUT7..11 sink PMOS gates, exactly one selected column. BLANK HIGH disables every LED and gate sink.',
        '400Hz frame / 5x500us phases / >=30us BLANK before next phase / <=470us full on. LAT LOW while shifting, pulse HIGH then LOW while blanked.',
        'USB-C 5V only, no PD. Adafruit4090 supplies separate5.1k Rd resistors; no duplicate Rd on this board. CC divider loading checked against tolerance.',
        'Both TPS22918 switches default OFF. BLANK pullup uses SW_3V3. Park serial controls LOW and BLANK high-Z before disabling rails to prevent backfeed.',
        'TPD4E05U06 opposite NC pads are joined by external copper to corresponding DC nets. Do not treat the IC as internally flow-through.',
        'BQ24392 isolates raw USB_DP/DM from USB_DP_HOST/DM_HOST. GOOD_BAT always3V3; BC full grant requires DET HIGH and AL_N LOW; host suspend always overrides.',
        'One owned LED fully diode-verified; check other20. Fit/current/inrush/suspend, 30us deadtime and temperature need bench tests. In2: CT_5V<=12mm only; In4: pure GND.'
    ]
    for i,t in enumerate(notes): s.append(h.drawing_text(t,12.7,754.38+5.08*i,1.8))
    fy=797.56
    for i,net in enumerate(['VBUS','FUSED_VBUS','+3V3','GND']):
        x=40.64+45.72*i;ref=f'#FLG0{i+1}';pid=h.uid('B2:'+ref)
        s.append(f'(symbol (lib_id "HouseRules_main:PowerFlag") (at {h.f(x)} {h.f(fy)} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {h.q(pid)}) {h.prop("Reference",ref,x,fy,hide=True)} {h.prop("Value","PWR_FLAG",x,fy-3.81,hide=True)} (pin "1" (uuid {h.q(h.uid(pid+":pin:1"))})) (instances (project {h.q(stem)} (path {h.q("/"+sheet)} (reference {h.q(ref)}) (unit 1)))))')
        s.append(f'(wire (pts (xy {h.f(x)} {h.f(fy)}) (xy {h.f(x)} {h.f(fy+2.54)})) (stroke (width 0) (type default)) (uuid {h.q(h.uid(pid+":wire"))}))')
        s.append(f'(global_label {h.q(net)} (shape passive) (at {h.f(x)} {h.f(fy+2.54)} 0) {h.effects(1.05,"left bottom")} (uuid {h.q(h.uid(pid+":label"))}))')
    s.append('(embedded_fonts no))')
    path=target/(stem+'.kicad_sch'); path.write_text('\n'.join(s)+'\n')
    (target/'HouseRules_main.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n'+'\n'.join(h.symbol(p,True)[0] for p in parts)+h.flag_symbol('main',True)+'\n)\n')
    (target/'sym-lib-table').write_text('(sym_lib_table (version 7)\n(lib (name "HouseRules_main")(type "KiCad")(uri "${KIPRJMOD}/HouseRules_main.kicad_sym")(options "")(descr "B2 explicit package symbols")))\n')
    # A named project enables KiCad CLI to resolve local tables. Do not replace
    # layout design rules if another tool has already created this project.
    project=target/(stem+'.kicad_pro')
    if not project.exists():project.write_text(json.dumps({'meta':{'version':1},'erc':{'erc_exclusions':[],'meta':{'version':0},'pin_map':[],'rule_severities':{}}},indent=2)+'\n')
    standard=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
    libs=set()
    for p in parts:
        lib,name=p['footprint'].split(':'); libs.add(lib)
        folder=target/'footprints'/(lib+'.pretty');folder.mkdir(parents=True,exist_ok=True)
        output=folder/(name+'.kicad_mod')
        if lib=='HouseRules' and name=='WirePad_B2':
            output.write_text('(footprint "WirePad_B2" (version 20240108) (generator "pcbnew") (layer "F.Cu") (attr smd) (fp_text reference "REF**" (at 0 -1.3) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.12)))) (fp_text value "OWNER_WIRE" (at 0 1.3) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.12)))) (pad "1" smd roundrect (at 0 0) (size 1.8 1.1) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2)))\n')
        elif lib=='HouseRules':shutil.copyfile(ROOT/'hardware/kicad/HouseRules.pretty'/(name+'.kicad_mod'),output)
        elif lib=='TI':
            if not output.exists():raise FileNotFoundError(f'Root-owned B2 TI land pattern not created yet: {output}')
        else:shutil.copyfile(standard/(lib+'.pretty')/(name+'.kicad_mod'),output)
    (target/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(f'(lib (name "{lib}")(type "KiCad")(uri "${{KIPRJMOD}}/footprints/{lib}.pretty")(options "")(descr "B2 KiCad footprint"))\n' for lib in sorted(libs))+')\n')
    return path

def verify(spec,path):
    reports=DEST/'reports';reports.mkdir(exist_ok=True)
    erc=reports/'schematic.erc.json';net=reports/'schematic.net.xml'
    r=subprocess.run([str(CLI),'sch','erc','--format','json','--severity-all','--output',str(erc),'--exit-code-violations',str(path)],capture_output=True,text=True)
    print(r.stdout,r.stderr)
    data=json.loads(erc.read_text()); violations=[v for sh in data.get('sheets',[]) for v in sh.get('violations',[])]
    for v in violations[:8]: print(json.dumps(v))
    subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','--output',str(net),str(path)],check=True,capture_output=True,text=True)
    actual={(p.attrib['ref'],p.attrib['pin']):n.attrib['name'].lstrip('/') for n in ET.parse(net).findall('./nets/net') for p in n.findall('node') if not p.attrib['ref'].startswith('#')}
    expected={(p['ref'],pn):nn for p in spec['parts'] for pn,nn in p['pins'].items() if nn is not None}
    missing={str(k):v for k,v in expected.items() if actual.get(k)!=v}
    extra={str(k):v for k,v in actual.items() if k not in expected and not v.startswith('unconnected-')}
    summary={'revision':'B2','spec_sha256':hashlib.sha256((DEST/'electrical-spec.json').read_bytes()).hexdigest(),
             'component_count':len(spec['parts']),'connected_pin_count':len(expected),'netlist_matches_spec':not(missing or extra),
             'missing':missing,'extra':extra,'erc_exit_code':r.returncode,'erc_violation_count':len(violations),'erc_exclusions':False}
    (reports/'schematic-verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    if r.returncode or missing or extra:raise SystemExit('B2 schematic verification failed; inspect reports')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    spec=json.loads((DEST/'electrical-spec.json').read_text());path=build(spec)
    print(path)
    if args.verify:verify(spec,path)
