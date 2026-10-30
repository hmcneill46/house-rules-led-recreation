#!/usr/bin/env python3
"""Prepare separate Orca projects from the proven KE/Hyper PLA fit profile.

No printer connection, motion or firmware changes. Original meshes are only
translated on the plate; all scale and rotation transforms remain identity.
The generated PCB dummy is a print-only thickness/position gauge, not a PCB.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import uuid
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
B2 = HERE.parent
ROOT = B2.parents[2]
BASE = ROOT / 'hardware/printing/HouseRules_Fit_KE04_PLA.3mf'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('', CORE)
ET.register_namespace('p', PROD)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def triangles(path):
    data = path.read_bytes()
    if len(data) >= 84 and 84 + 50 * struct.unpack('<I', data[80:84])[0] == len(data):
        for off in range(84, len(data), 50):
            values = struct.unpack('<12fH', data[off:off + 50])
            yield [tuple(values[j:j + 3]) for j in (3, 6, 9)]
    else:
        points = [tuple(map(float, line.split()[1:4])) for line in data.decode().splitlines()
                  if line.lstrip().startswith('vertex ')]
        assert len(points) % 3 == 0
        for off in range(0, len(points), 3):
            yield points[off:off + 3]


def xml_bytes(element):
    return ET.tostring(element, encoding='utf-8', xml_declaration=True)


def metadata(parent, key, value):
    return ET.SubElement(parent, 'metadata', {'key': key, 'value': str(value)})


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'house-rules-b2-print:' + value))


def make_dummy():
    """Use the checked PCB's exact84 LED centres; FDM holes are1.0mm."""
    audit = json.loads((B2 / 'reports/board-audit.json').read_text())
    points = [p['relative_position_nm'] for p in audit['LED_geometry'].values()]
    assert len(points) == 84
    holes = sorted([[round(x / 1e6, 6), round(y / 1e6, 6)] for x, y in points])
    folder = HERE / 'models'
    folder.mkdir(exist_ok=True)
    scad = folder / 'B2-main-board-fit-1p6mm.scad'
    scad.write_text('// PRINT-ONLY gauge: no copper/components; NOT fabrication data.\n'
        '//1.0mm FDM holes differ from the real0.90mm finished PCB holes.\n'
        '$fn=32;\nholes=' + json.dumps(holes) + ';\n'
        'difference(){cube([88.4,17.3,1.6]);\n'
        ' for(p=holes)translate([p[0],p[1],-.1])cylinder(h=1.8,d=1.0);}\n')
    output = folder / 'B2-main-board-fit-1p6mm.stl'
    p = subprocess.run(['/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD',
                        '-o', str(output), str(scad)], capture_output=True, text=True)
    (HERE / 'logs/dummy-build.log').write_text(p.stdout + p.stderr)
    p.check_returncode()
    return output


