#!/usr/bin/env python3
"""Export review-only KiCad fabrication and assembly packages for both boards.

Run with KiCad's bundled Python (pcbnew + wx). This tool never uploads, orders,
changes the PCB or normalises its via types. It refuses native DRC errors,
non-through vias, missing factory MPN/LCSC data and PCB/spec inconsistencies.

The generated generic/JLC-shaped CPL is an uncorrected KiCad position export:
all package-specific feeder/pin-1 rotations require the assembler's review.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / 'hardware/kicad'
MAC_CLI = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
LAYERS = {
    'main': ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'],
    'usb': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
}
EXPECTED = {'main': {'layers': 6, 'thickness': 1.6},
            'usb': {'layers': 4, 'thickness': 1.0}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    result = subprocess.run([str(x) for x in command], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Command failed:\n' + ' '.join(map(str, command))
                           + '\n' + result.stdout)
    return result.stdout


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def natural(ref):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', ref)]


def excluded(ref):
    return ref.startswith('DS') or ref.startswith('TP')


def board_inventory(k, board, key, spec):
    expected = {p['ref']: p for p in spec['parts'] if p['board'] == key}
    actual = {f.GetReference(): f for f in board.GetFootprints()}
    if actual.keys() != expected.keys():
        raise RuntimeError(f'{key}: PCB/spec designators differ')
    layers = board.GetCopperLayerCount()
    thickness = k.ToMM(board.GetDesignSettings().GetBoardThickness())
    if layers != EXPECTED[key]['layers'] or abs(thickness - EXPECTED[key]['thickness']) > .001:
        raise RuntimeError(f'{key}: unexpected stack {layers} layers, {thickness} mm')
    origin = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = k.ToMM(origin.x), k.ToMM(origin.y)
    outline = k.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(outline, False) or outline.OutlineCount() != 1:
        raise RuntimeError(f'{key}: expected one closed board outline')
    bounds = outline.BBox()  # Polygon centreline; excludes Edge.Cuts stroke width.
    for actual_dim, target, label in (
            (k.ToMM(bounds.GetWidth()), spec['boards'][key]['width'], 'width'),
            (k.ToMM(bounds.GetHeight()), spec['boards'][key]['height'], 'height')):
        if abs(actual_dim - target) > .005:
            raise RuntimeError(f'{key}: outline {label} differs from circuit specification')
    inventory = {}
    for ref in sorted(actual, key=natural):
        fp = actual[ref]
        part = expected[ref]
        footprint = str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName())
        side = 'bottom' if fp.GetLayer() == k.B_Cu else 'top'
        if fp.GetValue() != part['value'] or footprint != part['footprint']:
            raise RuntimeError(f'{key}:{ref}: PCB value/footprint differs from circuit specification')
        if side != ('bottom' if part['side'] == 'B' else 'top'):
            raise RuntimeError(f'{key}:{ref}: PCB/spec mounting side differs')
        if (abs(k.ToMM(fp.GetX()) - ox - part['x']) > .005
                or abs(k.ToMM(fp.GetY()) - oy - part['y']) > .005):
            raise RuntimeError(f'{key}:{ref}: PCB/spec placement differs by more than 0.005 mm')
        mpn = fp.GetField('MPN').GetText()
        lcsc = fp.GetField('LCSC').GetText()
        if mpn != part.get('mpn', '') or lcsc != part.get('lcsc', ''):
            raise RuntimeError(f'{key}:{ref}: PCB/spec MPN or LCSC differs')
        for pad in fp.Pads():
            pin = pad.GetNumber()
            if pin in part['pins'] and part['pins'][pin]:
                if pad.GetNetname() != part['pins'][pin]:
                    raise RuntimeError(f'{key}:{ref}.{pin}: PCB/spec net differs')
        if not excluded(ref) and (not mpn or not re.fullmatch(r'C\d+', lcsc)):
            raise RuntimeError(f'{key}:{ref}: factory part lacks exact MPN/LCSC code')
        inventory[ref] = {
            'MPN': mpn, 'LCSC': lcsc, 'Value': fp.GetValue(),
            'Package': str(fp.GetFPID().GetLibItemName()), 'Side': side,
            'PCB_X_mm': f'{k.ToMM(fp.GetX()):.6f}',
            'PCB_Y_mm': f'{k.ToMM(fp.GetY()):.6f}',
            'PCB_angle_deg': f'{fp.GetOrientationDegrees():.6f}',
        }
    vias = [t for t in board.GetTracks() if isinstance(t, k.PCB_VIA)]
    non_through = [v for v in vias if v.GetViaType() != k.VIATYPE_THROUGH
                   or v.TopLayer() != k.F_Cu or v.BottomLayer() != k.B_Cu]
    if non_through:
        raise RuntimeError(f'{key}: {len(non_through)} native vias are not normal F.Cu-B.Cu THROUGH vias; '
                           'normalise the design and rerun final DRC before export. No HDI process is intended.')
    return inventory, {'layers': layers, 'thickness_mm': thickness,
                       'outline_mm': [k.ToMM(bounds.GetWidth()), k.ToMM(bounds.GetHeight())],
                       'aux_origin_mm': [ox, oy], 'native_through_vias': len(vias)}


def check_drc(cli, pcb, report):
    # Refill only in the DRC process's memory. Never pass --save-board.
    run([cli, 'pcb', 'drc', '--format', 'json', '--severity-all',
         '--schematic-parity', '--refill-zones', '--output', report, pcb])
    data = json.loads(report.read_text())
    errors = []
    for section in ('violations', 'unconnected_items', 'schematic_parity'):
        errors.extend(item for item in data.get(section, []) if item.get('severity') == 'error')
    if errors:
        preview = '\n'.join(str(e.get('description', e)) for e in errors[:8])
        raise RuntimeError(f'{pcb.name}: {len(errors)} DRC/parity/unconnected errors; export stopped.\n{preview}')
    return {section: len(data.get(section, [])) for section in
            ('violations', 'unconnected_items', 'schematic_parity')}


def export_assembly(cli, pcb, output, inventory):
    factory = {ref: p for ref, p in inventory.items() if not excluded(ref)}
    raw_path = output / 'positions-native-all.csv'
    # Do not negate bottom X: top and bottom share the same unmirrored XY system.
    # --exclude-fp-th is deliberately absent: USB shells have mechanical holes.
    run([cli, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
         '--side', 'both', '--use-drill-file-origin', '--smd-only',
         '--exclude-dnp', '--output', raw_path, pcb])
    with raw_path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if not {'Ref', 'PosX', 'PosY', 'Rot', 'Side'}.issubset(fields):
            raise RuntimeError(f'Unexpected KiCad position CSV headings: {fields}')
        rows = [r for r in reader if r['Ref'] in factory]
    found = [row['Ref'] for row in rows]
    if len(found) != len(set(found)) or set(found) != set(factory):
        raise RuntimeError('Native SMD position export did not contain every factory component exactly once')
    rows.sort(key=lambda row: natural(row['Ref']))
    write_csv(output / 'positions-native-factory.csv', fields, rows)
    # Remove unfiltered native file so owner-fit/testpoint positions are never
    # mistaken for a factory placement list. The boards themselves retain them.
    raw_path.unlink()
    cpl = []
    review = []
    for row in rows:
        ref, info = row['Ref'], factory[row['Ref']]
        side = row['Side'].strip().lower()
        if side not in ('top', 'bottom') or side != info['Side']:
            raise RuntimeError(f'{ref}: unexpected native position side {row["Side"]!r}')
        for field in ('PosX', 'PosY', 'Rot'):
            float(row[field])
        cpl.append({'Designator': ref, 'Mid X': row['PosX'] + 'mm',
                    'Mid Y': row['PosY'] + 'mm', 'Layer': side,
                    'Rotation': row['Rot']})
        review.append({'Designator': ref, **info, 'CPL_X_mm': row['PosX'],
                       'CPL_Y_mm': row['PosY'], 'CPL_rotation_deg': row['Rot']})
    write_csv(output / 'cpl-manufacturer-review.csv',
              ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'], cpl)
    write_csv(output / 'placement-review.csv',
              ['Designator', 'MPN', 'LCSC', 'Value', 'Package', 'Side',
               'PCB_X_mm', 'PCB_Y_mm', 'PCB_angle_deg',
               'CPL_X_mm', 'CPL_Y_mm', 'CPL_rotation_deg'], review)
    groups = collections.defaultdict(list)
    for ref, info in factory.items():
        groups[(info['MPN'], info['LCSC'], info['Value'], info['Package'])].append(ref)
    bom = [{'MPN': mpn, 'LCSC': code, 'Qty': len(refs),
            'Designators': ','.join(sorted(refs, key=natural)),
            'Value': value, 'Package': package}
           for (mpn, code, value, package), refs in groups.items()]
    bom.sort(key=lambda row: natural(row['Designators'].split(',')[0]))
    write_csv(output / 'bom.csv', ['MPN', 'LCSC', 'Qty', 'Designators', 'Value', 'Package'], bom)
    exclusions = [{'Designator': ref, 'Value': info['Value'],
                   'Reason': 'Owner supplied LED; fit after PCBA' if ref.startswith('DS')
                   else 'PCB test pad; no component to purchase or place'}
                  for ref, info in inventory.items() if excluded(ref)]
    write_csv(output / 'excluded-from-factory.csv', ['Designator', 'Value', 'Reason'], exclusions)
    return len(factory)


README = '''# Review-only manufacturing export — HOUSE RULES A1

These files were generated locally from the saved KiCad boards. No design was
uploaded and no order was placed. This package is an engineering prototype for
review; generating it does not authorise production or establish hardware tests.

Before buying/uploading: complete the owned LED pin/orientation and mechanical fit
tests, review current native DRC/ERC/parity reports, confirm the case and USB
harness, inspect Gerbers/drill in an independent viewer, and review the assembler's
component matches, pin-1 orientation, feeder rotations, stock and final quote.
The user must review the concrete final package/quote before an order is placed.
The internal cable must use plain JST SHR-06V-S mating housings at both ends;
the wider SHR-06V-S-B version is outside the reviewed mechanical envelope.

## Board and process choices to confirm with the fabricator

- Main: six copper layers, 88.4 x 17.3 mm nominal, 1.6 mm FR-4. In1.Cu is GND;
  In4.Cu is +5 V. F.Cu, In2.Cu, In3.Cu and B.Cu carry signal/fanout copper.
- USB carrier: four copper layers, 16.0 x 16.8 mm nominal, 1.0 mm FR-4. In1.Cu is GND.
- Use the fabricator's standard stack at these thicknesses, and 1 oz outer copper;
  confirm the inner-copper weight and actual dielectric stack. No controlled
  impedance has been specified or verified. Do not order 2 oz copper against the
  present fine-track layout.
- Main exposed-pad thermal vias require resin-filled, copper-capped via-in-pad
  processing (VIPPO/POFV), with a flat solderable surface; tenting alone is not
  equivalent inside an exposed pad. The same filled/capped treatment is needed for
  QFN signal-land vias and any other SMD-pad vias. Specify the main board's 0.2 mm drill
  vias for filling/capping, and have CAM confirm that all owned LED mounting holes
  remain open. JLC currently lists this via-in-pad
  process as standard/free for six or more layers; confirm it on the actual quote.
- All intended vias are ordinary F.Cu-B.Cu plated through vias. No blind, buried,
  laser or HDI vias are requested. Minimum via geometry is 0.4 mm pad / 0.2 mm drill.
  JLC notes that 0.2 mm drills below a 0.45 mm via pad may incur an extra fee.
  The tightly routed board must not be enlarged blindly to avoid that fee.
- Factory assembly must solder the USB socket's through-hole metal shell anchors as
  well as its SMT electrical contacts. The shell anchor holes remain open and are
  excluded from via-filling instructions, as are every owned LED mounting hole.
- Prefer a flat surface finish suitable for the 0.4 mm-pitch QFNs (e.g. ENIG), subject
  to the assembler's recommendation and quote. Fine silkscreen is below JLC's
  published 1 mm/0.15 mm readability guidance; use the assembly/programming diagram
  for BOOT, RESET, SWD and polarity identification.
- These narrow boards may require assembly rails/panel tooling chosen by the
  assembler. Do not change the final depanelised board outline or enlarge it beyond
  the LED silhouette. Confirm depanelisation tolerances and support before approval.
  Do not permit automatic tooling holes inside either finished board without a
  clearance review; the main LED mounting pads are close to its corners. Prefer
  tooling on removable rails where practical.

Sources checked 29 October 2026:
[JLC capabilities](https://jlcpcb.com/capabilities/pcb-),
[JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering),
[JLC via-in-pad process](https://jlcpcb.com/help/article/via-in-pad-pofv-guide),
[JLC board dimensions](https://jlcpcb.com/help/article/pcb-dimensions).
Public availability and pricing can change; no stock is reserved.

## Files and coordinate conventions

Each board has a fabrication folder containing Gerber X2 copper, soldermask,
silkscreen, outline, separate PTH/NPTH Excellon drill files and a drill map.
Native DRC and drill reports are in the board's reports folder.
The fabrication ZIP contains those files only. Paste Gerbers and factory BOM/CPL
are in the assembly folder. Gerber and drill exports use the same saved auxiliary
origin. No mirroring or Y inversion is added by this Python tool.

BOM columns are MPN, LCSC, Qty, Designators, Value, Package. Values and component
identities come from the actual PCB, cross-checked against circuit-spec.json.
DS1-DS7 and all TP pads are excluded from factory BOM/CPL; their mounting holes and
copper remain in fabrication Gerbers. Excluded parts/pads are listed separately.

positions-native-factory.csv preserves KiCad's own millimetre position/rotation
convention and top/bottom side labels. Both sides share the unmirrored placement
coordinate system, with the saved auxiliary origin and KiCad's exported Y axis.
The auxiliary origin is near the board's upper-left corner, so negative exported
Y coordinates are expected. Bottom X is NOT negated. The generic CPL candidate
uses the same values; no package-specific rotation corrections are applied.
placement-review.csv adds the native PCB centre/angle and exact component identity
for visual comparison. In particular, the main-board SMT parts are on BOTTOM and
the carrier SMT parts are on TOP. KiCad angles are not a guarantee of JLC or another
assembler's feeder orientation. Inspect every asymmetric part and pin-1 marker in
the manufacturer's placement preview, and obtain its approval before production.

The CPL has common JLC-shaped headings, but another vendor may require its own BOM,
CPL, layer naming, panel or rotation format. Do not silently transform bottom
coordinates/angles or accept automatic part substitutions. The manifest records
input and output hashes and DRC result counts so the exact package can be reviewed.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', type=Path, default=Path(shutil.which('kicad-cli') or MAC_CLI))
    parser.add_argument('--board', choices=['main', 'usb', 'all'], default='all')
    parser.add_argument('--output', type=Path, default=ROOT / 'hardware/manufacturing/A1_review')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f'Refusing to overwrite existing output: {output}; choose a new --output directory.')
    if not args.cli.is_file():
        raise SystemExit('KiCad CLI not found; pass --cli /path/to/kicad-cli')
    try:
        import wx
        wx.Log.EnableLogging(False)
        import pcbnew as k
    except ImportError as exc:
        raise SystemExit('Run with KiCad Python containing pcbnew and wx. On this Mac:\n'
                         '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 '
                         'hardware/tools/export_manufacturing.py') from exc
    app = wx.App(False)
    spec = json.loads((CAD / 'circuit-spec.json').read_text())
    chosen = ['main', 'usb'] if args.board == 'all' else [args.board]
    manifest = {'status': 'REVIEW ONLY — NOT APPROVED FOR ORDER',
                'kicad_version': run([args.cli, '--version']).strip(),
                'script_sha256': digest(Path(__file__).resolve()), 'boards': {}}
    inputs = [CAD / 'circuit-spec.json']
    for key in chosen:
        inputs.extend(CAD / f'house-rules-{key}.{ext}'
                      for ext in ('kicad_pcb', 'kicad_pro', 'kicad_sch', 'kicad_dru'))
    input_hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    # Build in a temporary directory; failed checks never leave a partial package
    # at the requested output path. No source PCB is saved or rewritten.
    with tempfile.TemporaryDirectory(prefix='house-rules-manufacturing-') as scratch:
        staged = Path(scratch) / 'package'
        staged.mkdir()
        (staged / 'README.md').write_text(README, encoding='utf-8')
        for key in chosen:
            pcb = CAD / f'house-rules-{key}.kicad_pcb'
            board = k.LoadBoard(str(pcb))
            inventory, detail = board_inventory(k, board, key, spec)
            dest = staged / key
            fabrication, assembly, reports = (dest / p for p in ('fabrication', 'assembly', 'reports'))
            for p in (fabrication, assembly, reports):
                p.mkdir(parents=True)
            detail['drc_counts'] = check_drc(args.cli, pcb, reports / 'native-drc.json')
            fabrication_layers = LAYERS[key] + ['F.Mask', 'B.Mask', 'F.SilkS', 'B.SilkS', 'Edge.Cuts']
            run([args.cli, 'pcb', 'export', 'gerbers', '--layers', ','.join(fabrication_layers),
                 '--use-drill-file-origin', '--subtract-soldermask', '--check-zones',
                 '--output', str(fabrication) + '/', pcb])
            run([args.cli, 'pcb', 'export', 'drill', '--format', 'excellon',
                 '--drill-origin', 'plot', '--excellon-units', 'mm',
                 '--excellon-zeros-format', 'decimal', '--excellon-separate-th',
                 '--excellon-oval-format', 'route', '--generate-map', '--map-format', 'pdf',
                 '--generate-report', '--report-path', reports / 'drill-report.txt',
                 '--output', str(fabrication) + '/', pcb])
            run([args.cli, 'pcb', 'export', 'gerbers', '--layers', 'F.Paste,B.Paste',
                 '--use-drill-file-origin', '--check-zones', '--output', str(assembly) + '/', pcb])
            detail['factory_component_count'] = export_assembly(args.cli, pcb, assembly, inventory)
            detail['factory_excluded'] = [r for r in inventory if excluded(r)]
            detail['copper_layers_top_to_bottom'] = LAYERS[key]
            manifest['boards'][key] = detail
            with zipfile.ZipFile(dest / f'house-rules-{key}-fabrication-REVIEW.zip', 'w',
                                 compression=zipfile.ZIP_DEFLATED) as archive:
                for p in sorted(fabrication.iterdir()):
                    archive.write(p, p.name)
        if input_hashes != {str(p.relative_to(ROOT)): digest(p) for p in inputs}:
            raise RuntimeError('Design inputs changed during export; rerun once edits have stopped.')
        manifest['input_sha256'] = input_hashes
        manifest['output_sha256'] = {str(p.relative_to(staged)): digest(p)
                                    for p in sorted(staged.rglob('*')) if p.is_file()}
        (staged / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, output)
    print(f'Review-only manufacturing package exported to {output}')
    print('No upload or order. Manufacturer rotation/part/process review and user approval remain required.')


if __name__ == '__main__':
    main()
