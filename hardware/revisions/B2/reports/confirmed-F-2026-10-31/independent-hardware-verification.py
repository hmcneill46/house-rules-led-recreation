#!/usr/bin/env python3
"""Independent read-only check of the owner-confirmed F hardware revision.

Run with KiCad's Python. Expectations come from frozen Git efad429 plus the
owner's 12.875 mm request, not the pitch updater or its generated report.
Only this script's JSON report is written inside the repository.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

import pcbnew as k
import wx

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]
REPO = B2.parents[2]
BOARD = B2 / 'kicad/house-rules-main-B2.kicad_pcb'
FROZEN_REV = 'efad429'
FROZEN_BOARD_SHA = '90018f786599e140bdc7ed6a75be65f574c2691c98f3b2d91a7383906dbe0b04'
EXPECTED_BOARD_SHA = 'b42e3d59b40a2e9cc877f8c5595d58339a2c7b0797970fa826ea84c19b8105f1'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NM = 1000000
POWER = {'VBUS', 'FUSED_VBUS', '+5V', '+3V3', 'SW_3V3', 'VLED_5V', 'GND'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_bytes(relative):
    return subprocess.check_output(['git', 'show', FROZEN_REV + ':' + relative], cwd=REPO)


def field(fp, name):
    f = fp.GetField(name)
    return f.GetText() if f else ''


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def fp_identity(fp):
    lib = fp.GetFPID()
    return [fp.GetValue(), str(lib.GetLibNickname())+':'+str(lib.GetLibItemName()), fp.GetLayer(), fp.GetOrientationDegrees(),
            field(fp, 'MPN'), field(fp, 'LCSC'), fp.IsDNP()]


def pad_identity(pad):
    size, drill = pad.GetSize(), pad.GetDrillSize()
    return [pad.GetNetname(), size.x, size.y, drill.x, drill.y,
            int(pad.GetShape()), int(pad.GetAttribute()), pad.GetOrientationDegrees(),
            bool(pad.GetPrimaryDrillFilledFlag()), bool(pad.GetPrimaryDrillCappedFlag()),
            tuple(int(x) for x in pad.GetLayerSet().Seq())]


def outline(board):
    shape = k.SHAPE_POLY_SET()
    require(board.GetBoardPolygonOutlines(shape, False), 'Closed outline unavailable')
    require(shape.OutlineCount() == 1 and shape.HoleCount(0) == 0, 'One outline without routed holes required')
    box = shape.BBox()
    origin = board.GetDesignSettings().GetAuxOrigin()
    require((box.GetX(), box.GetY()) == (origin.x, origin.y), 'Outline must start at auxiliary origin')
    require((box.GetWidth(), box.GetHeight()) == (89450000, 17300000), 'Exact 89.450 x17.300 outline required')
    return [box.GetWidth() / NM, box.GetHeight() / NM]


def via_identity(via, settings):
    filled = via.GetFillingMode() == k.FILLING_MODE_FILLED or (
        via.GetFillingMode() == k.FILLING_MODE_FROM_BOARD and settings.m_FillVias)
    capped = via.GetCappingMode() == k.CAPPING_MODE_CAPPED or (
        via.GetCappingMode() == k.CAPPING_MODE_FROM_BOARD and settings.m_CapVias)
    return (via.GetNetname(), via.GetWidth(k.F_Cu), via.GetDrillValue(), int(via.GetViaType()),
            via.TopLayer(), via.BottomLayer(), bool(filled), bool(capped))


def min_gap(a, b, same=False):
    gaps = []
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if same and j <= i:
                continue
            gaps.append((math.hypot(x[0]-y[0], x[1]-y[1])-(x[2]+y[2])/2)/NM)
    return min(gaps)


def board_check(board, old):
    cur = {fp.GetReference(): fp for fp in board.GetFootprints()}
    prior = {fp.GetReference(): fp for fp in old.GetFootprints()}
    require(set(cur) == set(prior) and len(cur) == 82, 'Exact frozen 82 references required')
    for suffix in ['.kicad_pro','.kicad_dru','.kicad_sch']:
        relative = 'hardware/revisions/B2/kicad/house-rules-main-B2'+suffix
        require((REPO/relative).read_bytes() == git_bytes(relative),
                'Frozen project/rules/schematic bytes changed: '+suffix)
    spec = json.loads((B2 / 'electrical-spec.json').read_text())
    frozen_spec = json.loads(git_bytes('hardware/revisions/B2/electrical-spec.json'))
    require(spec['parts'] == frozen_spec['parts'], 'Electrical parts and all pin roles must remain frozen')
    for name in ['gpio', 'mcu_wire_pads', 'usb_breakout_wire_pads', 'usb_data_wires', 'bc12', 'protocol', 'scan', 'power']:
        require(spec[name] == frozen_spec[name], 'Electrical/firmware contract changed: ' + name)
    factory = {p['ref']: p for p in spec['parts'] if p['assembly'] == 'factory'}
    require(len(factory) == 55, '55 factory parts required')
    origin = board.GetDesignSettings().GetAuxOrigin()
    old_origin = old.GetDesignSettings().GetAuxOrigin()
    require(origin == old_origin, 'Auxiliary origin changed')
    leds, footprint_shifts = {}, {}
    for ref, fp in cur.items():
        before = prior[ref]
        require(fp_identity(fp) == fp_identity(before), 'Footprint metadata/rotation/side changed: ' + ref)
        require(fp.GetY() == before.GetY(), 'Footprint Y changed: ' + ref)
        shift = fp.GetX() - before.GetX()
        require(0 <= shift <= 1050000, 'Footprint X escaped widening range: ' + ref)
        footprint_shifts[ref] = shift
        pads, oldpads = {p.GetNumber(): p for p in fp.Pads()}, {p.GetNumber(): p for p in before.Pads()}
        require(set(pads) == set(oldpads), 'Pad-number set changed: ' + ref)
        for num, pad in pads.items():
            oldpad = oldpads[num]
            require(pad_identity(pad) == pad_identity(oldpad), 'Pad/net/process identity changed: ' + ref + '.' + num)
            require((pad.GetPosition().x-oldpad.GetPosition().x, pad.GetPosition().y-oldpad.GetPosition().y) == (shift, 0),
                    'Footprint was distorted instead of rigidly translated: ' + ref + '.' + num)
        if re.fullmatch(r'DS[1-7]', ref):
            index = int(ref[2:])-1
            require(shift == 175000*index, 'Incorrect owner-selected module translation: ' + ref)
            require(fp.GetX()-origin.x == 6100000+12875000*index and fp.GetY()-origin.y == 8650000,
                    'Incorrect module centre: ' + ref)
            require(len(pads) == 12, 'Exactly 12 module pads required')
            for num, pad in pads.items():
                require(tuple(pad.GetDrillSize()) == (900000, 900000), 'LED drill size changed')
                require(tuple(pad.GetSize()) == (1400000, 1400000), 'LED copper annulus changed')
                require(not pad.GetPrimaryDrillFilledFlag() and not pad.GetPrimaryDrillCappedFlag(), 'LED hole closed')
                leds[ref+'.'+num] = [pad.GetPosition().x-origin.x, pad.GetPosition().y-origin.y]
    drilled = [p for fp in cur.values() for p in fp.Pads() if p.GetDrillSize().x or p.GetDrillSize().y]
    require(len(leds) == len(drilled) == 84, 'Exactly 84 LED holes and no other footprint drills required')
    ds = board.GetDesignSettings()
    require(board.GetCopperLayerCount() == 6 and ds.GetBoardThickness() == 1600000, 'Six layers and1.6mm required')
    require(not ds.m_DrcExclusions, 'DRC exclusions are forbidden')
    vias = [v for v in board.GetTracks() if isinstance(v, k.PCB_VIA)]
    oldvias = [v for v in old.GetTracks() if isinstance(v, k.PCB_VIA)]
    require(len(vias) == len(oldvias) == 276, 'Frozen 276 vias required')
    require(Counter(via_identity(v,ds) for v in vias) == Counter(via_identity(v,old.GetDesignSettings()) for v in oldvias),
            'Via electrical/process inventory changed')
    require(all(via_identity(v,ds)[2:] == (300000, int(k.VIATYPE_THROUGH), k.F_Cu, k.B_Cu, True, True) for v in vias),
            'All vias must be filled/capped F-B through 0.30mm')
    vh = [(v.GetX(), v.GetY(), v.GetDrillValue()) for v in vias]
    lh = [(p.GetPosition().x, p.GetPosition().y, p.GetDrillSize().x) for p in drilled]
    clearances = {'via_to_LED': min_gap(vh,lh), 'via_to_via': min_gap(vh,vh,True)}
    require(clearances['via_to_LED'] >= .45-1e-9 and clearances['via_to_via'] >= .25-1e-9, 'Physical drill clearance failed')
    thermal = {}
    for ref in ['U1','U2','U3','U4']:
        ep = next(p for p in cur[ref].Pads() if p.GetNumber() == '25')
        box = ep.GetBoundingBox()
        inside = [v for v in vias if box.GetX() <= v.GetX() <= box.GetRight() and box.GetY() <= v.GetY() <= box.GetBottom()]
        require(len(inside) == 3 and all(v.GetNetname() == 'GND' for v in inside), 'Thermal vias failed: ' + ref)
        for v in inside:
            radius = v.GetWidth(k.F_Cu)/2
            require(v.GetX()-radius >= box.GetX() and v.GetX()+radius <= box.GetRight()
                    and v.GetY()-radius >= box.GetY() and v.GetY()+radius <= box.GetBottom(), 'Thermal annulus escapes EP')
        thermal[ref] = len(inside)
    ct = 0
    for track in board.GetTracks():
        if isinstance(track, k.PCB_VIA):
            continue
        net = track.GetNetname()
        minimum = 150000 if net in POWER or re.fullmatch(r'COL[1-5]_A',net) else 110000
        require(track.GetWidth() >= minimum, 'Track width reduced below preserved minimum')
        if track.GetLayer() == k.In2_Cu and net == 'CT_5V':
            ct += track.GetLength()/NM
        elif track.GetLayer() in [k.In2_Cu,k.In4_Cu]:
            require(net == 'GND', 'Foreign signal on reference plane')
    require(ct <= 12, 'CT timing bridge exceeds12mm')
    planes = {}
    for layer in [k.In2_Cu,k.In4_Cu]:
        zones = [z for z in board.Zones() if z.GetLayer() == layer]
        require(zones and all(z.GetNetname() == 'GND' for z in zones), 'GND-only zones required')
        area = sum(z.GetFilledPolysList(layer).Area()/NM**2 for z in zones)
        count = sum(z.GetFilledPolysList(layer).OutlineCount() for z in zones)
        require(area > 89.45*17.3/2, 'Ground area belowhalfPCB')
        if layer == k.In2_Cu:
            require(count == 1, 'In2 GND must remain one connected filled outline')
        planes[k.LayerName(layer)] = {'area_mm2':area,'connected_outlines':count}
    return {'outline_mm':outline(board),'LED_holes_nm':leds,'module_centres_mm':[[6.1+12.875*i,8.65] for i in range(7)],
            'all_84_holes_exact_frozen_pattern_plus_175000nm_per_index':True,'footprints_rigid_not_scaled':True,
            'project_custom_rules_and_schematic_identical_to_frozen_Git':True,
            'footprint_X_shift_nm':footprint_shifts,'references':82,'factory_parts':55,'vias':276,'thermal_vias':thermal,
            'hole_edge_clearance_mm':clearances,'CT_In2_length_mm':ct,'ground_planes':planes,
            'nominal_LED_outer_rectangle_mm':[-.25,-.25,89.95,17.8],
            'PCB_inside_nominal_LED_outer_rectangle_with_0p25mm_margins':True}


def native_drc():
    with tempfile.TemporaryDirectory(prefix='house-rules-independent-F-') as temp:
        folder = Path(temp)
        cad = BOARD.parent
        for name in ['house-rules-main-B2.kicad_pcb','house-rules-main-B2.kicad_pro','house-rules-main-B2.kicad_dru',
                     'house-rules-main-B2.kicad_sch','fp-lib-table','sym-lib-table','HouseRules_main.kicad_sym']:
            shutil.copy2(cad/name,folder/name)
        shutil.copytree(cad/'footprints',folder/'footprints')
        require(sha(folder/BOARD.name) == sha(BOARD), 'Native DRC staged board mismatch')
        command = [CLI,'pcb','drc','--format','json','--severity-all','--schematic-parity','--exit-code-violations',
                   '--output',str(folder/'drc.json'),str(folder/BOARD.name)]
        run = subprocess.run(command,capture_output=True,text=True)
        require(run.returncode == 0, 'Independent native DRC failed: '+run.stdout+run.stderr)
        drc = json.loads((folder/'drc.json').read_text())
        counts = {n:len(drc[n]) for n in ['violations','unconnected_items','schematic_parity']}
        require(not any(counts.values()), 'Native violations/unconnected/parity found')
        return {'independent_read_only_staged_run':True,'counts':counts,'version':drc['kicad_version'],
                'report_sha256':sha(folder/'drc.json'),'stdout':run.stdout,'stderr':run.stderr,
                'source_SHA256':sha(BOARD),'saved_board_or_refill_requested':False}


def triangles(path):
    data = path.read_bytes()
    if len(data) >= 84 and len(data) == 84+50*struct.unpack('<I',data[80:84])[0]:
        for offset in range(84,len(data),50):
            floats = struct.unpack('<12fH',data[offset:offset+50])
            yield [tuple(floats[i:i+3]) for i in [3,6,9]]
    else:
        vertices = [tuple(map(float,line.split()[1:4])) for line in data.decode().splitlines() if line.lstrip().startswith('vertex ')]
        require(len(vertices)%3 == 0, 'Malformed ASCII STL')
        for i in range(0,len(vertices),3):
            yield vertices[i:i+3]


def mesh(path):
    edges, directions, vertices, volume = Counter(),Counter(),[],0
    for a,b,c in triangles(path):
        v = [tuple(round(x,5) for x in p) for p in [a,b,c]]
        vertices += v
        for i in range(3):
            p,q = v[i],v[(i+1)%3]
            edges[tuple(sorted([p,q]))] += 1
            directions[(p,q)] += 1
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    require(all(n == 2 for n in edges.values()) and volume > 0, 'Mesh notclosedpositive: '+str(path))
    require(all(directions[(a,b)] == directions[(b,a)] for a,b in edges), 'Mesh windinginconsistent')
    lo,hi = [[f(p[i] for p in vertices) for i in range(3)] for f in [min,max]]
    return {'sha256':sha(path),'bounds_mm':[lo,hi],'size_mm':[round(hi[i]-lo[i],5) for i in range(3)],
            'watertight_consistently_oriented':True,'volume_mm3':volume}


def case_check():
    folder = B2/'mechanical'
    contract = json.loads((B2/'stock-module-contract.json').read_text())
    old = json.loads(git_bytes('hardware/revisions/B2/stock-module-contract.json'))
    case = contract['case']
    require(case['outer'] == [94.65,22.6,24.0] and case['main_pcb_xy'] == [89.45,17.3], 'Case/PCB geometry contract mismatch')
    require(case['front_opening'] == [91.45,18.4] and case['led_module_pitch'] == 12.875, 'Case front/pitch mismatch')
    generated = dict((name,json.loads(value)) for name,value in re.findall(r'^(\w+)=(.*);$',(folder/'stock-module-values.scad').read_text(),re.M))
    for name,value in {'case_main_xy':[89.45,17.3],'case_outer_xyz':[94.65,22.6,24.0],
                       'case_front_opening':[91.45,18.4],'case_led_module_pitch':12.875,
                       'case_first_led_centre':[6.1,8.65],'main_upper_wire_pad_stop_x':65.4}.items():
        require(generated[name] == value, 'Generated SCAD contract variable mismatch: '+name)
    source = (folder/'enclosure.scad').read_text()
    require('module_pitch=case_led_module_pitch;' in source and 'main_w=case_main_xy[0];' in source,
            'Case source is not consuming the confirmed geometry contract')
    require(contract['mcu'] == old['mcu'] and contract['usb'] == old['usb'], 'Stock poses/mount geometry unexpectedlychanged')
    geometry = json.loads((folder/'geometry-verification.json').read_text())
    require(geometry['contract_sha256'] == sha(B2/'stock-module-contract.json') and geometry['scad_sha256'] == sha(folder/'enclosure.scad'),
            'Mechanical report is stale relative to currentcontract/source')
    require(all(c['empty'] for c in geometry['collision_checks'].values()), 'Case seated/slide interference present')
    require(geometry['closure_transition']['intentional_positive_interference'], 'Snap undercut transition check missing')
    result = {}
    for name in ['enclosure-B2-PROTOTYPE-shell.stl','enclosure-B2-PROTOTYPE-back.stl','mcu-channel-fit-coupon.stl',
                 'mcu-retaining-cap.stl','case-closure-fit-coupon.stl']:
        result[name] = mesh(folder/name)
    require(result['enclosure-B2-PROTOTYPE-shell.stl']['size_mm'] == [94.65,22.6,22.8], 'Actual shell STL size incorrect')
    require(result['enclosure-B2-PROTOTYPE-back.stl']['size_mm'][:2] == [94.65,22.6], 'Actual back STL size incorrect')
    placement = json.loads((folder/'main-placement-mechanical-audit.json').read_text())
    require(placement['pass'] and placement['board_sha256'] == sha(BOARD) and placement['contract_sha256'] == sha(B2/'stock-module-contract.json'),
            'Native case contact audit stale orfailed')
    return {'meshes':result,'case_contract_sha256':sha(B2/'stock-module-contract.json'),'geometry_report_sha256':sha(folder/'geometry-verification.json'),
            'main_placement_audit_sha256':sha(folder/'main-placement-mechanical-audit.json'),
            'owner_selected_F_is_spacing_evidence_not_FDM_accuracy_claim':True,'stock_poses_unchanged':True,
            'case_intersection_and_transition_checks_current':True}


def manufacturing_check(folder, board):
    folder = folder.resolve()
    data = json.loads((folder/'manifest.json').read_text())
    require(data['source_pcb_sha256'] == sha(BOARD), 'Manufacturing source SHA notcurrent')
    require(data['refilled_saved_snapshot_sha256'] == sha(folder/'source'/BOARD.name), 'Manufacturing snapshot hash mismatch')
    require(data['refilled_saved_snapshot_sha256'] == sha(BOARD), 'Staged source is not byte-identical to the verified canonical PCB')
    staged = k.LoadBoard(str(folder/'source'/BOARD.name))
    require(outline(staged) == [89.45,17.3], 'Staged outline mismatch')
    for relative,digest in data['output_sha256'].items():
        target = (folder/relative).resolve()
        require(target.is_relative_to(folder) and target.is_file() and sha(target) == digest, 'Manifest output digest mismatch: '+relative)
    tools, holes, selected = {},[],None
    drill = folder/'fabrication/house-rules-main-B2-PTH.drl'
    for line in drill.read_text().splitlines():
        m = re.fullmatch(r'T(\d+)C([\d.]+)',line)
        if m:
            tools[m[1]] = float(m[2]);continue
        m = re.fullmatch(r'T(\d+)',line)
        if m:
            selected=m[1];continue
        m = re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
        if m:
            holes.append((round(float(m[1])*NM),round(-float(m[2])*NM),round(tools[selected]*NM)))
    require(Counter(x[2] for x in holes) == Counter({300000:276,900000:84}), 'Actual Excellon drillcounts wrong')
    origin = board.GetDesignSettings().GetAuxOrigin()
    led = [(p.GetPosition().x-origin.x,p.GetPosition().y-origin.y,900000)
           for fp in board.GetFootprints() if re.fullmatch(r'DS[1-7]',fp.GetReference()) for p in fp.Pads()]
    def match_drill_coordinates(actual, expected):
        remaining = list(expected)
        maximum_axis_error = 0
        for x,y,d in actual:
            matches = [(i,max(abs(x-a),abs(y-b))) for i,(a,b,c) in enumerate(remaining)
                       if c == d and abs(x-a) <= 500 and abs(y-b) <= 500]
            require(len(matches) == 1, 'Exported drill has no unique source match within half a micrometre')
            index,error = matches[0]
            maximum_axis_error = max(maximum_axis_error,error)
            remaining.pop(index)
        require(not remaining, 'Source drill missing from export')
        return maximum_axis_error/NM
    led_error = match_drill_coordinates([x for x in holes if x[2] == 900000],led)
    via = [(v.GetX()-origin.x,v.GetY()-origin.y,300000) for v in board.GetTracks() if isinstance(v,k.PCB_VIA)]
    # KiCad Excellon rounds these coordinates to 1 micrometre. Some frozen
    # KiCad pad Ys contain an extra 1 nm, so compare at the actual export
    # resolution rather than asserting impossible bit-for-bit nanometres.
    via_error = match_drill_coordinates([x for x in holes if x[2] == 300000],via)
    profile = (folder/'fabrication/house-rules-main-B2-Edge_Cuts.gm1').read_text()
    xy = [tuple(map(int,m)) for m in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',profile)]
    require('%FSLAX46Y46*%' in profile and set(xy) == {(0,0),(89450000,0),(89450000,-17300000),(0,-17300000)}, 'Actual Gerberprofile not89.45x17.3')
    copper_layers = []
    for path in (folder/'fabrication').iterdir():
        if not path.is_file():
            continue
        content = path.read_text(errors='ignore')
        copper_layers += [int(n) for n in re.findall(r'%TF\.FileFunction,Copper,L(\d+),',content)]
    require(sorted(copper_layers) == [1,2,3,4,5,6], 'Actual Gerber copper stack is not exactly six layers')
    spec = json.loads((B2/'electrical-spec.json').read_text())
    factory = {p['ref']:p for p in spec['parts'] if p['assembly'] == 'factory'}
    with (folder/'assembly/bom.csv').open(newline='') as handle:
        bom = list(csv.DictReader(handle))
    bomrefs = {}
    for row in bom:
        for ref in row['Designator'].split(','):
            require(ref not in bomrefs and ref in factory, 'BOM duplicate/unexpectedreference')
            require(row['LCSC Part #'] == factory[ref]['lcsc'] and row['Comment'] == factory[ref]['mpn'], 'BOMpartmismatch: '+ref)
            bomrefs[ref] = row
    require(set(bomrefs) == set(factory), 'BOM55factoryreferencecoveragefailed')
    with (folder/'assembly/positions-native-factory.csv').open(newline='') as handle:
        native = {r['Ref']:r for r in csv.DictReader(handle)}
    with (folder/'assembly/cpl-manufacturer-review.csv').open(newline='') as handle:
        cpl = {r['Designator']:r for r in csv.DictReader(handle)}
    require(set(native) == set(cpl) == set(factory), 'CPL55factoryreferencecoveragefailed')
    fps = {f.GetReference():f for f in board.GetFootprints()}
    for ref,row in cpl.items():
        fp = fps[ref];nr = native[ref]
        expected = [(fp.GetX()-origin.x)/NM,-(fp.GetY()-origin.y)/NM,fp.GetOrientationDegrees()]
        values = [float(row['Mid X'].removesuffix('mm')),float(row['Mid Y'].removesuffix('mm')),float(row['Rotation'])]
        require(all(abs(a-b)<1e-6 for a,b in zip(values,expected)) and row['Layer'] == 'bottom', 'CPLcoordinate/rotation/side mismatch: '+ref)
        require(values == [float(nr['PosX']),float(nr['PosY']),float(nr['Rot'])], 'CPL changednativeconvention')
    return {'package':str(folder.relative_to(B2)),'manifest_sha256':sha(folder/'manifest.json'),
            'all_manifest_output_hashes_verified':True,'actual_Excellon_LED_centres_match_at_1um_export_resolution':84,
            'staged_source_identical_to_canonical_PCB':True,'actual_Gerber_copper_layers':sorted(copper_layers),
            'actual_Excellon_via_centres_match_at_1um_export_resolution':276,
            'Excellon_maximum_axis_coordinate_rounding_error_mm':{'LED':led_error,'via':via_error},
            'actual_Gerber_outline_mm':[89.45,17.3],'BOM_CPL_exact_factory_references':55,
            'CPL_native_coordinates_angles_and_bottom_side_verified':True,
            'manufacturer_feeder_and_pin1_review_still_required':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-case',action='store_true',help='Clearly report PCB-only interim verification')
    parser.add_argument('--manufacturing',type=Path)
    args=parser.parse_args()
    wx.Log.EnableLogging(False)
    app=wx.App(False)
    before=sha(BOARD)
    require(before == EXPECTED_BOARD_SHA,'Canonical PCB differs from frozen target for this review')
    with tempfile.TemporaryDirectory(prefix='house-rules-frozen-B2-') as temp:
        frozen=Path(temp)/BOARD.name
        frozen.write_bytes(git_bytes('hardware/revisions/B2/kicad/house-rules-main-B2.kicad_pcb'))
        require(sha(frozen) == FROZEN_BOARD_SHA,'Frozen Git source unexpectedly differs')
        board=k.LoadBoard(str(BOARD));old=k.LoadBoard(str(frozen))
        report={'result':'PASS','date_utc':datetime.now(timezone.utc).isoformat(),'canonical_PCB_sha256':before,
                'frozen_Git_revision':FROZEN_REV,'frozen_PCB_sha256':FROZEN_BOARD_SHA,
                'scope':'Independent actual PCB/mesh/export inspection; does not certify fabricated hardware, USB electrical behavior, soldering or actual stock revisions.',
                'PCB':board_check(board,old),'independent_native_DRC':native_drc(),
                'case':'SKIPPED: PCB-only interim verification' if args.skip_case else case_check(),
                'manufacturing':'NOT YET INCLUDED' if not args.manufacturing else manufacturing_check(args.manufacturing,board),
                'no_order_payment_or_printer_execution':True}
    require(sha(BOARD) == before,'Canonical PCB mutated during read-only independent verification')
    report['verifier_sha256']=sha(Path(__file__))
    report['canonical_PCB_unchanged_during_verification']=True
    output=HERE/'independent-hardware-verification.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['result','canonical_PCB_sha256','case','manufacturing']},indent=2))


if __name__=='__main__':
    main()
