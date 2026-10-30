#!/usr/bin/env python3
"""Generate exact three-decimal D/E/F spacing trials without changing the PCB.

Pitch changes use integer nanometres, avoiding the earlier coarse generator's
two-decimal rounding. All 12 hole positions in each module are translated as
one rigid group. Labels and source filenames retain all three decimals.
"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
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
VARIANTS = [('D', '12.825'), ('E', '12.850'), ('F', '12.875')]
JOB = 'LED_Pitch_DEF_Fine_KE04_HyperPLA'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_model(label, pitch_text, audit):
    pitch = Decimal(pitch_text)
    delta = pitch - Decimal('12.700')
    delta_nm = int(delta * 1_000_000)
    assert Decimal(delta_nm) / 1_000_000 == delta
    holes_nm = {}
    for key, pad in sorted(audit['LED_geometry'].items()):
        module = int(key.split('.')[0][2:]) - 1
        x, y = pad['relative_position_nm']
        assert int(x) == x and int(y) == y
        holes_nm[key] = [int(x) + module * delta_nm, int(y)]
    holes = {key: [x / 1e6, y / 1e6] for key, (x, y) in holes_nm.items()}
    width = Decimal('88.400') + 6 * delta
    name = label + '_pitch_' + pitch_text.replace('.', 'p')
    source = HERE / 'models' / (name + '.scad')
    source.write_text('// PRINT-ONLY fine trial; not a fabrication or case outline.\n'
        '// Intramodule pattern unchanged;1.0mm holes;1.6mm base.\n'
        '$fn=32;\nholes=' + json.dumps(list(holes.values())) + ';\n'
        'union(){difference(){union(){cube([' + format(width, '.3f') + ',17.3,1.6]);\n'
        ' translate([-18,0,0])cube([18.2,17.3,1.6]);}\n'
        ' for(p=holes)translate([p[0],p[1],-.1])cylinder(h=1.8,d=1.0);}\n'
        ' translate([-9,13.4,1.59])linear_extrude(height=.61)text("' + label + '",size=4,font="Liberation Sans:style=Bold",halign="center",valign="center");\n'
        ' translate([-9,8.4,1.59])linear_extrude(height=.61)text("P' + pitch_text + '",size=3,font="Liberation Sans:style=Bold",halign="center",valign="center");\n'
        ' translate([-9,3.8,1.59])linear_extrude(height=.61)text("+' + format(delta, '.3f') + '",size=3,font="Liberation Sans:style=Bold",halign="center",valign="center");}\n')
    output = source.with_suffix('.stl')
    result = subprocess.run([OPENSCAD, '-o', str(output), str(source)], capture_output=True, text=True)
    (HERE / 'logs' / (name + '.log')).write_text(result.stdout + result.stderr)
    result.check_returncode()
    assert 'WARNING' not in result.stderr and 'ERROR' not in result.stderr, result.stderr
    return {'label': label, 'pitch_mm': float(pitch), 'printed_pitch_text': 'P' + pitch_text,
        'extra_per_join_mm': float(delta), 'extra_per_join_nm': delta_nm,
        'printed_increment_text': '+' + format(delta, '.3f'),
        'extra_across_six_joins_mm': float(6 * delta),
        'core_outline_mm': [float(width), 17.3], 'label_tab_mm': [18, 17.3],
        'overall_outline_mm': [float(width + 18), 17.3],
        'base_thickness_mm': 1.6, 'label_total_height_mm': 2.2,
        'print_hole_diameter_mm': 1.0, 'holes_nm': holes_nm, 'holes_mm': holes,
        'STL': str(output.relative_to(HERE)), 'STL_sha256': sha(output),
        'SCAD': str(source.relative_to(HERE)), 'SCAD_sha256': sha(source)}


def main():
    for folder in ('models', 'projects', 'sliced-projects', 'gcode', 'logs', 'previews'):
        (HERE / folder).mkdir(exist_ok=True)
    audit_path = B2 / 'reports/board-audit.json'
    audit = json.loads(audit_path.read_text())
    assert audit['result'] == 'PASS' and len(audit['LED_geometry']) == 84
    with ThreadPoolExecutor(max_workers=2) as pool:
        variants = list(pool.map(lambda v: make_model(*v, audit), VARIANTS))
    module_spec = importlib.util.spec_from_file_location('b2_print_writer', PRINTING / 'prepare_prints.py')
    writer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(writer)
    config = json.loads((PRINTING / 'profiles/01_B2_FitTests_KE04_HyperPLA.json').read_text())
    config.update({'print_settings_id': 'House Rules fine pitch trials 0.20mm @Ender3V3KE04',
                   'enable_support': '0', 'brim_type': 'no_brim'})
    objects = [(HERE / v['STL'], [55, 62 + 32 * i]) for i, v in enumerate(variants)]
    objects.append((ROOT / 'hardware/mechanical/pin-fit-scale-50mm.stl', [85, 165]))
    project = writer.project(JOB, objects, config, output_root=HERE)
    (HERE / 'settings.json').write_text(json.dumps(config, indent=2) + '\n')
    report = {'date': '2026-10-30', 'status': 'PRINT-ONLY fine trials; no PCB geometry changed',
        'owner_evidence': 'Owner confirms the required repeat lies between12.80 and12.90mm and requests these three intermediate trials.',
        'source_PCB_audit_sha256': sha(audit_path), 'source_PCB_sha256': audit['board_sha256'],
        'coordinate_arithmetic': 'Integer nanometres; exact125000/150000/175000nm rigid translations per module index. No two-decimal rounding.',
        'intramodule_pattern_unchanged': True, 'variants': variants, 'project': project,
        'print_precision_note': 'Nominal CAD increments are0.025mm; do not infer this absolute accuracy from FDM. Across six joins the differences accumulate to0.150mm. Check flatness and the50mm coupon.',
        'hardware_execution': 'No printer connection or print started'}
    (HERE / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(HERE / project['project'])


if __name__ == '__main__':
    main()
