#!/usr/bin/env python3
"""Check actual meshes, sliced geometry and executable KE G-code independently.

Read-only for inputs. Writes verification.json only; does not connect a printer.
The old fine-trial verifier supplies generic STL/3MF parsers, not expectations.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re
import zipfile

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]
ROOT = B2.parents[2]
parser_spec = importlib.util.spec_from_file_location('mesh_parsers', HERE.parent/'fine-pitch-tests-2026-10-30/verify_fine_pitch_tests.py')
parsers = importlib.util.module_from_spec(parser_spec)
parser_spec.loader.exec_module(parsers)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_dummy(path, geometry):
    triangles = parsers.read_stl(path)
    edges = Counter()
    bottom = Counter()
    directed = Counter()
    adjacency = defaultdict(set)
    for triangle in triangles:
        for i, a in enumerate(triangle):
            b = triangle[(i+1)%3]
            edges[tuple(sorted((a,b)))] += 1
            directed[(a,b)] += 1
            adjacency[a].add(b)
            adjacency[b].add(a)
            if all(abs(p[2]) < 1e-8 for p in triangle):
                bottom[tuple(sorted((a[:2],b[:2])))] += 1
    assert all(n == 2 for n in edges.values())
    assert all(directed[(a,b)] == directed[(b,a)] for a,b in edges)
    assert len(parsers.components(adjacency)) == 1
    assert len(adjacency)-len(edges)+len(triangles) == -166
    boundary = defaultdict(set)
    for (a,b),n in bottom.items():
        if n == 1:
            boundary[a].add(b)
            boundary[b].add(a)
    assert all(len(n) == 2 for n in boundary.values())
    loops = parsers.components(boundary)
    assert len(loops) == 85
    holes = [loop for loop in loops if len(loop) == 32]
    assert len(holes) == 84
    centres = []
    for loop in holes:
        assert all(abs(max(p[i] for p in loop)-min(p[i] for p in loop)-1) < .0001 for i in (0,1))
        centres.append(tuple(sum(p[i] for p in loop)/len(loop) for i in (0,1)))
    used = set()
    errors = []
    for key,pad in geometry.items():
        expected = [v/1e6 for v in pad['relative_position_nm']]
        index = min(range(84),key=lambda i:math.dist(centres[i],expected))
        errors.append(math.dist(centres[index],expected))
        assert errors[-1] < .0001 and index not in used, key
        used.add(index)
    actual_bounds = parsers.bounds(triangles)
    assert max(abs(a-b) for a,b in zip(actual_bounds[0],[0,0,0])) < .0001
    assert max(abs(a-b) for a,b in zip(actual_bounds[1],[89.45,17.3,1.6])) < .0001
    return {'closed_consistently_wound_single_body':True,'actual_hole_count':84,
        'actual_hole_diameter_mm':1.0,'maximum_centre_error_from_native_PCB_mm':max(errors),
        'actual_bounds_mm':actual_bounds,'nominal_module_pitch_mm':12.875}


def check_gcode(path, shell, expected_count, expected_height):
    text = path.read_text()
    config = dict(re.findall(r'^; ([A-Za-z0-9_]+) = (.*)$',text,re.M))
    expected = {'printer_settings_id':'Creality Ender-3 V3 KE 0.4 nozzle',
        'nozzle_diameter':'0.4','filament_type':'PLA','filament_diameter':'1.75',
        'gcode_flavor':'klipper','layer_height':'0.2','initial_layer_print_height':'0.2',
        'xy_hole_compensation':'0','xy_contour_compensation':'0',
        'enable_support':'1' if shell else '0','brim_type':'outer_only' if shell else 'no_brim',
        'nozzle_temperature':'215','nozzle_temperature_initial_layer':'220',
        'first_layer_bed_temperature':'60'}
    for key,value in expected.items():
        assert config.get(key) == value,(path.name,key,config.get(key),value)
    with zipfile.ZipFile(ROOT/'hardware/printing/HouseRules_Fit_KE04_PLA.3mf') as z:
        original = json.loads(z.read('Metadata/project_settings.config'))
    for key in ('machine_start_gcode','machine_end_gcode'):
        assert config[key].replace('\\n','\n') == original[key]
    executable = text.split('; CONFIG_BLOCK_START',1)[0]
    for token in ('M104 S220','M109 S220','M140 S60','M190 S60','M104 S215',
                  'M140 S55','M104 S0','M140 S0','M106 S0','M106 S255',
                  'G28 X Y','G28 Z','BED_MESH_CALIBRATE PROBE_COUNT=5,5'):
        assert re.search(r'^'+re.escape(token)+r'(?:\s|$)',executable,re.M),token
    heaters = {'M104':{0.,215.,220.},'M109':{220.},'M140':{0.,55.,60.},'M190':{60.}}
    for code,value in re.findall(r'^(M104|M109|M140|M190) S([0-9.]+)',executable,re.M):
        assert float(value) in heaters[code]
    xyz = [0.,0.,0.]
    e = 0.
    relative_e = relative_xyz = started = False
    obj = None
    kind = ''
    moves = []
    extrusions = []
    model = []
    objects = Counter()
    features = Counter()
    first = set()
    for line in executable.splitlines():
        if line.startswith(';LAYER_CHANGE'):started = True
        if line.startswith(';TYPE:'):kind = line[6:]
        if line.startswith('EXCLUDE_OBJECT_START NAME='):obj = line.split('=',1)[1]
        if line.startswith('EXCLUDE_OBJECT_END'):obj = None
        command = line.split(';')[0].strip()
        if not command:continue
        code = command.split()[0]
        params = {k:float(v) for k,v in re.findall(r'([XYZEF])(-?(?:\d+(?:\.\d*)?|\.\d+))',command)}
        if code == 'M83':relative_e = True
        elif code == 'M82':relative_e = False
        elif code == 'G90':relative_xyz = False
        elif code == 'G91':relative_xyz = True
        elif code == 'G92':
            if 'E' in params:e = params['E']
        elif code in ('G0','G1'):
            before = xyz[:]
            for i,axis in enumerate('XYZ'):
                if axis in params:xyz[i] = xyz[i]+params[axis] if relative_xyz else params[axis]
            de = params.get('E',0) if relative_e else params.get('E',e)-e
            if 'E' in params:e = e+de if relative_e else params['E']
            if any(axis in params for axis in 'XYZ'):moves.append(xyz[:])
            if started and de > 0 and math.dist(before[:2],xyz[:2]) > 0:
                extrusions.extend([before[:],xyz[:]])
                features[kind] += 1
                if obj:
                    objects[obj] += 1
                    if abs(xyz[2]-.2) < 1e-6:first.add(obj)
                    if kind not in ('Support','Support interface','Brim','Skirt'):
                        model.extend([before[:],xyz[:]])
    assert len(objects) == expected_count and len(first) == expected_count,(path.name,objects,first)
    assert all(-2.001 <= p[0] <= 220 and 0 <= p[1] <= 220 and 0 <= p[2] <= 245 for p in moves)
    assert all(0 <= p[0] <= 220 and 0 <= p[1] <= 220 and 0 < p[2] <= expected_height+.21 for p in extrusions)
    assert abs(max(p[2] for p in model)-expected_height) <= .21
    assert abs(min(p[0] for p in moves)+2) < 1e-8
    assert any(abs(p[0]+1.7) < 1e-8 for p in moves)
    assert abs(moves[-1][0]-2) < 1e-8 and abs(moves[-1][1]-218) < 1e-8
    if shell:
        assert features['Support'] > 0 and features['Support interface'] > 0
        assert features['Brim'] > 0
    else:
        assert all(features[k] == 0 for k in ('Support','Support interface','Brim'))
    return {'actual_profile_and_heater_commands_verified':True,'native_start_end_preserved':True,
        'temperatures_C':{'nozzle':[220,215],'bed':[60,55]},
        'all_objects_extrude_from_first_layer':True,'object_extrusion_segments':dict(objects),
        'feature_extrusion_segments':dict(features),'all_motion_bounds_mm':[[min(p[i] for p in moves) for i in range(3)],[max(p[i] for p in moves) for i in range(3)]],
        'extrusion_bounds_mm':[[min(p[i] for p in extrusions) for i in range(3)],[max(p[i] for p in extrusions) for i in range(3)]],
        'actual_model_maximum_Z_mm':max(p[2] for p in model),
        'stock_negative_X_purge_and_final_park_preserved':True,
        'estimated_time':re.search(r'^; estimated printing time \(normal mode\) = (.+)$',text,re.M).group(1),
        'estimated_filament_g':float(re.search(r'^; filament used \[g\] = ([0-9.]+)',text,re.M).group(1))}


def main():
    board_audit = json.loads((B2/'reports/board-audit.json').read_text())
    assert board_audit['result'] == 'PASS'
    assert sha(B2/'kicad/house-rules-main-B2.kicad_pcb') == board_audit['board_sha256']
    preparation = json.loads((HERE/'preparation.json').read_text())
    mechanical = json.loads((B2/'mechanical/geometry-verification.json').read_text())
    assert mechanical['contract_sha256'] == sha(B2/'stock-module-contract.json')
    assert mechanical['scad_sha256'] == sha(B2/'mechanical/enclosure.scad')
    assert all(c['empty'] for c in mechanical['collision_checks'].values())
    assert mechanical['closure_transition']['intentional_positive_interference']
    placement = json.loads((B2/'mechanical/main-placement-mechanical-audit.json').read_text())
    assert placement['pass'] and placement['board_sha256'] == board_audit['board_sha256']
    assert placement['contract_sha256'] == sha(B2/'stock-module-contract.json')
    report = {'result':'PASS','date_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Independent STL/3MF/executable G-code checks, not a physical print or fit test.',
        'canonical_PCB_sha256':board_audit['board_sha256'],
        'mechanical_geometry_report_sha256':sha(B2/'mechanical/geometry-verification.json'),
        'native_case_contact_audit_sha256':sha(B2/'mechanical/main-placement-mechanical-audit.json'),
        'dummy':check_dummy(HERE/'models/B2-main-board-fit-1p6mm.stl',board_audit['LED_geometry']),
        'unchanged_local_fit_parts':{},'jobs':{}}
    for name in ('mcu-channel-fit-coupon.stl','mcu-retaining-cap.stl','case-closure-fit-coupon.stl'):
        current = B2/'mechanical'/name
        archived = B2/'mechanical/archive-12p700-2026-10-29'/name
        check = parsers.compare_meshes(archived,parsers.read_stl(current))
        report['unchanged_local_fit_parts'][name] = {'archived_sha256':sha(archived),
            'current_sha256':sha(current),'actual_triangle_geometry_unchanged':check['source_mesh_geometry_retained']}
    for job,record in preparation['jobs'].items():
        project = HERE/'sliced-projects'/(job+'.3mf')
        gcode = HERE/'gcode'/(job+'.gcode')
        with zipfile.ZipFile(project) as z:
            assert z.read('Metadata/plate_1.gcode') == gcode.read_bytes()
            actual = parsers.sliced_objects(z)
        assert len(actual) == len(record['objects'])
        mesh_checks = {}
        for source in record['objects']:
            path = ROOT/source['source']
            assert sha(path) == source['sha256']
            check = parsers.compare_meshes(path,actual[path.stem])
            assert max(abs(a-b) for side,expect in zip(check['actual_plate_bounds_mm'],source['plate_bounds_mm']) for a,b in zip(side,expect)) < .00002
            mesh_checks[path.stem] = check
        height = max(o['size_mm'][2] for o in record['objects'])
        report['jobs'][job] = {'Gcode_sha256':sha(gcode),'sliced_project_sha256':sha(project),
            'embedded_Gcode_byte_identical':True,'meshes':mesh_checks,
            'Gcode_checks':check_gcode(gcode,record['supports'],len(record['objects']),height)}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: confirmed-F dummy and three KE/Hyper PLA print jobs; exact meshes and embedded G-code match.')


if __name__ == '__main__':
    main()
