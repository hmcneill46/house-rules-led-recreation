#!/usr/bin/env python3
"""Make three labelled seven-module spacing trials; never change the PCB.

Each module's12-hole pattern and1.0mm print holes are preserved. Only the
translation between modules changes. Labels sit on an external test-only tab.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess

HERE = Path(__file__).resolve().parent
PRINTING = HERE.parent
B2 = PRINTING.parent
ROOT = B2.parents[2]
OPENSCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_model(label, pitch, audit):
    delta = round(pitch - 12.7, 2)
    holes = {}
    for key, pad in audit['LED_geometry'].items():
        module = int(key.split('.')[0][2:]) - 1
        x, y = [v / 1e6 for v in pad['relative_position_nm']]
        holes[key] = [round(x + module * delta, 6), round(y, 6)]
    width = round(88.4 + 6 * delta, 3)
    name = label + '_pitch_' + format(pitch, '.2f').replace('.', 'p')
    source = HERE / 'models' / (name + '.scad')
    source.write_text('// PRINT-ONLY spacing trial; not a PCB or case outline.\n'
        '// Intramodule centres unchanged.1.0mm FDM holes,1.6mm base.\n'
        '$fn=32;\nholes=' + json.dumps(list(holes.values())) + ';\n'
        'union(){\n difference(){\n'
        '  union(){cube([' + str(width) + ',17.3,1.6]);\n'
        '   translate([-18,0,0])cube([18.2,17.3,1.6]);}\n'
        '  for(p=holes)translate([p[0],p[1],-.1])cylinder(h=1.8,d=1.0);\n }\n'
        ' translate([-9,13.4,1.59])linear_extrude(height=.61)text("' + label + '",size=4,font="Liberation Sans:style=Bold",halign="center",valign="center");\n'
        ' translate([-9,8.4,1.59])linear_extrude(height=.61)text("P' + format(pitch, '.2f') + '",size=3,font="Liberation Sans:style=Bold",halign="center",valign="center");\n'
        ' translate([-9,3.8,1.59])linear_extrude(height=.61)text("+' + format(delta, '.2f') + '",size=3,font="Liberation Sans:style=Bold",halign="center",valign="center");\n}\n')
    output = source.with_suffix('.stl')
    p = subprocess.run([OPENSCAD, '-o', str(output), str(source)], capture_output=True, text=True)
    (HERE / 'logs' / (name + '.log')).write_text(p.stdout + p.stderr)
    p.check_returncode()
    assert 'WARNING' not in p.stderr and 'ERROR' not in p.stderr, p.stderr
    return {'label': label, 'pitch_mm': pitch, 'extra_per_join_mm': delta,
        'extra_across_six_joins_mm': round(6 * delta, 2),
        'core_outline_mm': [width, 17.3], 'label_tab_mm': [18, 17.3],
        'overall_outline_mm': [width + 18, 17.3], 'base_thickness_mm': 1.6,
        'label_total_height_mm': 2.2, 'print_hole_diameter_mm': 1.0,
        'holes': holes, 'STL': str(output.relative_to(HERE)), 'STL_sha256': sha(output),
        'SCAD': str(source.relative_to(HERE)), 'SCAD_sha256': sha(source)}


def main():
    for name in ('models', 'projects', 'sliced-projects', 'gcode', 'logs', 'previews'):
        (HERE / name).mkdir(exist_ok=True)
    audit_path = B2 / 'reports/board-audit.json'
    audit = json.loads(audit_path.read_text())
    assert audit['result'] == 'PASS' and len(audit['LED_geometry']) == 84
    with ThreadPoolExecutor(max_workers=2) as pool:
        variants = list(pool.map(lambda v: make_model(*v, audit), [('A', 12.8), ('B', 12.9), ('C', 13.0)]))
    module_spec = importlib.util.spec_from_file_location('b2_print_writer', PRINTING / 'prepare_prints.py')
    writer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(writer)
    config = json.loads((PRINTING / 'profiles/01_B2_FitTests_KE04_HyperPLA.json').read_text())
    config.update({'print_settings_id': 'House Rules spacing trials 0.20mm @Ender3V3KE04',
                   'enable_support': '0', 'brim_type': 'no_brim'})
    models = [(HERE / v['STL'], [55, 62 + i * 32]) for i, v in enumerate(variants)]
    models.append((ROOT / 'hardware/mechanical/pin-fit-scale-50mm.stl', [85, 165]))
    job = 'LED_Pitch_ABC_KE04_HyperPLA'
    project = writer.project(job, models, config, output_root=HERE)
    (HERE / 'settings.json').write_text(json.dumps(config, indent=2) + '\n')
    record = {'date': '2026-10-30', 'status': 'PRINT-ONLY trial set; no PCB geometry changed',
        'printer': 'Creality Ender-3 V3 KE0.4mm', 'filament': 'Creality Hyper PLA grey1.75mm',
        'source_PCB_audit_sha256': sha(audit_path), 'source_PCB_sha256': audit['board_sha256'],
        'intramodule_hole_pattern_unchanged': True,
        'font': 'Bundled OpenSCAD Liberation Sans Bold',
        'sizing_rationale': 'Photos show fitted bow; prior owner caliper estimate about12.9mm wide makes12.9 the middle trial. Perspective/print warpage prevent measuring the required increment from images alone.',
        'variants': variants, 'project': project,
        'physical_testing': 'Check empty strips flat, then reuse allseven modules on each. Smallest no-force, no-bow fit is candidate; confirm other14 modules too.',
        'release_note': 'Current12.70mm-pitch PCB/case still require physical spacing resolution and revised checks before any order. Trial tabs/outlines are not final PCB/case dimensions.'}
    (HERE / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
    print(HERE / project['project'])


if __name__ == '__main__':
    main()
