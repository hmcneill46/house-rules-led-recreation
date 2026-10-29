#!/usr/bin/env python3
"""Read-only native KiCad audit for the final B2 carrier.

Run with KiCad's bundled Python (pcbnew + wx). No board, project or rules file
is written. Native DRC is a separate export gate; this audit checks represented
identity, connectivity, mechanics and the requested fabrication process.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

import pcbnew as k
import wx

B2 = Path(__file__).resolve().parents[1]
ROOT = B2.parents[2]
DEFAULT_BOARD = B2 / 'kicad/house-rules-main-B2.kicad_pcb'
DEFAULT_SPEC = B2 / 'electrical-spec.json'
DEFAULT_A1 = ROOT / 'hardware/kicad/house-rules-main.kicad_pcb'
DEFAULT_SEVERITY_EVIDENCE = B2 / 'reports/kicad-default-severity-audit.json'
COPPER = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
WIDE_NETS = {'VBUS', 'FUSED_VBUS', '+5V', '+3V3', 'SW_3V3', 'VLED_5V', 'GND'}
VERIFIED_NATIVE_DEFAULT_IGNORES = frozenset({
    'footprint_filters_mismatch', 'footprint_type_mismatch', 'missing_courtyard',
    'track_not_centered_on_via', 'tuning_profile_track_geometries'})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def natural(ref):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', ref)]


def field(fp, name):
    item = fp.GetField(name)
    return item.GetText() if item else ''


def verify_default_severity_evidence():
    """Require the separately captured pristine native KiCad default evidence."""
    data = json.loads(DEFAULT_SEVERITY_EVIDENCE.read_text())
    if data.get('native_version') != '10.0.7':
        raise RuntimeError('Native default-severity evidence version is unverified')
    if data.get('before_first_cli', {}).get('matching_project_exists') is not False:
        raise RuntimeError('Default-severity evidence did not start without a matching project')
    runs = data.get('runs', [])
    if not runs or runs[0].get('phase') != 'no-matching-project':
        raise RuntimeError('Pristine no-project default-severity evidence is missing')
    for run in runs:
        keys = {p['key'] for p in run['native_drc']['ignored_checks']}
        if keys != VERIFIED_NATIVE_DEFAULT_IGNORES:
            raise RuntimeError('Pristine native ignored checks differ from the reviewed five')
    return {'native_version': data['native_version'],
            'verified_default_ignored_checks': sorted(VERIFIED_NATIVE_DEFAULT_IGNORES),
            'evidence_path': str(DEFAULT_SEVERITY_EVIDENCE),
            'evidence_sha256': digest(DEFAULT_SEVERITY_EVIDENCE)}


def exclusions_in_json(data, path='', allowed_native_defaults=None):
    """Block overrides/exclusions while identifying five verified native defaults.

    Only the exact native "ignore" value in the board severity map is exempt.
    The allow-list is verified independently against pristine native DRC evidence.
    """
    found = []
    if isinstance(data, dict):
        for key, value in data.items():
            here = path + '/' + key
            if (key.endswith('_exclusions') or key.endswith('_exclusion_comments')) and value:
                found.append({'path': here, 'value': value})
            if key == 'rule_severities' and isinstance(value, dict):
                for name, severity in value.items():
                    if str(severity).lower() not in ('ignore', 'ignored', 'exclude'):
                        continue
                    record = {'path': here + '/' + name, 'value': severity}
                    if (here == '/board/design_settings/rule_severities'
                            and name in VERIFIED_NATIVE_DEFAULT_IGNORES and severity == 'ignore'):
                        if allowed_native_defaults is not None:
                            allowed_native_defaults.append(record)
                    else:
                        found.append(record)
            found.extend(exclusions_in_json(value, here, allowed_native_defaults))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(exclusions_in_json(value, path + '/' + str(index), allowed_native_defaults))
    return found


def effective_cover(via, settings):
    fm, cm = via.GetFillingMode(), via.GetCappingMode()
    filled = fm == k.FILLING_MODE_FILLED or (fm == k.FILLING_MODE_FROM_BOARD and settings.m_FillVias)
    capped = cm == k.CAPPING_MODE_CAPPED or (cm == k.CAPPING_MODE_FROM_BOARD and settings.m_CapVias)
    return bool(filled), bool(capped), int(fm), int(cm)


def led_geometry(board):
    origin = board.GetDesignSettings().GetAuxOrigin()
    result = {}
    for fp in board.GetFootprints():
        if not re.fullmatch(r'DS[1-7]', fp.GetReference()):
            continue
        for pad in fp.Pads():
            key = fp.GetReference() + '.' + pad.GetNumber()
            if key in result:
                raise ValueError('Duplicate LED terminal ' + key)
            point, size, drill = pad.GetPosition(), pad.GetSize(), pad.GetDrillSize()
            result[key] = {
                'relative_position_nm': [point.x - origin.x, point.y - origin.y],
                'pad_size_nm': [size.x, size.y], 'drill_nm': [drill.x, drill.y],
                'shape': int(pad.GetShape()), 'attribute': int(pad.GetAttribute()),
                'orientation_deg': pad.GetOrientationDegrees(),
                'filled': bool(pad.GetPrimaryDrillFilledFlag()),
                'capped': bool(pad.GetPrimaryDrillCappedFlag()),
            }
    return result


def measure_drill_gaps(via_holes, led_holes, units_per_mm=1):
    """Measure physical hole edges independently of copper nets/DRC exemptions.

    Input holes contain x/y/drill in common units plus optional identity fields.
    The same routine also verifies actual plotted Excellon coordinates.
    """
    result = {}
    for name, pairs, minimum in (
            ('via_to_LED_PTH', ((v, p) for v in via_holes for p in led_holes), .45),
            ('via_to_via', ((v, w) for i, v in enumerate(via_holes)
                            for w in via_holes[i + 1:]), .25)):
        closest, minimum_gap, failures = None, None, []
        for a, b in pairs:
            gap = (math.hypot(a['x'] - b['x'], a['y'] - b['y'])
                   - (a['drill'] + b['drill']) / 2) / units_per_mm
            if minimum_gap is None or gap < minimum_gap:
                minimum_gap, closest = gap, {'a': a, 'b': b}
            if gap < minimum - 1e-9:
                failures.append({'edge_gap_mm': gap, 'a': a, 'b': b})
        result[name] = {'required_edge_gap_mm': minimum,
                        'minimum_edge_gap_mm': minimum_gap,
                        'closest_pair': closest, 'coordinate_units_per_mm': units_per_mm,
                        'violation_count': len(failures), 'violations': failures,
                        'all_nets_including_same_net': True}
    return result


def audit_board(board_path=DEFAULT_BOARD, spec_path=DEFAULT_SPEC, a1_path=DEFAULT_A1):
    board_path, spec_path, a1_path = map(lambda p: Path(p).resolve(), (board_path, spec_path, a1_path))
    before = digest(board_path)
    board = k.LoadBoard(str(board_path))
    spec = json.loads(spec_path.read_text())
    severity_evidence = verify_default_severity_evidence()
    errors = []

    def require(condition, message, detail=None):
        if not condition:
            errors.append({'check': message, **({'detail': detail} if detail is not None else {})})

    expected = {p['ref']: p for p in spec['parts']}
    fps = list(board.GetFootprints())
    actual = {f.GetReference(): f for f in fps}
    factory = {r: p for r, p in expected.items() if p.get('assembly') == 'factory'}
    require(len(expected) == 82 and len(factory) == 55, 'Source must describe82 parts/55 factory parts')
    require(len(fps) == len(actual), 'PCB contains duplicate references')
    require(set(actual) == set(expected), 'PCB/source reference set parity',
            {'missing': sorted(set(expected) - set(actual)), 'extra': sorted(set(actual) - set(expected))})
    inventory, connected = {}, 0
    for ref in sorted(set(actual) & set(expected), key=natural):
        fp, part = actual[ref], expected[ref]
        footprint = str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName())
        observed = {'Value': fp.GetValue(), 'MPN': field(fp, 'MPN'), 'LCSC': field(fp, 'LCSC'),
                    'Footprint': footprint, 'Side': 'bottom' if fp.GetLayer() == k.B_Cu else 'top',
                    'PCB_X_mm': k.ToMM(fp.GetX()), 'PCB_Y_mm': k.ToMM(fp.GetY()),
                    'PCB_angle_deg': fp.GetOrientationDegrees(), 'Assembly': part.get('assembly')}
        pad1 = [p for p in fp.Pads() if p.GetNumber() == '1']
        require(len(pad1) == 1, ref + ': one physical pad1 required for orientation review')
        if len(pad1) == 1:
            o = board.GetDesignSettings().GetAuxOrigin(); position = pad1[0].GetPosition()
            observed['Pad1_native_relative_X_mm'] = k.ToMM(position.x - o.x)
            observed['Pad1_native_relative_Y_mm'] = k.ToMM(position.y - o.y)
        inventory[ref] = observed
        for name, value in [('Value', part['value']), ('MPN', part.get('mpn', '')),
                            ('LCSC', part.get('lcsc', '')), ('Footprint', part['footprint']),
                            ('Side', 'bottom' if part.get('side') == 'B' else 'top')]:
            require(observed[name] == value, ref + ': exact ' + name + ' parity',
                    {'expected': value, 'actual': observed[name]})
        if ref in factory:
            require(bool(observed['MPN']) and re.fullmatch(r'C\d+', observed['LCSC']) is not None,
                    ref + ': exact factory MPN/LCSC required')
            require(not fp.IsDNP(), ref + ': factory component must not be DNP')
        pads = list(fp.Pads())
        numbers = [p.GetNumber() for p in pads if p.GetNumber()]
        require(len(numbers) == len(set(numbers)), ref + ': duplicate numbered pads unsupported')
        require(set(numbers) == set(part['pins']), ref + ': exact physical pin-number set parity')
        for pad in pads:
            number = pad.GetNumber()
            if not number or number not in part['pins']:
                continue
            n, wanted = pad.GetNetname(), part['pins'][number]
            if wanted is None:
                require(not n or n.startswith('unconnected-'), ref + '.' + number + ': intentional NC became connected', n)
            else:
                connected += 1
                require(n == wanted, ref + '.' + number + ': exact net parity', {'expected': wanted, 'actual': n})
    require(connected == 327, 'Exactly327 represented connected component pins required', connected)

    ds = board.GetDesignSettings()
    require(board.GetCopperLayerCount() == 6, 'Exactly six copper layers required')
    require(ds.GetBoardThickness() == k.FromMM(1.6), 'Exactly1.6mm board thickness required')
    outline = k.SHAPE_POLY_SET()
    outlines_ok = board.GetBoardPolygonOutlines(outline, False)
    require(bool(outlines_ok) and outline.OutlineCount() == 1, 'One closed board outline required')
    outline_report = {}
    if outlines_ok and outline.OutlineCount() == 1:
        bounds = outline.BBox()
        require(bounds.GetWidth() == k.FromMM(88.4) and bounds.GetHeight() == k.FromMM(17.3),
                'Exact88.4x17.3mm outline centreline required')
        require(outline.HoleCount(0) == 0, 'No internal milled/tooling holes allowed')
        outline_report = {'width_mm': k.ToMM(bounds.GetWidth()), 'height_mm': k.ToMM(bounds.GetHeight()),
                          'holes': outline.HoleCount(0)}
    a1 = k.LoadBoard(str(a1_path))
    leds, reference_leds = led_geometry(board), led_geometry(a1)
    require(len(leds) == len(reference_leds) == 84, 'Exactly84 LED PTH terminals required')
    led_diffs = {r: {'a1': reference_leds.get(r), 'b2': leds.get(r)}
                 for r in sorted(set(leds) | set(reference_leds)) if leds.get(r) != reference_leds.get(r)}
    require(not led_diffs, 'LED coordinates/drills/pad size/orientation exactly match frozen A1 relative to auxiliary origin', led_diffs)
    require(all(v['drill_nm'] == [900000, 900000] and v['pad_size_nm'] == [1400000, 1400000]
                and not v['filled'] and not v['capped'] for v in leds.values()),
            'All84 LED0.9mm holes/1.4mm pads remain open and uncapped')
    drilled_pads = [{'ref': f.GetReference(), 'pad': p.GetNumber(),
                     'drill_mm': [k.ToMM(p.GetDrillSize().x), k.ToMM(p.GetDrillSize().y)]}
                    for f in fps for p in f.Pads() if p.GetDrillSize().x or p.GetDrillSize().y]
    require(len(drilled_pads) == 84 and all(re.fullmatch(r'DS[1-7]', p['ref']) for p in drilled_pads),
            'Only the84 LED holes may be footprint drills; no finished-board tooling holes', drilled_pads)

    vias = [v for v in board.GetTracks() if isinstance(v, k.PCB_VIA)]
    via_rows, via_sizes = [], Counter()
    for via in vias:
        filled, capped, fm, cm = effective_cover(via, ds)
        size = via.GetWidth(k.F_Cu); drill = via.GetDrillValue()
        via_sizes[(size, drill)] += 1
        good = (via.GetViaType() == k.VIATYPE_THROUGH and via.TopLayer() == k.F_Cu
                and via.BottomLayer() == k.B_Cu and drill == 300000
                and size in (450000, 600000) and filled and capped
                and all(via.GetWidth(board.GetLayerID(layer)) == size for layer in COPPER))
        row = {'x_mm': k.ToMM(via.GetX()), 'y_mm': k.ToMM(via.GetY()), 'net': via.GetNetname(),
               'pad_mm': k.ToMM(size), 'drill_mm': k.ToMM(drill), 'filled': filled, 'capped': capped,
               'filling_mode': fm, 'capping_mode': cm}
        via_rows.append(row)
        require(good, 'Every via must be F-B through,0.3mm drill,0.45/0.6mm pad, effectively filled+capped', row)
    require(bool(vias), 'Routed board requires through vias')
    via_holes = [{'x': v.GetX(), 'y': v.GetY(), 'drill': v.GetDrillValue(),
                  'net': v.GetNetname()} for v in vias]
    led_holes = [{'x': p.GetPosition().x, 'y': p.GetPosition().y,
                  'drill': p.GetDrillSize().x, 'ref': f.GetReference(),
                  'pad': p.GetNumber(), 'net': p.GetNetname()}
                 for f in fps if re.fullmatch(r'DS[1-7]', f.GetReference()) for p in f.Pads()]
    hole_clearances = measure_drill_gaps(via_holes, led_holes, units_per_mm=1000000)
    for name, measurement in hole_clearances.items():
        require(measurement['violation_count'] == 0,
                name + ': physical drill-edge clearance, including same-net holes', measurement)
    thermal = {}
    for ref in ('U1', 'U2', 'U3', 'U4'):
        if ref not in actual:
            continue
        ep = next((p for p in actual[ref].Pads() if p.GetNumber() == '25'), None)
        require(ep is not None, ref + ': exposed pad25 required')
        if ep is None:
            continue
        bb = ep.GetBoundingBox()
        inside = []
        for via in vias:
            p = via.GetPosition(); radius = via.GetWidth(k.F_Cu) / 2
            if bb.GetX() <= p.x <= bb.GetRight() and bb.GetY() <= p.y <= bb.GetBottom():
                inside.append(via)
                require(p.x - radius >= bb.GetX() and p.x + radius <= bb.GetRight()
                        and p.y - radius >= bb.GetY() and p.y + radius <= bb.GetBottom()
                        and via.GetNetname() == 'GND', ref + ': thermal via pad must lie wholly in EP25 and be GND')
        thermal[ref] = [{'x_mm': k.ToMM(v.GetX()), 'y_mm': k.ToMM(v.GetY())} for v in inside]
        require(len(inside) == 3, ref + ': exactly three exposed-pad thermal vias required', thermal[ref])
    require(sum(len(v) for v in thermal.values()) == 12, 'Exactly12 exposed-pad thermal vias required')

    track_sizes, power_sizes = Counter(), Counter()
    foreign_plane_tracks, quiet_ct_tracks = [], []
    for track in board.GetTracks():
        if isinstance(track, k.PCB_VIA):
            continue
        width, net = track.GetWidth(), track.GetNetname()
        track_sizes[width] += 1
        wide = net in WIDE_NETS or re.fullmatch(r'COL[1-5]_A', net) is not None
        if wide:
            power_sizes[width] += 1
        require(width >= (150000 if wide else 110000), 'Minimum track width0.11mm; power/anodes0.15mm',
                {'net': net, 'width_mm': k.ToMM(width), 'layer': k.LayerName(track.GetLayer())})
        if track.GetLayer() == k.In2_Cu and net == 'CT_5V':
            quiet_ct_tracks.append({'length_mm': track.GetLength() / 1e6,
                'start_mm': [k.ToMM(track.GetStart().x), k.ToMM(track.GetStart().y)],
                'end_mm': [k.ToMM(track.GetEnd().x), k.ToMM(track.GetEnd().y)],
                'width_mm': k.ToMM(width)})
        elif track.GetLayer() in (k.In2_Cu, k.In4_Cu) and net != 'GND':
            foreign_plane_tracks.append({'net': net, 'layer': k.LayerName(track.GetLayer())})
    require(not foreign_plane_tracks,
            'In4 must be GND-only; In2 permits only the short CT_5V timing-capacitor exception', foreign_plane_tracks)
    ct_length = sum(t['length_mm'] for t in quiet_ct_tracks)
    require(ct_length <= 12.0 + 1e-9, 'In2 CT_5V exception must total no more than12mm', ct_length)
    plane_exception = {'net': 'CT_5V', 'layer': 'In2.Cu', 'used': bool(quiet_ct_tracks),
        'maximum_total_track_length_mm': 12.0, 'actual_total_track_length_mm': ct_length,
        'track_count': len(quiet_ct_tracks), 'tracks': quiet_ct_tracks,
        'reason': 'Quiet load-switch timing-capacitor connection only; four signal-layer escape was closed. No USB, clocks or other signal exception.',
        'In4_remains_GND_only': not any(t['layer'] == 'In4.Cu' for t in foreign_plane_tracks)}
    plane_report = {}
    for layer in (k.In2_Cu, k.In4_Cu):
        zones = [z for z in board.Zones() if z.GetLayer() == layer]
        grounds = [z for z in zones if z.GetNetname() == 'GND']
        require(bool(grounds) and len(grounds) == len(zones), k.LayerName(layer) + ': GND reference zones only')
        area = sum(z.GetFilledPolysList(layer).Area() / 1e12 for z in grounds)
        outlines = sum(z.GetFilledPolysList(layer).OutlineCount() for z in grounds)
        require(area > 88.4 * 17.3 * .5, k.LayerName(layer) + ': saved GND fill must cover at least half the board area', area)
        if layer == k.In2_Cu and quiet_ct_tracks:
            require(outlines == 1, 'In2 GND fill must remain one connected filled outline around CT bridge', outlines)
        plane_report[k.LayerName(layer)] = {'ground_zones': len(grounds), 'filled_area_mm2': round(area, 6),
                                           'connected_fill_outlines': outlines}

    project = board_path.with_suffix('.kicad_pro')
    native_default_ignores = []
    project_exclusions = exclusions_in_json(json.loads(project.read_text()),
        allowed_native_defaults=native_default_ignores) if project.exists() else []
    require(not project_exclusions, 'No explicit DRC exclusions or non-default ignored-rule overrides', project_exclusions)
    rules_file = board_path.with_suffix('.kicad_dru')
    ignored_rules = bool(rules_file.exists() and re.search(r'\(\s*severity\s+(?:ignore|ignored|exclusion)\b', rules_file.read_text(), re.I))
    require(not ignored_rules, 'No custom-rule severity ignore/exclusion overrides')
    require(not ds.m_DrcExclusions, 'No native DRC exclusions')
    require(digest(board_path) == before, 'Source PCB changed during read-only audit')
    return {
        'result': 'PASS' if not errors else 'FAIL', 'date_utc': datetime.now(timezone.utc).isoformat(),
        'board': str(board_path), 'board_sha256': before, 'spec_sha256': digest(spec_path),
        'a1_led_reference': str(a1_path), 'a1_led_reference_sha256': digest(a1_path),
        'audit_script_sha256': digest(Path(__file__)), 'error_count': len(errors), 'errors': errors,
        'component_count': len(fps), 'factory_component_count': len(factory), 'connected_pin_count': connected,
        'copper_layers_top_to_bottom': COPPER, 'native_copper_layer_count': board.GetCopperLayerCount(),
        'thickness_mm': k.ToMM(ds.GetBoardThickness()), 'outline': outline_report,
        'aux_origin_mm': [k.ToMM(ds.GetAuxOrigin().x), k.ToMM(ds.GetAuxOrigin().y)],
        'exact_A1_LED_geometry_matches': not led_diffs, 'LED_holes_open': len(leds) == 84 and all(not d['filled'] and not d['capped'] for d in leds.values()),
        'LED_geometry': leds, 'via_count': len(vias),
        'via_geometry_counts': [{'pad_mm': k.ToMM(w), 'drill_mm': k.ToMM(d), 'count': n}
                                for (w, d), n in sorted(via_sizes.items())],
        'thermal_vias': thermal, 'via_inventory': via_rows,
        'drill_hole_edge_clearances': hole_clearances,
        'track_width_counts': {f'{k.ToMM(w):.6f}': n for w, n in sorted(track_sizes.items())},
        'power_anode_track_width_counts': {f'{k.ToMM(w):.6f}': n for w, n in sorted(power_sizes.items())},
        'ground_references': plane_report, 'project_exclusions': project_exclusions,
        'quiet_CT_In2_exception': plane_exception,
        'serialized_native_default_ignored_checks': native_default_ignores,
        'native_default_severity_evidence': severity_evidence,
        'inventory': inventory,
        'scope': 'Native represented identity/pins/geometry/process flags only. Does not certify analog behavior, actual fabrication, USB compliance or assembly rotations. Fresh native DRC/parity is additionally required.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=DEFAULT_BOARD)
    parser.add_argument('--spec', type=Path, default=DEFAULT_SPEC)
    parser.add_argument('--a1-reference', type=Path, default=DEFAULT_A1)
    parser.add_argument('--output', type=Path, default=B2 / 'reports/board-audit.json')
    args = parser.parse_args()
    wx.Log.EnableLogging(False)
    app = wx.App(False)
    report = audit_board(args.board, args.spec, args.a1_reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({n: report[n] for n in ('result', 'board_sha256', 'error_count', 'component_count', 'factory_component_count', 'connected_pin_count', 'via_count')}, indent=2))
    if report['errors']:
        print(json.dumps(report['errors'][:8], indent=2))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
