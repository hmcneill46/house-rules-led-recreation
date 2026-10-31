#!/usr/bin/env python3
"""Independently inspect the combined native plate and executable KE G-code.

Read-only for inputs; writes verification.json only. The expectations are the
seven frozen confirmed-F meshes, not a generated layout's claimed geometry.
No printer is connected and no print is started.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[2]
ROOT = B2.parents[2]
SHELL = 'enclosure-B2-PROTOTYPE-shell'
EXPECTED_PCB_SHA = 'b42e3d59b40a2e9cc877f8c5595d58339a2c7b0797970fa826ea84c19b8105f1'
SOURCES = {
    'B2-main-board-fit-1p6mm': ('hardware/revisions/B2/printing/2026-10-31-confirmed-F/models/B2-main-board-fit-1p6mm.stl', '643ecddb8ad7384f3c721909019f144565dcae5642ff531b7a59f3a5442d8c9e'),
    'mcu-channel-fit-coupon': ('hardware/revisions/B2/mechanical/mcu-channel-fit-coupon.stl', '7f7b609fb40f6c3aa99f3b5b3976fd423c8cd30a5c9071053362c5d020de4d3f'),
    'case-closure-fit-coupon': ('hardware/revisions/B2/mechanical/case-closure-fit-coupon.stl', 'af8297bc7ef0153aae03c1c863ac9521cd3c536ebac961e16e313ba1dabd6d11'),
    'pin-fit-scale-50mm': ('hardware/mechanical/pin-fit-scale-50mm.stl', '8407d5a158e01f16f075c1205059893b26de417170958225695eb6dd52e3255a'),
    SHELL: ('hardware/revisions/B2/mechanical/enclosure-B2-PROTOTYPE-shell.stl', '568d92a04acd80bb85939bcf59cb91d3df77d251180da0e0bae272e63dd40bb3'),
    'enclosure-B2-PROTOTYPE-back': ('hardware/revisions/B2/mechanical/enclosure-B2-PROTOTYPE-back.stl', 'fb5dcc29a8ca4c8559f471e5d2cde42042af05010f8449a3655fd8bac2574af9'),
    'mcu-retaining-cap': ('hardware/revisions/B2/mechanical/mcu-retaining-cap.stl', 'baa5db4801ea1992f102fffc7f4c64ede8f2175703322fae2d54381a8a7d307e'),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parsers = load_module('combined_mesh_parsers', HERE.parents[1] / 'fine-pitch-tests-2026-10-30/verify_fine_pitch_tests.py')
previous = load_module('combined_dummy_check', HERE.parent / 'verify_print_pack.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings(archive):
    global_config = json.loads(archive.read('Metadata/project_settings.config'))
    model_settings = ET.fromstring(archive.read('Metadata/model_settings.config'))
    result = {}
    for obj in model_settings.findall('object'):
        metadata = {m.attrib['key']: m.attrib['value'] for m in obj.findall('metadata')}
        name = metadata['name']
        result[name] = {key: metadata.get(key, global_config.get(key)) for key in
                        ('enable_support', 'brim_type', 'brim_width', 'support_type',
                         'support_style', 'support_on_build_plate_only',
                         'support_top_z_distance', 'support_interface_top_layers')}
    assert set(result) == set(SOURCES), result
    assert global_config['print_sequence'] == 'by layer'
    for name, config in result.items():
        assert config['enable_support'] == ('1' if name == SHELL else '0'), (name, config)
        assert config['brim_type'] == ('outer_only' if name == SHELL else 'no_brim'), (name, config)
        if name == SHELL:
            assert float(config['brim_width']) == 3
            assert config['support_type'] == 'normal(auto)' and config['support_style'] == 'snug'
            assert config['support_on_build_plate_only'] == '1'
            assert float(config['support_top_z_distance']) == .2
            assert int(config['support_interface_top_layers']) == 2
    return global_config, result


def inflated(box, margin):
    return [[box[0][0]-margin, box[0][1]-margin],
            [box[1][0]+margin, box[1][1]+margin]]


def contains(box, point, tolerance=.001):
    return all(box[0][i]-tolerance <= point[i] <= box[1][i]+tolerance for i in range(2))


def gap(a, b):
    return math.hypot(max(0, a[0][0]-b[1][0], b[0][0]-a[1][0]),
                      max(0, a[0][1]-b[1][1], b[0][1]-a[1][1]))


def identify(name):
    if name is None:
        return None
    matches = [stem for stem in SOURCES if name == stem or name.startswith(stem + '_id_')]
    assert len(matches) == 1, name
    return matches[0]


def executable_audit(path, actual_bounds):
    text = path.read_text()
    config = dict(re.findall(r'^; ([A-Za-z0-9_]+) = (.*)$', text, re.M))
    expected = {'printer_settings_id':'Creality Ender-3 V3 KE 0.4 nozzle',
        'nozzle_diameter':'0.4', 'filament_type':'PLA', 'filament_diameter':'1.75',
        'gcode_flavor':'klipper', 'print_sequence':'by layer',
        'layer_height':'0.2', 'initial_layer_print_height':'0.2',
        'xy_hole_compensation':'0', 'xy_contour_compensation':'0',
        'nozzle_temperature':'215', 'nozzle_temperature_initial_layer':'220',
        'first_layer_bed_temperature':'60'}
    for key, value in expected.items():
        assert config.get(key) == value, (key, config.get(key), value)
    with zipfile.ZipFile(ROOT / 'hardware/printing/HouseRules_Fit_KE04_PLA.3mf') as archive:
        original = json.loads(archive.read('Metadata/project_settings.config'))
    for key in ('machine_start_gcode', 'machine_end_gcode'):
        assert config[key].replace('\\n', '\n') == original[key], key
    executable = text.split('; CONFIG_BLOCK_START', 1)[0]
    for token in ('M104 S220','M109 S220','M140 S60','M190 S60','M104 S215',
                  'M140 S55','M104 S0','M140 S0','M106 S0','M106 S255',
                  'G28 X Y','G28 Z','BED_MESH_CALIBRATE PROBE_COUNT=5,5'):
        assert re.search(r'^'+re.escape(token)+r'(?:\s|$)', executable, re.M), token
    heaters = {'M104':{0.,215.,220.}, 'M109':{220.}, 'M140':{0.,55.,60.}, 'M190':{60.}}
    for command, value in re.findall(r'^(M104|M109|M140|M190) S([0-9.]+)', executable, re.M):
        assert float(value) in heaters[command]
    layer_z = list(map(float, re.findall(r'^;Z:([0-9.]+)', executable, re.M)))
    assert layer_z and abs(layer_z[0]-.2) < 1e-8
    assert all(b >= a-1e-8 for a,b in zip(layer_z,layer_z[1:])), 'Layer sequence returns to completed layers'
    assert abs(max(layer_z)-22.8) < .001
    xyz = [0.,0.,0.]
    e = 0.
    relative_e = relative_xyz = started = False
    object_name = None
    kind = ''
    moves, extrusion_points = [], []
    objects = Counter()
    first_layer = set()
    features = Counter()
    special = Counter()
    per_object_special = defaultdict(Counter)
    shell_envelope = inflated(actual_bounds[SHELL], 3.15)
    special_points = []
    model_z = defaultdict(list)
    first_printed_layer = None
    for line in executable.splitlines():
        if line.startswith(';LAYER_CHANGE'):
            started = True
        if line.startswith(';Z:'):
            first_printed_layer = float(line[3:])
        if line.startswith(';TYPE:'):
            kind = line[6:]
        if line.startswith('EXCLUDE_OBJECT_START NAME='):
            object_name = identify(line.split('=',1)[1])
        if line.startswith('EXCLUDE_OBJECT_END'):
            object_name = None
        command = line.split(';',1)[0].strip()
        if not command:
            continue
        code = command.split()[0]
        params = {k:float(v) for k,v in re.findall(r'([XYZEF])(-?(?:\d+(?:\.\d*)?|\.\d+))', command)}
        if code == 'M83':
            relative_e = True
        elif code == 'M82':
            relative_e = False
        elif code == 'G90':
            relative_xyz = False
        elif code == 'G91':
            relative_xyz = True
        elif code == 'G92':
            if 'E' in params:
                e = params['E']
        elif code in ('G0','G1'):
            before = xyz[:]
            for axis_index, axis in enumerate('XYZ'):
                if axis in params:
                    xyz[axis_index] = xyz[axis_index]+params[axis] if relative_xyz else params[axis]
            de = params.get('E',0) if relative_e else params.get('E',e)-e
            if 'E' in params:
                e = e+de if relative_e else params['E']
            if any(axis in params for axis in 'XYZ'):
                moves.append(xyz[:])
            if started and de > 0 and math.dist(before[:2],xyz[:2]) > 1e-9:
                extrusion_points.extend((before[:],xyz[:]))
                features[kind] += 1
                if kind in ('Support','Support interface','Brim','Skirt'):
                    assert kind != 'Skirt', 'Unexpected skirt not part of the allocated shell brim'
                    assert object_name in (None,SHELL), (kind, object_name)
                    assert contains(shell_envelope,before) and contains(shell_envelope,xyz), (kind,before,xyz)
                    special[kind] += 1
                    per_object_special[str(object_name)][kind] += 1
                    special_points.extend((before[:],xyz[:]))
                else:
                    assert object_name is not None, (kind,before,xyz)
                    assert contains(inflated(actual_bounds[object_name],.25),before)
                    assert contains(inflated(actual_bounds[object_name],.25),xyz)
                    objects[object_name] += 1
                    model_z[object_name].append(xyz[2])
                    if abs(xyz[2]-.2) < .00001 and abs(first_printed_layer-.2) < .00001:
                        first_layer.add(object_name)
    assert set(objects) == set(SOURCES) and first_layer == set(SOURCES), (objects,first_layer)
    assert all(special[k] > 0 for k in ('Support','Support interface','Brim')), special
    assert all(-2.001 <= p[0] <= 220 and 0 <= p[1] <= 220 and 0 <= p[2] <= 245 for p in moves)
    assert all(0 <= p[0] <= 220 and 0 <= p[1] <= 220 and 0 < p[2] <= 23.01 for p in extrusion_points)
    assert abs(min(p[0] for p in moves)+2) < 1e-8
    assert any(abs(p[0]+1.7) < 1e-8 for p in moves)
    assert abs(moves[-1][0]-2) < 1e-8 and abs(moves[-1][1]-218) < 1e-8
    for name, zs in model_z.items():
        expected_height = actual_bounds[name][1][2]-actual_bounds[name][0][2]
        assert abs(max(zs)-expected_height) < .21, (name,max(zs),expected_height)
    bounds = lambda points:[[min(p[i] for p in points) for i in range(3)],
                           [max(p[i] for p in points) for i in range(3)]]
    return {'all_seven_objects_extrude_on_first_layer':True,
        'print_sequence':'by layer; actual layer Z never resets',
        'native_start_end_and_negative_X_purge_preserved':True,
        'actual_heater_commands_and_Klipper_KE04_PLA_profile_verified':True,
        'temperatures_C':{'nozzle':[220,215],'bed':[60,55]},
        'all_motion_bounds_mm':bounds(moves), 'extrusion_bounds_mm':bounds(extrusion_points),
        'support_interface_brim_only_in_shell_allocation':True,
        'shell_allocation_including_3p15mm_brim_mm':shell_envelope,
        'special_feature_bounds_mm':bounds(special_points),
        'special_feature_segments':dict(special),
        'special_feature_segments_by_active_object':{name:dict(value) for name,value in per_object_special.items()},
        'model_segments_by_object':dict(objects), 'all_feature_segments':dict(features),
        'actual_model_maximum_Z_by_object_mm':{name:max(zs) for name,zs in model_z.items()},
        'estimated_time':re.search(r'^; estimated printing time \(normal mode\) = (.+)$',text,re.M).group(1),
        'estimated_filament_g':float(re.search(r'^; filament used \[g\] = ([0-9.]+)',text,re.M).group(1))}


def main():
    board = B2 / 'kicad/house-rules-main-B2.kicad_pcb'
    assert sha(board) == EXPECTED_PCB_SHA
    board_audit = json.loads((B2 / 'reports/board-audit.json').read_text())
    assert board_audit['result'] == 'PASS' and board_audit['board_sha256'] == EXPECTED_PCB_SHA
    preparation = json.loads((HERE / 'preparation.json').read_text())
    assert len(preparation['jobs']) == 1
    job, record = next(iter(preparation['jobs'].items()))
    assert len(record['objects']) == 7
    gcode = HERE / 'gcode' / (job+'.gcode')
    project = HERE / 'sliced-projects' / (job+'.3mf')
    with zipfile.ZipFile(project) as archive:
        assert archive.read('Metadata/plate_1.gcode') == gcode.read_bytes()
        _, effective_settings = settings(archive)
        actual = parsers.sliced_objects(archive)
    assert set(actual) == set(SOURCES)
    mesh_checks = {}
    actual_bounds = {}
    claimed = {Path(row['source']).stem:row for row in record['objects']}
    assert set(claimed) == set(SOURCES)
    for name,(relative_path,expected_sha) in SOURCES.items():
        path = ROOT / relative_path
        assert sha(path) == expected_sha, path
        assert claimed[name]['sha256'] == expected_sha
        check = parsers.compare_meshes(path,actual[name])
        expected_bounds = claimed[name]['plate_bounds_mm']
        assert max(abs(a-b) for side,expect in zip(check['actual_plate_bounds_mm'],expected_bounds)
                   for a,b in zip(side,expect)) < .00002
        mesh_checks[name] = check
        actual_bounds[name] = check['actual_plate_bounds_mm']
    allocated = {name:inflated(bounds,3.15 if name == SHELL else 0) for name,bounds in actual_bounds.items()}
    pairs = []
    names = sorted(allocated)
    for index, name in enumerate(names):
        assert all(0 <= v <= 220 for side in allocated[name] for v in side)
        for other in names[index+1:]:
            separation = gap(allocated[name],allocated[other])
            assert separation >= 2-.00002, (name,other,separation)
            pairs.append({'a':name,'b':other,'allocated_bounding_rectangle_gap_mm':separation})
    report = {'result':'PASS','date_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Independent actual STL, sliced mesh/settings and executable G-code checks; no physical print or fit guarantee.',
        'canonical_PCB_sha256':EXPECTED_PCB_SHA,
        'mechanical_report_sha256':sha(B2/'mechanical/geometry-verification.json'),
        'job':job, 'prepared_project_sha256':sha(HERE/'projects'/(job+'.3mf')),
        'sliced_project_sha256':sha(project), 'Gcode_sha256':sha(gcode),
        'embedded_Gcode_byte_identical':True,
        'source_meshes_frozen_and_unscaled':True, 'object_count':7,
        'dummy':previous.check_dummy(ROOT / SOURCES['B2-main-board-fit-1p6mm'][0],board_audit['LED_geometry']),
        'meshes':mesh_checks,'effective_sliced_per_object_settings':effective_settings,
        'allocated_pairwise_gaps':pairs,
        'Gcode_checks':executable_audit(gcode,actual_bounds),
        'canonical_PCB_unchanged':sha(board) == EXPECTED_PCB_SHA,
        'no_printer_connection_or_execution':True}
    (HERE / 'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: all seven confirmed-F objects on one plate; shell-only supports/brim, native KE settings and executable toolpaths checked.')


if __name__ == '__main__':
    main()
