#!/usr/bin/env python3
"""Promote an explicitly chosen routed candidate; add no electrical copper.

This refreshes part metadata, bundles existing 3D models and prints wire-group
anchor numbers. A fresh independent native DRC and electrical audit are still
mandatory after running this script. It is not a manufacturing approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import wx
import pcbnew as k

B2 = Path(__file__).resolve().parents[1]
CAD = B2 / 'kicad'
MODELS = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    app = wx.App(False)
    source = args.input.resolve()
    target = CAD / 'house-rules-main-B2.kicad_pcb'
    assert source != target.resolve(), 'Choose a separate candidate for promotion'
    board = k.LoadBoard(str(source))
    assert board.GetCopperLayerCount() == 6
    spec = json.loads((B2 / 'electrical-spec.json').read_text())
    actual = {f.GetReference(): f for f in board.GetFootprints()}
    assert set(actual) == {p['ref'] for p in spec['parts']}
    copper_before = len(board.GetTracks())
    # KiCad assigns one-terminal names to intentional no-connect pins. Carry
    # those exact schematic names into the PCB without adding any copper.
    nc_nodes = {}
    for net in ET.parse(B2 / 'reports/schematic.net.xml').findall('.//nets/net'):
        if net.attrib['name'].startswith('unconnected-'):
            nodes = net.findall('node')
            assert len(nodes) == 1
            node = nodes[0]
            nc_nodes[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name']
    nets = {n.GetNetname(): n for n in board.GetNetInfo().NetsByNetcode().values()}
    for name in set(nc_nodes.values()):
        if name not in nets:
            net = k.NETINFO_ITEM(board, name)
            board.Add(net)
            nets[name] = net
    models = []
    for part in spec['parts']:
        footprint = actual[part['ref']]
        footprint.SetValue(part['value'])
        footprint.Value().SetVisible(False)
        for name, value in [('MPN', part.get('mpn', '')), ('LCSC', part.get('lcsc', '')),
                            ('Datasheet', part.get('datasheet', '')),
                            ('Description', part.get('role', ''))]:
            footprint.SetField(name, value)
            footprint.GetField(name).SetVisible(False)
        for pad in footprint.Pads():
            key = (part['ref'], pad.GetNumber())
            if key in nc_nodes:
                assert not part['pins'][pad.GetNumber()]
                assert not pad.GetNetname() or pad.GetNetname().startswith('unconnected-')
                pad.SetNet(nets[nc_nodes[key]])
        updated_models = []
        for model in footprint.Models():
            raw = model.m_Filename
            # The placement seed used a removed generic model name. Use the
            # installed model for the exact TI RGE0024C package instead.
            if part['footprint'] == 'TI:RGE0024C':
                raw = '${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm.step'
            elif part['ref'] == 'U9':
                raw = '${KIPRJMOD}/3d/TI_RSE0010A-envelope.wrl'
            candidates = []
            if '${KIPRJMOD}' in raw:
                candidates.extend([Path(raw.replace('${KIPRJMOD}', str(CAD))),
                                   Path(raw.replace('${KIPRJMOD}', str(source.parent)))])
            candidates.append(Path(raw.replace('${KICAD10_3DMODEL_DIR}', str(MODELS))))
            resolved = next((p for p in candidates if p.is_file()), None)
            if resolved is None:
                raise ValueError(f'Missing 3D model for {part["ref"]}: {raw}')
            if resolved.parent == CAD / '3d':
                bundled = resolved
            else:
                bundled = CAD / '3d' / (part['footprint'].split(':')[0] + '__' + resolved.name)
                if bundled.exists():
                    assert bundled.read_bytes() == resolved.read_bytes(), bundled
                else:
                    shutil.copy2(resolved, bundled)
            model.m_Filename = '${KIPRJMOD}/3d/' + bundled.name
            updated_models.append(model)
            models.append({'reference': part['ref'], 'file': str(bundled.relative_to(CAD)),
                           'sha256': hashlib.sha256(bundled.read_bytes()).hexdigest()})
        # SWIG returns model values when iterating the vector. Replace the
        # vector explicitly; assigning a field on an iterated value is lost.
        footprint.Models().clear()
        for model in updated_models:
            footprint.Models().push_back(model)
    origin = board.GetDesignSettings().GetAuxOrigin()
    anchors = [('1', 32.1), ('12', 64.1), ('13', 67.1),
               ('18', 84.55), ('19', 21.2), ('20', 28.7)]
    for drawing in list(board.GetDrawings()):
        if not isinstance(drawing, k.PCB_TEXT):
            continue
        if drawing.GetText() == 'HOUSE RULES B2':
            drawing.SetTextSize(k.VECTOR2I(k.FromMM(1), k.FromMM(1)))
            drawing.SetTextThickness(k.FromMM(.15))
            drawing.SetPosition(k.VECTOR2I(origin.x + k.FromMM(16), origin.y + k.FromMM(16.55)))
        elif drawing.GetLayer() == k.B_SilkS and drawing.GetText() in {a[0] for a in anchors}:
            board.Remove(drawing)
    for label, x in anchors:
        text = k.PCB_TEXT(board)
        text.SetText(label)
        text.SetLayer(k.B_SilkS)
        text.SetMirrored(True)
        text.SetTextSize(k.VECTOR2I(k.FromMM(1), k.FromMM(1)))
        text.SetTextThickness(k.FromMM(.15))
        text.SetPosition(k.VECTOR2I(origin.x + k.FromMM(x), origin.y + k.FromMM(.85)))
        board.Add(text)
    via_count = 0
    for item in board.GetTracks():
        if not isinstance(item, k.PCB_VIA):
            continue
        assert item.TopLayer() == k.F_Cu and item.BottomLayer() == k.B_Cu
        assert abs(k.ToMM(item.GetDrillValue()) - .30) < .000001
        assert min(abs(k.ToMM(item.GetWidth(k.F_Cu)) - d) for d in (.45, .60)) < .000001
        item.SetViaType(k.VIATYPE_THROUGH)
        item.SetDrill(k.FromMM(.30))
        item.SetFillingMode(k.FILLING_MODE_FILLED)
        item.SetCappingMode(k.CAPPING_MODE_CAPPED)
        item.SetFrontTentingMode(k.TENTING_MODE_TENTED)
        item.SetBackTentingMode(k.TENTING_MODE_TENTED)
        via_count += 1
    assert len(board.GetTracks()) == copper_before
    for extension in ('.kicad_pro', '.kicad_dru'):
        setting = source.with_suffix(extension)
        assert setting.is_file(), f'Candidate settings are required: {setting}'
        shutil.copy2(setting, target.with_suffix(extension))
    project_path = target.with_suffix('.kicad_pro')
    project_data = json.loads(project_path.read_text())
    project_rules = project_data['board']['design_settings']['rules']
    project_rules.update({'min_hole_clearance': .20, 'min_via_diameter': .45,
                          'min_via_annular_width': .075, 'min_through_hole_diameter': .30})
    power_nets = ['VBUS', 'FUSED_VBUS', '+5V', '+3V3', 'SW_3V3', 'VLED_5V', 'GND'] + \
        ['COL' + str(i) + '_A' for i in range(1, 6)]
    patterns = project_data['net_settings'].setdefault('netclass_patterns', [])
    for net in power_nets:
        patterns[:] = [p for p in patterns if p.get('pattern') != net]
        patterns.append({'netclass': 'Power', 'pattern': net})
    project_path.write_text(json.dumps(project_data, indent=2) + '\n')
    rules_path = target.with_suffix('.kicad_dru')
    rules_text = rules_path.read_text()
    if 'Power neck minimum' not in rules_text:
        condition = ' || '.join("A.NetName == '" + net + "'" for net in power_nets)
        rules_text += '\n(rule "Power neck minimum" (condition "' + condition + \
            '") (constraint track_width (min 0.15mm)))\n'
        rules_path.write_text(rules_text)
    board.GetDesignSettings().m_HoleClearance = k.FromMM(.20)
    board.BuildConnectivity()
    k.SaveBoard(str(target), board)
    report = {'status': 'promoted for independent final verification, not a production approval',
              'input': str(source.relative_to(B2)),
              'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'output': str(target.relative_to(B2)),
              'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
              'electrical_spec_sha256': hashlib.sha256((B2 / 'electrical-spec.json').read_bytes()).hexdigest(),
              'copper_objects_unchanged': copper_before,
              'intentional_no_connect_pads_named_from_native_schematic': len(nc_nodes),
              'explicitly_filled_capped_through_vias': via_count,
              'wire_group_anchor_numbers': [a[0] for a in anchors],
              'bundled_models': models}
    (B2 / 'reports/finalization.json').write_text(json.dumps(report, indent=2) + '\n')
    print(target)


if __name__ == '__main__':
    main()