def project(job, objects, config, output_root=None):
    destination = HERE if output_root is None else Path(output_root)
    model = ET.Element('{' + CORE + '}model', {
        'unit': 'millimeter', 'requiredextensions': 'p',
        '{http://www.w3.org/XML/1998/namespace}lang': 'en-US'})
    for name, value in [('Application', 'OrcaSlicer-2.4.2'), ('OrcaSlicer', '2.4.2'),
                        ('BambuStudio:3mfVersion', '1'), ('Title', job)]:
        ET.SubElement(model, '{' + CORE + '}metadata', {'name': name}).text = value
    resources = ET.SubElement(model, '{' + CORE + '}resources')
    build = ET.SubElement(model, '{' + CORE + '}build', {'{' + PROD + '}UUID': uid(job)})
    settings = ET.Element('config')
    plate = ET.Element('plate')
    for k, v in [('plater_id', '1'), ('plater_name', job), ('locked', 'false')]:
        metadata(plate, k, v)
    relationships = ET.Element('Relationships', {'xmlns': REL})
    entries = {}
    record = []
    for index, (source, minimum_xy) in enumerate(objects):
        ts = list(triangles(source))
        raw = [p for triangle in ts for p in triangle]
        lo = [min(p[i] for p in raw) for i in range(3)]
        hi = [max(p[i] for p in raw) for i in range(3)]
        size = [hi[i] - lo[i] for i in range(3)]
        centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
        odd, even = 2 * index + 1, 2 * index + 2
        path = '3D/Objects/' + source.stem + '_' + str(odd) + '.model'
        child = ET.Element('{' + CORE + '}model', {'unit': 'millimeter'})
        child_resources = ET.SubElement(child, '{' + CORE + '}resources')
        child_obj = ET.SubElement(child_resources, '{' + CORE + '}object', {'id': str(odd), 'type': 'model'})
        mesh = ET.SubElement(child_obj, '{' + CORE + '}mesh')
        vertices = ET.SubElement(mesh, '{' + CORE + '}vertices')
        faces = ET.SubElement(mesh, '{' + CORE + '}triangles')
        lookup = {}
        for triangle in ts:
            indices = []
            for point in triangle:
                if point not in lookup:
                    lookup[point] = len(lookup)
                    ET.SubElement(vertices, '{' + CORE + '}vertex', {
                        axis: format(point[i] - centre[i], '.12g') for i, axis in enumerate('xyz')})
                indices.append(lookup[point])
            ET.SubElement(faces, '{' + CORE + '}triangle', {
                'v' + str(i + 1): str(n) for i, n in enumerate(indices)})
        ET.SubElement(child, '{' + CORE + '}build')
        entries[path] = xml_bytes(child)
        parent_obj = ET.SubElement(resources, '{' + CORE + '}object', {
            'id': str(even), 'type': 'model', '{' + PROD + '}UUID': uid(job + source.name)})
        components = ET.SubElement(parent_obj, '{' + CORE + '}components')
        ET.SubElement(components, '{' + CORE + '}component', {
            '{' + PROD + '}path': '/' + path, 'objectid': str(odd),
            '{' + PROD + '}UUID': uid(path), 'transform': '1 0 0 0 1 0 0 0 1 0 0 0'})
        target = [minimum_xy[0] + size[0] / 2, minimum_xy[1] + size[1] / 2, size[2] / 2]
        ET.SubElement(build, '{' + CORE + '}item', {
            'objectid': str(even), '{' + PROD + '}UUID': uid('item:' + path),
            'transform': '1 0 0 0 1 0 0 0 1 ' + ' '.join(format(v, '.12g') for v in target),
            'printable': '1', 'auto_drop': '1'})
        ET.SubElement(relationships, 'Relationship', {'Target': '/' + path, 'Id': 'rel-' + str(index + 1),
            'Type': 'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'})
        obj_config = ET.SubElement(settings, 'object', {'id': str(even)})
        metadata(obj_config, 'name', source.stem)
        metadata(obj_config, 'extruder', '1')
        part = ET.SubElement(obj_config, 'part', {'id': str(odd), 'subtype': 'normal_part'})
        for k, v in [('name', source.stem), ('matrix', '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'),
                     ('source_file', source.name), ('source_object_id', '0'), ('source_volume_id', '0')]:
            metadata(part, k, v)
        for axis, value in zip('xyz', centre):
            metadata(part, 'source_offset_' + axis, format(value, '.12g'))
        ET.SubElement(part, 'mesh_stat', {k: '0' for k in
            ['edges_fixed', 'degenerate_facets', 'facets_removed', 'facets_reversed', 'backwards_edges']})
        instance = ET.SubElement(plate, 'model_instance')
        for k, v in [('object_id', even), ('instance_id', '0'), ('identify_id', 100 + index)]:
            metadata(instance, k, v)
        record.append({'source': str(source.relative_to(ROOT)), 'sha256': sha(source),
            'triangles': len(ts), 'size_mm': size, 'source_bounds_mm': [lo, hi],
            'plate_bounds_mm': [minimum_xy + [0],
                [minimum_xy[0] + size[0], minimum_xy[1] + size[1], size[2]]],
            'scale_percent': 100, 'rotation_degrees': [0, 0, 0]})
    settings.append(plate)
    entries.update({'3D/3dmodel.model': xml_bytes(model),
        '3D/_rels/3dmodel.model.rels': xml_bytes(relationships),
        'Metadata/model_settings.config': xml_bytes(settings),
        'Metadata/project_settings.config': json.dumps(config, indent=2).encode(),
        '_rels/.rels': ('<?xml version="1.0"?><Relationships xmlns="' + REL + '">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>').encode(),
        '[Content_Types].xml': b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="gcode" ContentType="text/x.gcode"/></Types>'})
    output = destination / 'projects' / (job + '.3mf')
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return {'project': str(output.relative_to(destination)), 'project_sha256': sha(output), 'objects': record}


def main():
    for folder in ('logs', 'models', 'projects', 'profiles', 'gcode', 'previews'):
        (HERE / folder).mkdir(exist_ok=True)
    with zipfile.ZipFile(BASE) as archive:
        config = json.loads(archive.read('Metadata/project_settings.config'))
    assert config['printer_settings_id'] == 'Creality Ender-3 V3 KE 0.4 nozzle'
    assert config['nozzle_diameter'] == ['0.4'] and config['gcode_flavor'] == 'klipper'
    start_end = {k: config[k] for k in ('machine_start_gcode', 'machine_end_gcode')}
    config.update({'print_settings_id': 'House Rules B2 0.20mm Hyper PLA @Ender3V3KE04',
        'outer_wall_speed': '35', 'inner_wall_speed': '60',
        'internal_solid_infill_speed': '80', 'sparse_infill_speed': '80',
        'top_surface_speed': '35', 'bridge_speed': '25', 'internal_bridge_speed': '100%',
        'support_speed': '60', 'support_interface_speed': '30',
        'support_type': 'normal(auto)', 'support_style': 'snug',
        'support_on_build_plate_only': '1', 'support_threshold_angle': '30',
        'support_top_z_distance': '0.2', 'support_bottom_z_distance': '0.2',
        'support_object_xy_distance': '0.3', 'support_interface_top_layers': '2',
        'support_interface_spacing': '0.3',
        'sparse_infill_pattern': 'gyroid', 'sparse_infill_density': '25%',
        'travel_speed': '180', 'default_acceleration': '1500',
        'outer_wall_acceleration': '800', 'inner_wall_acceleration': '1500',
        'print_sequence': 'by layer', 'brim_width': '3', 'brim_object_gap': '0.15'})
    assert all(config[k] == v for k, v in start_end.items())
    dummy = make_dummy()
    mech = B2 / 'mechanical'
    jobs = [
        ('01_B2_FitTests_KE04_HyperPLA', [(dummy, [65, 65]),
            (mech / 'mcu-channel-fit-coupon.stl', [80, 105]),
            (mech / 'case-closure-fit-coupon.stl', [115, 102]),
            (ROOT / 'hardware/mechanical/pin-fit-scale-50mm.stl', [85, 140])], False),
        ('02_B2_Shell_KE04_HyperPLA', [(mech / 'enclosure-B2-PROTOTYPE-shell.stl', [63.2, 98.7])], True),
        ('03_B2_BackAndCap_KE04_HyperPLA', [
            (mech / 'enclosure-B2-PROTOTYPE-back.stl', [63.2, 85]),
            (mech / 'mcu-retaining-cap.stl', [100, 125])], False)]
    report = {'slicer': 'OrcaSlicer2.4.2', 'printer': config['printer_settings_id'],
        'filament': 'Creality Hyper PLA GREY1.75mm', 'base_project': str(BASE.relative_to(ROOT)),
        'base_project_sha256': sha(BASE), 'machine_start_end_preserved': True,
        'jobs': {}, 'hardware_execution': 'No printer connection or print started'}
    for name, objects, supports in jobs:
        job_config = dict(config, enable_support='1' if supports else '0',
                          brim_type='outer_only' if supports else 'no_brim')
        (HERE / 'profiles' / (name + '.json')).write_text(json.dumps(job_config, indent=2) + '\n')
        report['jobs'][name] = project(name, objects, job_config)
        report['jobs'][name]['supports'] = supports
        report['jobs'][name]['outside_brim_mm'] = 3 if supports else 0
    (HERE / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(HERE)


if __name__ == '__main__':
    main()
