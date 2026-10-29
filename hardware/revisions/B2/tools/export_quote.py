#!/usr/bin/env python3
"""Export a distinct, explicitly non-production quotation study from a candidate.

This does not waive DRC or approve manufacturing. It refuses existing output
directories so a later circuit cannot silently overwrite earlier price evidence.
Run with KiCad's Python interpreter (pcbnew and wx are required).
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import wx
import pcbnew as k

B2 = Path(__file__).resolve().parents[1]
CLI = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not args.label.replace('-', '').isalnum():
        raise ValueError('Use a short alphanumeric/hyphen study label')
    app = wx.App(False)
    source = args.source.resolve()
    spec_path = B2 / 'electrical-spec.json'
    spec = json.loads(spec_path.read_text())
    board = k.LoadBoard(str(source))
    actual = {f.GetReference(): f for f in board.GetFootprints()}
    assert set(actual) == {p['ref'] for p in spec['parts']}, 'Candidate has a stale part set'
    checked_pins = 0
    for part in spec['parts']:
        footprint = actual[part['ref']]
        pads = {p.GetNumber(): p for p in footprint.Pads() if p.GetNumber()}
        assert set(pads) == set(part['pins']), part['ref']
        for number, expected in part['pins'].items():
            observed = pads[number].GetNetname()
            if expected:
                assert observed == expected, (part['ref'], number, expected, observed)
                checked_pins += 1
            else:
                assert not observed or observed.startswith('unconnected-'), (part['ref'], number)
    factory = {p['ref']: p for p in spec['parts'] if p.get('assembly') == 'factory'}
    for ref, part in factory.items():
        footprint = actual[ref]
        assert footprint.GetLayer() == k.B_Cu, ref
        assert footprint.GetField('MPN').GetText() == part['mpn'], ref
        assert footprint.GetField('LCSC').GetText() == part['lcsc'], ref
    target = args.out.resolve()
    target.mkdir(parents=True, exist_ok=False)
    stem = args.label + '-UNRELEASED-COST-STUDY-DO-NOT-ORDER'
    pcb = target / (stem + '.kicad_pcb')
    shutil.copy2(source, pcb)
    fabrication = target / 'fabrication'
    fabrication.mkdir()
    layers = board.GetCopperLayerCount()
    copper = ['F.Cu'] + [f'In{i}.Cu' for i in range(1, layers - 1)] + ['B.Cu']
    run([CLI, 'pcb', 'export', 'gerbers', '--layers',
         ','.join(copper + ['F.Mask', 'B.Mask', 'F.SilkS', 'B.SilkS', 'Edge.Cuts']),
         '--use-drill-file-origin', '--subtract-soldermask', '--check-zones',
         '--output', str(fabrication) + '/', pcb])
    run([CLI, 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin',
         'plot', '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal',
         '--excellon-separate-th', '--excellon-oval-format', 'route',
         '--output', str(fabrication) + '/', pcb])
    raw = target / 'native-all.csv'
    run([CLI, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
         '--side', 'both', '--use-drill-file-origin', '--smd-only', '--exclude-dnp',
         '--output', raw, pcb])
    with raw.open(newline='') as handle:
        positions = [p for p in csv.DictReader(handle) if p['Ref'] in factory]
    assert {p['Ref'] for p in positions} == set(factory)
    with (target / (stem + '-CPL.csv')).open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for p in positions:
            writer.writerow([p['Ref'], p['PosX'] + 'mm', p['PosY'] + 'mm', p['Side'], p['Rot']])
    groups = collections.defaultdict(list)
    for ref, part in factory.items():
        groups[(part['mpn'], part['lcsc'], part['footprint'].split(':')[1])].append(ref)
    with (target / (stem + '-BOM.csv')).open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (mpn, code, footprint), refs in sorted(groups.items()):
            writer.writerow([mpn, ','.join(refs), footprint, code])
    warning = ('UNRELEASED COST STUDY ONLY. DO NOT ORDER OR MANUFACTURE. '
               'This quotation input is not a production release. The board may be '
               'incompletely routed; native placement rotations have not received '
               'factory review. Re-export and re-quote the approved, fully verified '
               'board before ordering.\n')
    (target / 'README-DO-NOT-ORDER.txt').write_text(warning)
    with zipfile.ZipFile(target / (stem + '-GERBERS.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(fabrication.iterdir()):
            archive.write(file, file.name)
    manifest = {
        'status': 'UNRELEASED COST STUDY ONLY — NEVER PRODUCTION',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'electrical_spec_sha256': hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        'layers': layers, 'factory_component_count': len(factory),
        'bom_groups': len(groups), 'physical_component_count': len(actual),
        'connected_pin_name_parity': checked_pins,
        'warnings': [warning.strip(), 'Native bottom rotations require factory verification'],
    }
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))
    print(target)


if __name__ == '__main__':
    main()
