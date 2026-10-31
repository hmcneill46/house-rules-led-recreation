#!/usr/bin/env python3
"""Combine the seven unchanged confirmed-F objects into one KE/Hyper PLA job.

Native per-object overrides reserve support and brim for the shell. This writes
and slices files only: no UI scene is replaced and no printer is connected.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
B2 = HERE.parents[2]
ROOT = B2.parents[2]
JOB = 'B2_F_AllParts_OnePlate_KE04_HyperPLA'
SLICER = '/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer'
TEMP = Path('/tmp/house-rules-B2-F-single-plate-2026-10-31')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for folder in ('projects', 'profiles', 'gcode', 'sliced-projects', 'logs', 'previews'):
        (HERE/folder).mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('native_print_writer', PACK.parent/'prepare_prints.py')
    writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(writer)
    original = json.loads((PACK/'preparation.json').read_text())
    assert original['main_PCB_sha256'] == sha(B2/'kicad/house-rules-main-B2.kicad_pcb')
    originals = {Path(obj['source']).name: obj
                 for record in original['jobs'].values() for obj in record['objects']}
    placement = [
        ('enclosure-B2-PROTOTYPE-shell.stl', [60, 50]),
        ('enclosure-B2-PROTOTYPE-back.stl', [60, 88]),
        ('B2-main-board-fit-1p6mm.stl', [62, 124]),
        ('pin-fit-scale-50mm.stl', [60, 155]),
        ('case-closure-fit-coupon.stl', [123, 151]),
        ('mcu-channel-fit-coupon.stl', [60, 179]),
        ('mcu-retaining-cap.stl', [100, 174]),
    ]
    assert set(originals) == {name for name, xy in placement}
    objects, overrides = [], {}
    for name, xy in placement:
        source = ROOT/originals[name]['source']
        assert sha(source) == originals[name]['sha256']
        objects.append((source, xy))
        shell = name == 'enclosure-B2-PROTOTYPE-shell.stl'
        overrides[source.stem] = {'enable_support': '1' if shell else '0',
            'brim_type': 'outer_only' if shell else 'no_brim',
            'brim_width': '3' if shell else '0', 'brim_object_gap': '0.15'}
    config = json.loads((PACK/'profiles/02_B2_F_Shell_KE04_HyperPLA.json').read_text())
    config.update({'print_settings_id': 'House Rules B2 F all parts one plate @Ender3V3KE04',
                   'enable_support': '0', 'brim_type': 'no_brim', 'brim_width': '0',
                   'print_sequence': 'by layer'})
    record = writer.project(JOB, objects, config, output_root=HERE, object_overrides=overrides)
    record.update({'supports': 'shell only', 'outside_brim_mm': 3,
        'object_settings': overrides, 'print_sequence': 'by layer'})
    (HERE/'profiles'/f'{JOB}.json').write_text(json.dumps(config,indent=2)+'\n')
    preparation = {key: original[key] for key in ('slicer','printer','filament',
        'base_project','base_project_sha256','machine_start_end_preserved',
        'main_PCB_sha256','main_PCB_audit_sha256','mechanical_contract_sha256',
        'confirmed_module_pitch_mm','main_PCB_xy_mm')}
    preparation.update({'date':'2026-10-31','jobs':{JOB:record},
        'all_seven_original_meshes_unchanged':True,
        'original_three_job_preparation_sha256':sha(PACK/'preparation.json'),
        'hardware_execution':'None; files only'})
    (HERE/'preparation.json').write_text(json.dumps(preparation,indent=2)+'\n')
    TEMP.mkdir(exist_ok=True)
    command = [SLICER,'--datadir',str(TEMP/'user'),'--slice','0','--arrange','0',
        '--orient','0','--outputdir',str(TEMP),'--export-3mf',f'{JOB}-sliced.3mf',
        str(HERE/'projects'/f'{JOB}.3mf')]
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    (HERE/'logs/orca-slice.log').write_text(result.stdout+result.stderr)
    result.check_returncode()
    gcode, sliced = HERE/'gcode'/f'{JOB}.gcode', HERE/'sliced-projects'/f'{JOB}.3mf'
    shutil.copyfile(TEMP/'plate_1.gcode',gcode)
    shutil.copyfile(TEMP/f'{JOB}-sliced.3mf',sliced)
    with zipfile.ZipFile(sliced) as z:
        assert z.read('Metadata/plate_1.gcode') == gcode.read_bytes()
    provenance = {'date_utc':datetime.now(timezone.utc).isoformat(),
        'slicer':'Installed OrcaSlicer 2.4.2','command':command,'exit_code':0,
        'prepared_project_sha256':sha(HERE/'projects'/f'{JOB}.3mf'),
        'sliced_project_sha256':sha(sliced),'Gcode_sha256':sha(gcode),
        'embedded_Gcode_byte_identical':True,
        'owner_UI_state':'Existing unsaved Orca scene preserved.',
        'printer_execution':'None; no printer connection or print start.'}
    (HERE/'slice-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    for line in gcode.read_text().splitlines():
        if line.startswith(('; estimated printing time (normal mode)', '; filament used [g]')):
            print(line)
    print(gcode)


if __name__ == '__main__':
    main()
