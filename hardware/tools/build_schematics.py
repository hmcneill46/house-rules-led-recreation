#!/usr/bin/env python3
"""Create complete, editable KiCad schematics from the shared circuit specification.

Symbols have independent, explicit package pin definitions. No global ERC rules
are disabled. Power flags declare externally supplied rails and the rail after
the passive input fuse; the regulator itself drives +3V3.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "hardware/kicad"
CLI = Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
GRID = 1.27


def uid(text: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, text))


def q(value) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def f(value) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".") or "0"


def effects(size=1.0, justify="", hide=False):
    return f'(effects (font (size {f(size)} {f(size)})){f" (justify {justify})" if justify else ""}{" (hide yes)" if hide else ""})'


def prop(name, value, x=0, y=0, size=1.0, hide=False):
    return f'(property {q(name)} {q(value)} (at {f(x)} {f(y)} 0) {effects(size,hide=hide)})'


def pin_key(pin):
    return (0, int(pin)) if pin.isdigit() else (1, pin)


def pin_layout(part):
    """Return pin, name, type, local endpoint x/y, angle; local y is up."""
    pins = sorted(part["pins"], key=pin_key)
    if len(pins) == 1:
        return [(pins[0], part.get("pin_names", {}).get(pins[0], pins[0]),
                 part.get("types", {}).get(pins[0], "passive"), -5.08, 0.0, 0)]
    if len(pins) == 2:
        return [(p,part.get("pin_names",{}).get(p,p),part.get("types",{}).get(p,"passive"),
                 -7.62 if i==0 else 7.62,0.0,0 if i==0 else 180)
                for i,p in enumerate(pins)]
    split=(len(pins)+1)//2
    result=[]
    for side, group in enumerate([pins[:split],pins[split:]]):
        for i,p in enumerate(group):
            y=((len(group)-1)/2-i)*2.54
            result.append((p,part.get("pin_names",{}).get(p,p),part.get("types",{}).get(p,"passive"),
                           -22.86 if side==0 else 22.86,y,0 if side==0 else 180))
    return result


def symbol(part, library=False):
    ref=part["ref"]
    board=part["board"]
    name=ref if library else f"HouseRules_{board}:{ref}"
    pins=pin_layout(part)
    n=len(pins)
    height=max([abs(p[4]) for p in pins]+[0])+2.54
    width=17.78 if n>2 else 2.54
    prefix=re.match(r"[A-Z]+",ref).group(0)
    bom='no' if part['ref'].startswith('TP') else 'yes'
    s=[f'(symbol {q(name)} (pin_names (offset 0.762)) (exclude_from_sim no) (in_bom {bom}) (on_board yes)',
       prop("Reference",prefix,0,height+5.08),prop("Value",part["value"],0,height+2.54),
       prop("Footprint",part["footprint"],hide=True),prop("Datasheet",part.get("datasheet", ""),hide=True),
       prop("Description",part.get("role", ""),hide=True),
       f'(symbol {q(ref+"_0_1")}']
    if n==2 and ref.startswith('C'):
        for x in [-0.635,0.635]:
            s.append(f'(polyline (pts (xy {x} -2.54) (xy {x} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))')
        for x1,x2 in [(-2.54,-0.635),(0.635,2.54)]:
            s.append(f'(polyline (pts (xy {x1} 0) (xy {x2} 0)) (stroke (width 0.254) (type default)) (fill (type none)))')
    elif n==1:
        s.append('(circle (center 0 0) (radius 1.016) (stroke (width 0.254) (type default)) (fill (type none)))')
    else:
        s.append(f'(rectangle (start {-width} {height}) (end {width} {-height}) (stroke (width 0.254) (type default)) (fill (type background)))')
    s.append(')')
    s.append(f'(symbol {q(ref+"_1_1")}')
    for pin,name,typ,x,y,angle in pins:
        length=5.08 if n!=1 else 4.064
        s.append(f'(pin {typ} line (at {f(x)} {f(y)} {angle}) (length {f(length)}) (name {q(name)} {effects(.9)}) (number {q(pin)} {effects(.8)}))')
    s.extend([')',')'])
    return '\n'.join(s),height


def flag_symbol(board,library=False):
    name="PowerFlag" if library else f"HouseRules_{board}:PowerFlag"
    return f'''(symbol {q(name)} (power) (pin_numbers hide) (pin_names (offset 0) hide)
      (in_bom no) (on_board no)
      {prop("Reference","#FLG",hide=True)} {prop("Value","PWR_FLAG",hide=True)}
      (symbol "PowerFlag_0_1" (polyline (pts (xy -1.27 1.27) (xy 0 2.54) (xy 1.27 1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "PowerFlag_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" {effects(.9)}) (number "1" {effects(.8)}))))'''


def drawing_text(text,x,y,size=2.0):
    return f'(text {q(text)} (at {f(x)} {f(y)} 0) {effects(size,"left")} (uuid {q(uid("text:"+str(x)+":"+str(y)+":"+text))}))'


def instance(part,x,y,sheet_uuid,stem):
    board,ref=part['board'],part['ref']
    pid=uid('house-rules:'+board+':'+ref)
    _,height=symbol(part)
    bom='no' if ref.startswith('TP') else 'yes'
    s=[f'(symbol (lib_id {q("HouseRules_"+board+":"+ref)}) (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom {bom}) (on_board yes) (dnp no) (uuid {q(pid)})',
       prop('Reference',ref,x,y-height-5.08,1.5),prop('Value',part['value'],x,y-height-2.54,1.1),
       prop('Footprint',part['footprint'],x,y,hide=True),prop('Datasheet',part.get('datasheet',''),x,y,hide=True),
       prop('MPN',part.get('mpn',''),x,y,hide=True),prop('LCSC',part.get('lcsc',''),x,y,hide=True),
       prop('Description',part.get('role',''),x,y,hide=True)]
    for pin,*_ in pin_layout(part):
        s.append(f'(pin {q(pin)} (uuid {q(uid(pid+":pin:"+pin))}))')
    s.append(f'(instances (project {q(stem)} (path {q("/"+sheet_uuid)} (reference {q(ref)}) (unit 1)))))')
    objects=['\n'.join(s)]
    for pin,name,typ,px,py,angle in pin_layout(part):
        xx,yy=x+px,y-py
        net=part['pins'][pin]
        if net is None:
            objects.append(f'(no_connect (at {f(xx)} {f(yy)}) (uuid {q(uid(pid+":nc:"+pin))}))')
        else:
            end=xx+(-17.78 if px<0 else 17.78)
            objects.append(f'(wire (pts (xy {f(xx)} {f(yy)}) (xy {f(end)} {f(yy)})) (stroke (width 0) (type default)) (uuid {q(uid(pid+":wire:"+pin))}))')
            # Labels face inward over their own wire stubs, away from neighbours.
            la=0 if px<0 else 180
            objects.append(f'(global_label {q(net)} (shape passive) (at {f(end)} {f(yy)} {la}) {effects(1.05,"left bottom")} (uuid {q(uid(pid+":label:"+pin))}))')
    return objects


def make_board(board,parts,revision):
    stem='house-rules-'+board
    sheet=uid('house-rules:'+board+':sheet')
    library='HouseRules_'+board
    if board=='main':
        rows=[['U1','DS1','DS2','R1','C1','C2'],['U2','DS3','DS4','R2','C3','C4'],
              ['U3','DS5','DS6','R3','C5','C6'],['U4','DS7','R4','C7','C8','TP6'],
              ['U5','C11','C12','R8','R9','SW1','SW2'],['U6','F1','C9','C10','C13','J1'],
              ['R5','R6','R7','R10','R11','R12','R13'],['TP1','TP2','TP3','TP4','TP5']]
        titles=['BANK 1 / modules 1 + 2 / address 0x34','BANK 2 / modules 3 + 4 / address 0x35',
                'BANK 3 / modules 5 + 6 / address 0x36','BANK 4 / module 7 / address 0x37',
                'CONTROLLER / USB, artwork and recovery','POWER / protected input and 3V3 regulator',
                'BUS PULL-UPS / shutdown default / CC current-advertisement sensing','SWD RECOVERY / test contacts']
        positions={ref:(68.58+110.49*c,76.2+63.5*r) for r,row in enumerate(rows) for c,ref in enumerate(row)}
        page='A1'
    else:
        rows=[['J1','J2'],['U1','D1'],['R1','R2','C1']]
        titles=['USB-C / 5V sink and USB2 full-speed data','ESD / shunt protection','CC PULL-DOWNS / input bypass']
        positions={ref:(66.04+(110.49 if r<2 else 83.82)*c,53.34+50.8*r) for r,row in enumerate(rows) for c,ref in enumerate(row)}
        page='A4'
    missing=[p['ref'] for p in parts if p['ref'] not in positions]
    for i,ref in enumerate(missing):positions[ref]=(68.58+110.49*i,584.2)
    symbols=[symbol(p)[0] for p in parts]+[flag_symbol(board)]
    s=[f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0") (uuid {q(sheet)}) (paper {q(page)})',
       f'(title_block (title {q("House Rules / "+board+" PCB")}) (date "2026-10-29") (rev {q(revision)}) (company "House Rules recreation") (comment 1 "ENGINEERING PROTOTYPE / validate module pin orientation before fabrication"))',
       '(lib_symbols','\n'.join(symbols),')']
    for p in parts:s.extend(instance(p,*positions[p['ref']],sheet,stem))
    if board=='main':
        for r,t in enumerate(titles):s.append(drawing_text(t,12.7,45.72+63.5*r,2.3))
        s.append(drawing_text('Named nets connect all matching labels on this sheet. Every physical package pin is shown; crosses mark intentional no-connects.',12.7,566.42,2.2))
        s.append(drawing_text('47k ISET limits LED pulse current. LED_SDB defaults low. Firmware must authorise USB current before bright playback. USB data and recovery share the carrier harness.',12.7,571.5,2.1))
        fy=579.12
        rails=['VBUS','+5V','GND']
    else:
        for r,t in enumerate(titles):s.append(drawing_text(t,12.7,27.94+50.8*r,2.3))
        s.append(drawing_text('Separate 5.1k Rd on CC1 and CC2. No higher-voltage PD request.',12.7,180.34,1.7))
        s.append(drawing_text('Both cable orientations carry the same USB2 D+/D- nets.',12.7,185.42,1.7))
        s.append(drawing_text('Harness: pin number to same pin number; verify continuity before connection.',12.7,190.5,1.7))
        s.append(drawing_text('ESD NC pads are explicitly joined by PCB copper; they have no internal flow-through.',12.7,195.58,1.7))
        fy=168.91
        rails=['VBUS','GND']
    # Explicitly document why each externally powered/passive rail needs a flag.
    for i,net in enumerate(rails):
        x=40.64+40.64*i; ref=f'#FLG0{i+1}';pid=uid('house-rules:'+board+':'+ref)
        s.append(f'(symbol (lib_id {q(library+":PowerFlag")}) (at {f(x)} {f(fy)} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(pid)}) {prop("Reference",ref,x,fy,hide=True)} {prop("Value","PWR_FLAG",x,fy-3.81,hide=True)} (pin "1" (uuid {q(uid(pid+":pin:1"))})) (instances (project {q(stem)} (path {q("/"+sheet)} (reference {q(ref)}) (unit 1)))))')
        s.append(f'(wire (pts (xy {f(x)} {f(fy)}) (xy {f(x)} {f(fy+2.54)})) (stroke (width 0) (type default)) (uuid {q(uid(pid+":wire"))}))')
        s.append(f'(global_label {q(net)} (shape passive) (at {f(x)} {f(fy+2.54)} 0) {effects(1.05,"left bottom")} (uuid {q(uid(pid+":label"))}))')
    s.append('(embedded_fonts no))')
    (DEST/(stem+'.kicad_sch')).write_text('\n'.join(s)+'\n')
    library_symbols=[symbol(p,True)[0] for p in parts]+[flag_symbol(board,True)]
    (DEST/(library+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n'+'\n'.join(library_symbols)+'\n)\n')
    return sheet


def validate(spec):
    out=ROOT/'hardware/reports'
    out.mkdir(parents=True,exist_ok=True)
    failures=[]
    summary={'date':'2026-10-29','spec_sha256':hashlib.sha256((DEST/'circuit-spec.json').read_bytes()).hexdigest(),'boards':{},'erc_exclusions':False}
    for board in spec['boards']:
        sch=DEST/('house-rules-'+board+'.kicad_sch')
        erc=out/('schematic-verification-'+board+'.erc.json');net=out/('schematic-verification-'+board+'.net.xml')
        r=subprocess.run([str(CLI),'sch','erc','--format','json','--severity-all','--output',str(erc),'--exit-code-violations',str(sch)],capture_output=True,text=True)
        print(board,'ERC:',r.returncode,r.stdout.strip(),r.stderr.strip())
        if erc.exists():
            data=json.loads(erc.read_text())
            violations=[v for sh in data.get('sheets',[]) for v in sh.get('violations',[])]
            for v in violations[:8]:print(json.dumps(v))
            if len(violations)>8:print(f'... {len(violations)-8} additional violations in report')
        r2=subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','--output',str(net),str(sch)],capture_output=True,text=True)
        if r2.returncode:raise RuntimeError(r2.stdout+r2.stderr)
        tree=ET.parse(net)
        actual={}
        for n in tree.findall('./nets/net'):
            for pin in n.findall('node'):
                if not pin.attrib['ref'].startswith('#'):
                    actual[(pin.attrib['ref'],pin.attrib['pin'])]=n.attrib['name'].lstrip('/')
        expected={(p['ref'],pn):nn for p in spec['parts'] if p['board']==board for pn,nn in p['pins'].items() if nn is not None}
        missing={k:v for k,v in expected.items() if actual.get(k)!=v}
        extra={k:v for k,v in actual.items() if k not in expected and not v.startswith('unconnected-')}
        if missing or extra:raise RuntimeError(f'{board} netlist mismatch: missing={missing}, extra={extra}')
        print(board,f'netlist verified: {len(expected)} connected pins, all nets match circuit-spec.json')
        summary['boards'][board]={'component_count':len([p for p in spec['parts'] if p['board']==board]),'connected_pin_count':len(expected),'netlist_matches_spec':True,'erc_exit_code':r.returncode,'erc_violation_count':len(violations),'erc_report':erc.name,'netlist':net.name}
        if r.returncode:failures.append(str(erc))
    (out/'schematic-verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Verification outputs:',out)
    if failures:raise RuntimeError('ERC violations; see '+', '.join(failures))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    spec=json.loads((DEST/'circuit-spec.json').read_text())
    DEST.mkdir(parents=True,exist_ok=True)
    for b in spec['boards']:
        parts=[p for p in spec['parts'] if p['board']==b]
        sheet=make_board(b,parts,spec.get('revision','A1'))
        print(b,len(parts),'parts; root sheet UUID',sheet)
    table='(sym_lib_table (version 7)\n'+''.join(f'(lib (name "HouseRules_{b}")(type "KiCad")(uri "${{KIPRJMOD}}/HouseRules_{b}.kicad_sym")(options "")(descr "Explicit House Rules package symbols"))\n' for b in spec['boards'])+')\n'
    (DEST/'sym-lib-table').write_text(table)
    if args.verify:validate(spec)


if __name__=='__main__':main()
