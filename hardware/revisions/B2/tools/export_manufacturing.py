#!/usr/bin/env python3
"""Export a strictly gated, review-only B2 fabrication/55-part assembly package.

Run with KiCad's bundled Python. Canonical PCB/project files are read-only.
Native DRC refills and saves a staged same-stem copy before audit and plotting.
No upload, order, placement-rotation correction or source-board mutation occurs.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

import pcbnew as k
import wx
from audit_board import (B2, ROOT, DEFAULT_BOARD, DEFAULT_SPEC, DEFAULT_A1,
                         COPPER, audit_board, digest, natural, exclusions_in_json,
                         measure_drill_gaps, verify_default_severity_evidence,
                         DEFAULT_SEVERITY_EVIDENCE, VERIFIED_NATIVE_DEFAULT_IGNORES)

CAD = B2 / 'kicad'
CLI = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
STEM = 'house-rules-main-B2'
OWNER_LED_EVIDENCE = B2 / 'reports/owner-led-diode-test-2026-10-29.json'


def run(command):
    p = subprocess.run([str(s) for s in command], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(map(str, command)) + '\n' + p.stdout + p.stderr)
    return p.stdout + p.stderr


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def remove_staged_local_state(stage):
    """Discard only generated KiCad per-user UI state inside this staging tree."""
    root, removed = Path(stage).resolve(), []
    for path in sorted(root.rglob('*.kicad_prl')):
        try:
            path.parent.resolve().relative_to(root)
        except ValueError:
            raise RuntimeError('Refusing local-state cleanup outside the staging tree')
        if not path.is_file() and not path.is_symlink():
            raise RuntimeError('Unexpected non-file with a .kicad_prl name: ' + str(path))
        removed.append(str(path.relative_to(root)))
        path.unlink()
    return removed


def resolve_staged_model(raw, source_folder):
    """Resolve only a bundled 3D file; never fall back to installed/global assets."""
    prefix = '${KIPRJMOD}/3d/'
    if not raw.startswith(prefix):
        raise RuntimeError('PCB 3D model is not a portable ${KIPRJMOD}/3d reference: ' + raw)
    root = Path(source_folder).resolve()
    target = (root / raw[len('${KIPRJMOD}/'):]).resolve()
    try:
        relative = target.relative_to(root)
        target.relative_to(root / '3d')
    except ValueError:
        raise RuntimeError('PCB 3D model escapes the staged source/3d folder: ' + raw)
    if not target.is_file():
        raise RuntimeError('Staged PCB 3D model is missing: ' + raw)
    return target, str(relative)


def verify_model_references(pcb, source_folder, expected_assets=None):
    """Read the actual staged board and prove every referenced model is internal."""
    root = Path(source_folder).resolve()
    assets = {str(p.relative_to(root)): digest(p)
              for p in sorted((root / '3d').rglob('*')) if p.is_file()}
    if expected_assets is not None and assets != expected_assets:
        raise RuntimeError('Staged 3D assets differ from the complete fingerprinted canonical input set')
    board = k.LoadBoard(str(pcb))
    references, model_less = [], []
    for footprint in sorted(board.GetFootprints(), key=lambda f: natural(f.GetReference())):
        models = list(footprint.Models())
        if not models:
            model_less.append(footprint.GetReference())
        for model in models:
            target, relative = resolve_staged_model(str(model.m_Filename), source_folder)
            references.append({'reference': footprint.GetReference(),
                'native_path': str(model.m_Filename), 'staged_file': relative,
                'sha256': digest(target)})
    if not references:
        raise RuntimeError('The review board unexpectedly references no 3D models')
    return {'all_references_resolve_within_staged_source': True,
            'global_environment_or_absolute_model_paths_allowed': False,
            'reference_count': len(references),
            'unique_files': len({r['staged_file'] for r in references}),
            'bundled_asset_sha256': assets,
            'staged_assets_match_fingerprinted_inputs': expected_assets is not None,
            'references': references, 'footprints_without_3D_models': model_less,
            'scope': 'Portability of actual PCB model references; absent component models are listed, not invented or certified.'}


def validate_drc_report(path):
    data = json.loads(Path(path).read_text())
    if not str(data.get('kicad_version', '')).startswith('10.'):
        raise RuntimeError('A fresh KiCad10 DRC report is required')
    sections = ('violations', 'unconnected_items', 'schematic_parity')
    if any(n not in data or not isinstance(data[n], list) for n in sections):
        raise RuntimeError('Native DRC report lacks required result arrays')
    counts = {n: len(data[n]) for n in sections}
    # Reject every reported severity, including warnings, exclusions and future
    # severity labels. Do not filter to only severity=error as the A1 tool did.
    extras = {n: v for n, v in data.items() if 'exclu' in n.lower() and v}
    if any(counts.values()) or extras:
        preview = [item for n in sections for item in data[n]][:4]
        raise RuntimeError('Native DRC/parity is not exactly zero: ' + json.dumps(counts)
                           + '\n' + json.dumps(preview) + '\nExclusions: ' + json.dumps(extras))
    if not {'error', 'warning', 'exclusion'}.issubset(set(data.get('included_severities', []))):
        raise RuntimeError('DRC did not include errors, warnings and exclusions')
    ignored = data.get('ignored_checks', [])
    if (not isinstance(ignored, list) or any(not isinstance(p, dict)
            or p.get('key') not in VERIFIED_NATIVE_DEFAULT_IGNORES for p in ignored)):
        raise RuntimeError('DRC ignored a check outside the independently verified native defaults')
    return {'counts': counts, 'included_severities': data.get('included_severities'),
            'ignored_default_checks': ignored, 'report_sha256': digest(path)}


def check_drc(cli, pcb, report, log):
    command = [cli, 'pcb', 'drc', '--format', 'json', '--all-track-errors',
               '--severity-all', '--schematic-parity', '--refill-zones', '--save-board',
               '--exit-code-violations', '--output', report, pcb]
    result = subprocess.run([str(s) for s in command], capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    if not report.exists():
        raise RuntimeError('Native DRC produced no report: ' + result.stdout + result.stderr)
    detail = validate_drc_report(report)
    if result.returncode:
        raise RuntimeError('Native DRC returned nonzero despite empty arrays: ' + log.read_text())
    detail['command'] = [str(s) for s in command]
    return detail


def drill_stats(folder, expected_vias):
    """Read actual decimal metric Excellon tool definitions and hit records."""
    files = {}
    combined = Counter()
    plotted_holes = defaultdict(list)
    for path in sorted(folder.glob('*.drl')):
        text = path.read_text()
        if 'METRIC' not in text or 'G85' in text or re.search(r'^M15', text, re.M):
            raise RuntimeError('Only metric round-hole Excellon is expected: ' + path.name)
        if not re.search(r'^G90\s*$', text, re.M) or re.search(r'^G91\s*$', text, re.M):
            raise RuntimeError('Absolute Excellon coordinates are required: ' + path.name)
        tools = {int(n): float(d) for n, d in re.findall(r'^T(\d+)C([0-9.]+)', text, re.M)}
        hits = Counter(); selected = None
        position = {}
        for raw in text.splitlines():
            line = raw.strip()
            m = re.fullmatch(r'T(\d+)', line)
            if m:
                selected = int(m.group(1)); continue
            if re.fullmatch(r'(?:X[+-]?[0-9.]+)?(?:Y[+-]?[0-9.]+)?', line) and line and ('X' in line or 'Y' in line):
                if selected not in tools:
                    raise RuntimeError('Drill hit has no declared tool in ' + path.name)
                position.update({axis: float(value) for axis, value in
                                 re.findall(r'([XY])([+-]?[0-9.]+)', line)})
                if set(position) != {'X', 'Y'}:
                    raise RuntimeError('Drill hit lacks an absolute XY location in ' + path.name)
                hits[selected] += 1
                plotted_holes[round(tools[selected], 6)].append({
                    'x': position['X'], 'y': position['Y'], 'drill': tools[selected],
                    'file': path.name, 'tool': 'T' + str(selected), 'hit': hits[selected]})
        files[path.name] = {'sha256': digest(path),
                            'tools': [{'tool': 'T' + str(t), 'diameter_mm': d, 'hits': hits[t]}
                                      for t, d in sorted(tools.items())], 'total_hits': sum(hits.values())}
        for t, count in hits.items():
            combined[round(tools[t], 6)] += count
        if 'NPTH' in path.stem and sum(hits.values()):
            raise RuntimeError('Unexpected finished-board NPTH/tooling holes')
        if 'PTH' in path.stem and 'NPTH' not in path.stem:
            if tools != {1: .3, 2: .9} or hits != {1: expected_vias, 2: 84}:
                raise RuntimeError('PTH tools/hits must be T1=.30 via count, T2=.90 exactly84 open LED holes: '
                                   + json.dumps(files[path.name]))
    if not files or combined != {.3: expected_vias, .9: 84}:
        raise RuntimeError('Actual drill statistics disagree with the native board: ' + str(combined))
    gaps = measure_drill_gaps(plotted_holes[.3], plotted_holes[.9])
    if any(p['violation_count'] for p in gaps.values()):
        raise RuntimeError('Actual Excellon physical hole clearance failed: ' + json.dumps(gaps))
    return {'files': files, 'diameter_hit_counts': {f'{d:.6f}': n for d, n in sorted(combined.items())},
            'actual_plotted_drill_hole_edge_clearances': gaps,
            'T1_process': 'All0.30mm via holes resin filled and copper capped',
            'T2_process': 'All84 0.90mm LED PTH holes OPEN; never filled/capped'}


def check_gerber_layers(folder):
    functions = []
    for p in sorted(folder.iterdir()):
        if p.suffix in ('.drl', '.svg', '.gbrjob'):
            continue
        text = p.read_text(errors='replace')
        match = re.search(r'%TF\.FileFunction,([^*]+)\*%', text)
        if match:
            functions.append({'file': p.name, 'function': match.group(1)})
    copper = [p for p in functions if p['function'].startswith('Copper,')]
    if len(copper) != 6 or {p['function'].split(',')[1] for p in copper} != {'L' + str(i) for i in range(1, 7)}:
        raise RuntimeError('Actual Gerber X2 functions do not describe six copper layers: ' + str(copper))
    for prefix, count in [('Soldermask,', 2), ('Legend,', 2), ('Profile,', 1)]:
        if sum(p['function'].startswith(prefix) for p in functions) != count:
            raise RuntimeError('Missing fabrication Gerber function ' + prefix)
    return functions


def export_assembly(cli, pcb, output, audit):
    inventory = audit['inventory']
    factory = {r: p for r, p in inventory.items() if p['Assembly'] == 'factory'}
    if len(factory) != 55 or any(r.startswith(('DS', 'J')) for r in factory):
        raise RuntimeError('Exactly55 factory components, excluding every DS/J, required')
    raw = output / 'positions-native-unfiltered.csv'
    # Native KiCad CSV is authoritative: never pass --bottom-negate-x and never
    # negate coordinates or apply package/feeder rotation edits ourselves.
    run([cli, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both',
         '--use-drill-file-origin', '--smd-only', '--exclude-dnp', '--output', raw, pcb])
    with raw.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f); headings = reader.fieldnames
        all_rows = list(reader)
    if not {'Ref', 'PosX', 'PosY', 'Rot', 'Side'}.issubset(set(headings or [])):
        raise RuntimeError('Unexpected KiCad position headings')
    rows = [r for r in all_rows if r['Ref'] in factory]
    if len(rows) != 55 or len({r['Ref'] for r in rows}) != 55 or {r['Ref'] for r in rows} != set(factory):
        raise RuntimeError('Native position output does not contain all55 factory parts exactly once')
    rows.sort(key=lambda r: natural(r['Ref']))
    write_csv(output / 'positions-native-factory.csv', headings, rows)
    raw.unlink()
    cpl, review = [], []
    for r in rows:
        info = factory[r['Ref']]
        if r['Side'].lower() != 'bottom' or info['Side'] != 'bottom':
            raise RuntimeError('Every B2 factory part must be on bottom: ' + r['Ref'])
        if abs(float(r['PosX']) - (info['PCB_X_mm'] - audit['aux_origin_mm'][0])) > .00001:
            raise RuntimeError('Native bottom X was unexpectedly mirrored: ' + r['Ref'])
        for key in ('PosX', 'PosY', 'Rot'):
            float(r[key])
        cpl.append({'Designator': r['Ref'], 'Mid X': r['PosX'] + 'mm', 'Mid Y': r['PosY'] + 'mm',
                    'Layer': r['Side'].lower(), 'Rotation': r['Rot']})
        review.append({'Designator': r['Ref'], **{n: info[n] for n in
                       ('MPN', 'LCSC', 'Value', 'Footprint', 'Side', 'PCB_X_mm', 'PCB_Y_mm', 'PCB_angle_deg',
                        'Pad1_native_relative_X_mm', 'Pad1_native_relative_Y_mm')},
                       'CPL_X_mm': r['PosX'], 'CPL_Y_mm': r['PosY'], 'CPL_rotation_deg': r['Rot']})
    write_csv(output / 'cpl-manufacturer-review.csv', ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'], cpl)
    write_csv(output / 'placement-review.csv', list(review[0]), review)
    groups = defaultdict(list)
    for r, info in factory.items():
        groups[(info['MPN'], info['LCSC'], info['Value'], info['Footprint'])].append(r)
    bom, detail = [], []
    for (mpn, code, value, footprint), refs in sorted(groups.items()):
        names = ','.join(sorted(refs, key=natural))
        bom.append({'Comment': mpn, 'Designator': names, 'Footprint': footprint.split(':')[1], 'LCSC Part #': code})
        detail.append({'MPN': mpn, 'LCSC': code, 'Qty': len(refs), 'Designators': names,
                       'Value': value, 'Footprint': footprint})
    write_csv(output / 'bom.csv', ['Comment', 'Designator', 'Footprint', 'LCSC Part #'], bom)
    write_csv(output / 'bom-review.csv', ['MPN', 'LCSC', 'Qty', 'Designators', 'Value', 'Footprint'], detail)
    excluded = [{'Designator': r, 'Value': p['Value'], 'Reason':
                 'Owner-supplied matrix, fit after factory assembly' if r.startswith('DS') else
                 'Owner-soldered wire land, no factory component or placement'}
                for r, p in sorted(inventory.items(), key=lambda item: natural(item[0])) if p['Assembly'] != 'factory']
    if len(excluded) != 27:
        raise RuntimeError('Expected seven LED modules and20 owner wire lands excluded')
    write_csv(output / 'excluded-from-factory.csv', ['Designator', 'Value', 'Reason'], excluded)
    return {'factory_components': 55, 'bom_groups': len(groups), 'excluded_owner_items': 27,
            'native_rotation_policy': 'UNCORRECTED; manufacturer feeder/pin1 review required',
            'bottom_X_negated': False, 'CPL_coordinate_policy': 'Exact native KiCad mm CSV; no additional axis or rotation transform'}


README = '''# House Rules B2 — MANUFACTURING REVIEW, NOT PRODUCTION APPROVAL

This package passed a fresh native KiCad10 DRC including warnings, exclusions,
unconnected items and schematic parity, after refilling/saving a staged copy.
The five ignored checks that KiCad10.0.7 uses by default are reported
explicitly; their pristine native evidence is included in reports/. UUID
exclusions, custom-rule ignores and other ignored-rule overrides are forbidden.
Its native audit checks82 references,55 factory parts,327 connected pins and the
unchanged84 LED holes against frozen A1. Separate owner-reported diode tests
verify the full12-terminal map and front orientation of ONE owned
LMD07057AUE-101B-02: part-number label on the left in the correct front view.
The other20 modules remain unverified. This does not establish powered-board
operation, actual soldered fit, USB current/compliance, brightness, thermal
performance or print fit. The owner evidence is included in reports/.
No upload, order or payment has been made by the exporter.

Board requirements: SIX copper layers,88.4 x17.3mm final outline,1.6mm FR4.
Layer order is F.Cu/In1.Cu/In2.Cu/In3.Cu/In4.Cu/B.Cu. In4 is GND-only. In2 is
primarily GND with one explicitly approved quiet CT_5V timing-capacitor bridge,
maximum12mm total; no other signal is allowed there. Its GND fill must remain
one connected outline. The final measured length is recorded in the audit.
In3 has signal copper including USB and GND fill; USB retains its unbroken
In4 ground reference. Confirm the actual standard dielectric
stack with the manufacturer. No controlled-impedance certification is claimed.

ALL0.30mm ordinary F-to-B plated through VIAS must be epoxy/resin FILLED and
COPPER CAPPED flat, including12 exposed-pad thermal vias (three per TLC driver)
and the selective0.45mm-pad escape vias. Most via pads are0.60mm; selected escape
pads are0.45mm, minimum annulus0.075mm. Tenting or solder plugging alone is not
equivalent to this fill/cap requirement. No blind/buried/laser vias are specified.

Actual Excellon PTH T1 =0.30mm VIA holes: FILL AND CAP ALL.
Actual Excellon PTH T2 =0.90mm LED mounting holes, exactly84: KEEP OPEN,
UNFILLED AND UNCAPPED. Never apply a blanket fill instruction to all PTH holes.
The actual drill counts and source/output hashes are in manifest.json and
reports/drill-statistics.json. There must be no other finished-board hole tools.
Both native geometry and actual Excellon holes are independently checked for
at least0.45mm via-to-LED-PTH hole-edge clearance and0.25mm via-to-via clearance,
including same-net pairs. These physical checks do not depend on copper DRC.

Narrow-board assembly may need REMOVABLE OUTSIDE RAILS and tooling chosen by the
assembler. Tooling/fiducial holes must be OUTSIDE the finished88.4x17.3mm outline,
on removable rails only. Do not add holes inside the main board or move/close the
84 LED holes. Rails must depanelise completely so the final PCB stays hidden
behind the LEDs. CAM must confirm fill/cap selection, open LED holes and final
outline tolerance before an order is approved.

Factory assembly:55 SMT components on BOTTOM ONLY. DS1..DS7 andJ1..J20 are
owner-fit modules/wire lands, excluded from every factory BOM/CPL. Their copper
and LED holes remain in Gerbers. Do not solder-fill the84 empty LED holes.
The owner supplies the XIAO RP2040 Plus and Adafruit4090 separately and wires
20 leads/40 wire-end joints; these stock modules/looms are not factory BOM parts.

ROTATION REVIEW IS REQUIRED. bom.csv uses common JLC-shaped headings; bom-review
adds exact quantities/identities. cpl-manufacturer-review.csv preserves KiCad's
native millimetre position export, same auxiliary origin as Gerbers/drill.
BOTTOM X IS NOT NEGATED. Native exported Y can be negative. No extra mirroring,
Y inversion or package-specific angle correction has been applied. Native angles
are NOT a guarantee of the manufacturer's tape/feeder/pin1 convention.
placement-review.csv adds native pad1 coordinates relative to the auxiliary
origin, using native board XY (distinct from exported CPL Y), BOTTOM side,
exact MPN/LCSC, native angle and uncorrected CPL rotation. Review
all asymmetric components in the assembler's placement preview, especially QFNs,
PMOS switches, load switches, ESD/BC chips and diode polarity. Obtain the factory's
concrete placement/process review before production. No silent substitutions.

fabrication/ contains six actual Gerber X2 copper layers, both masks/silks, outline,
metric Excellon PTH/NPTH, drill map and Gerber job metadata. Its ZIP contains
fabrication files only. assembly/ adds paste Gerbers and factory CSVs. reports/
contains native DRC, exact board audit and actual drill statistics. source/ retains
the exact refilled/saved board used for these outputs plus project/schematic/rules
and local footprint libraries. source/3d/ includes the bundled model assets.
Every model referenced by the actual staged PCB must resolve through
${KIPRJMOD}/3d/ inside this snapshot; installed/global model fallbacks, absolute
paths and escaping relative paths are rejected. reports/3d-model-portability.json
records each reference/hash and explicitly lists footprints lacking a 3D model.
Absent models are not a claim of absent physical components. The repository
also retains generators, mechanical design, firmware and earlier source history.
The source canonical PCB was not modified. manifest.json links all inputs and
outputs to SHA256 hashes; a later change requires a fresh audit/export/quote.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=DEFAULT_BOARD)
    parser.add_argument('--spec', type=Path, default=DEFAULT_SPEC)
    parser.add_argument('--a1-reference', type=Path, default=DEFAULT_A1)
    parser.add_argument('--output', type=Path, default=B2 / 'manufacturing/B2_review')
    parser.add_argument('--cli', type=Path, default=CLI)
    args = parser.parse_args()
    source, output = args.board.resolve(), args.output.resolve()
    if output.exists():
        raise SystemExit('Refusing to overwrite existing review package: ' + str(output))
    wx.Log.EnableLogging(False)
    app = wx.App(False)
    severity_evidence = verify_default_severity_evidence()
    required = [source, args.spec.resolve(), args.a1_reference.resolve()]
    required += [DEFAULT_SEVERITY_EVIDENCE, OWNER_LED_EVIDENCE]
    required += [CAD / (STEM + suffix) for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru')]
    for folder in ('footprints',):
        required += sorted(p for p in (CAD / folder).rglob('*') if p.is_file())
    model_assets = sorted(p for p in (CAD / '3d').rglob('*') if p.is_file())
    if not model_assets:
        raise SystemExit('Missing bundled CAD/3d model assets')
    required += model_assets
    required += [p for p in (CAD / 'fp-lib-table', CAD / 'sym-lib-table', CAD / 'HouseRules_main.kicad_sym') if p.exists()]
    required += [Path(__file__).resolve(), Path(__file__).with_name('audit_board.py').resolve()]
    if not all(p.is_file() for p in required):
        raise SystemExit('Missing design input: ' + str([str(p) for p in required if not p.is_file()]))
    original = {str(p): digest(p) for p in required}
    try:
        with tempfile.TemporaryDirectory(prefix='house-rules-b2-manufacturing-') as tmp:
            stage = Path(tmp) / 'package'
            for name in ('source', 'fabrication', 'assembly', 'reports'):
                (stage / name).mkdir(parents=True)
            snap = stage / 'source'
            for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru'):
                shutil.copy2(CAD / (STEM + suffix), snap / (STEM + suffix))
            shutil.copy2(source, snap / (STEM + '.kicad_pcb'))
            for name in ('fp-lib-table', 'sym-lib-table', 'HouseRules_main.kicad_sym'):
                if (CAD / name).exists():
                    shutil.copy2(CAD / name, snap / name)
            shutil.copytree(CAD / 'footprints', snap / 'footprints')
            shutil.copytree(CAD / '3d', snap / '3d')
            project = json.loads((snap / (STEM + '.kicad_pro')).read_text())
            if exclusions_in_json(project):
                raise RuntimeError('Explicit DRC exclusions/ignored-rule overrides prevent export')
            if re.search(r'\(\s*severity\s+(?:ignore|ignored|exclusion)\b', (snap / (STEM + '.kicad_dru')).read_text(), re.I):
                raise RuntimeError('A custom-rule severity ignore/exclusion override prevents export')
            pcb = snap / (STEM + '.kicad_pcb')
            reports, fabrication, assembly = (stage / n for n in ('reports', 'fabrication', 'assembly'))
            shutil.copy2(DEFAULT_SEVERITY_EVIDENCE, reports / DEFAULT_SEVERITY_EVIDENCE.name)
            shutil.copy2(OWNER_LED_EVIDENCE, reports / OWNER_LED_EVIDENCE.name)
            drc = check_drc(args.cli, pcb, reports / 'native-drc.json', reports / 'native-drc.log')
            audit = audit_board(pcb, args.spec, args.a1_reference)
            (reports / 'board-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
            if audit['result'] != 'PASS':
                raise RuntimeError('Native board audit failed: ' + json.dumps(audit['errors'][:8]))
            model_portability = verify_model_references(pcb, snap,
                {str(p.relative_to(CAD)): original[str(p)] for p in model_assets})
            (reports / '3d-model-portability.json').write_text(json.dumps(model_portability, indent=2) + '\n')
            refilled_hash = digest(pcb)
            logs = []
            for label, command in [
                ('fabrication-gerbers', [args.cli, 'pcb', 'export', 'gerbers', '--layers',
                 ','.join(COPPER + ['F.Mask', 'B.Mask', 'F.SilkS', 'B.SilkS', 'Edge.Cuts']),
                 '--use-drill-file-origin', '--subtract-soldermask', '--output', str(fabrication) + '/', pcb]),
                ('drill', [args.cli, 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'plot',
                 '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal', '--excellon-separate-th',
                 '--excellon-oval-format', 'route', '--generate-map', '--map-format', 'svg', '--generate-report',
                 '--report-path', reports / 'native-drill-report.txt', '--output', str(fabrication) + '/', pcb]),
                ('assembly-paste', [args.cli, 'pcb', 'export', 'gerbers', '--layers', 'F.Paste,B.Paste',
                 '--use-drill-file-origin', '--output', str(assembly) + '/', pcb])]:
                logs.append({'stage': label, 'command': [str(s) for s in command]})
                (reports / (label + '.log')).write_text(run(command))
            functions = check_gerber_layers(fabrication)
            drills = drill_stats(fabrication, audit['via_count'])
            (reports / 'drill-statistics.json').write_text(json.dumps(drills, indent=2) + '\n')
            assembly_info = export_assembly(args.cli, pcb, assembly, audit)
            kicad_version = run([args.cli, '--version']).strip()
            removed_local_state = remove_staged_local_state(stage)
            if digest(pcb) != refilled_hash:
                raise RuntimeError('Staged PCB changed after DRC/audit; outputs cannot be tied to one board')
            (stage / 'README.md').write_text(README)
            with zipfile.ZipFile(stage / 'house-rules-main-B2-fabrication-REVIEW.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                for p in sorted(fabrication.iterdir()):
                    archive.write(p, p.name)
            if original != {str(p): digest(p) for p in required}:
                raise RuntimeError('Canonical design inputs changed during export; no package will be released')
            if model_assets != sorted(p for p in (CAD / '3d').rglob('*') if p.is_file()):
                raise RuntimeError('Canonical 3D asset inventory changed during export; no package will be released')
            manifest = {'status': 'REVIEW ONLY — NOT APPROVED FOR PRODUCTION',
                        'date_utc': datetime.now(timezone.utc).isoformat(),
                        'kicad_version': kicad_version,
                        'source_pcb_sha256': original[str(source)],
                        'refilled_saved_snapshot_sha256': refilled_hash,
                        'canonical_inputs_unchanged': True, 'input_sha256': original,
                        'drc': drc, 'audit': {n: audit[n] for n in ('result', 'component_count', 'factory_component_count',
                         'connected_pin_count', 'via_count', 'via_geometry_counts', 'thermal_vias', 'outline',
                         'ground_references', 'quiet_CT_In2_exception', 'drill_hole_edge_clearances')},
                        'native_default_severity_evidence': severity_evidence,
                        '3D_model_portability': model_portability,
                        'actual_gerber_file_functions': functions, 'actual_drill_statistics': drills,
                        'assembly': assembly_info, 'export_commands': logs,
                        'generated_staged_local_state_removed': removed_local_state,
                        'output_sha256': {str(p.relative_to(stage)): digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}}
            (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(stage, output)
    except Exception as exc:
        raise SystemExit('B2 export REFUSED; no review package created.\n' + str(exc))
    print('Review package: ' + str(output))
    print('Native DRC/parity0;82 references/55 factory/327 pins. Manufacturer rotation/process review remains required.')


if __name__ == '__main__':
    main()
