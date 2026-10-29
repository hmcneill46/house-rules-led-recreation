#!/usr/bin/env python3
"""Complete the two remaining carrier connections after the recorded SES import.

Run with KiCad's bundled Python. Locked USB traces and existing routing stay in
place. Native KiCad DRC and schematic/net parity are required after running.
"""
import json
import re
import uuid
from pathlib import Path
import wx
import pcbnew as k

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'hardware/kicad'
PCB = OUT / 'house-rules-usb.kicad_pcb'
app = wx.App(False)


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'house-rules:usb:routing-finish:' + key))


def remove_own_items():
    """Filter top-level expressions instead of unsafe SWIG Remove wrappers."""
    source = PCB.read_text()
    ids = {uid('cc2-bridge'), uid('vbus-escape-a'), uid('vbus-escape-b'),
           uid('vbus-escape-c'), uid('vbus-via-a'), uid('vbus-via-b'),
           uid('vbus-inner-a'), uid('vbus-inner-b'), uid('vbus-join')}
    # The old autorouter via has no second-layer connection and serves no route.
    ids.add('ddfa53a5-0706-4c1a-a2ff-cfa4921a894e')
    spans = []
    depth = 0
    quoted = escaped = False
    start = None
    for i, c in enumerate(source):
        if quoted:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == '(':
            if depth == 1:
                start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 1 and start is not None:
                block = source[start:i + 1]
                if any(f'(uuid "{v}")' in block for v in ids):
                    spans.append((start, i + 1))
                start = None
    for a, z in reversed(spans):
        source = source[:a] + source[z:]
    PCB.write_text(source)


def main():
    remove_own_items()
    b = k.LoadBoard(str(PCB))

    def pt(p):
        return k.VECTOR2I(k.FromMM(p[0] + 50), k.FromMM(p[1] + 50))

    def seg(key, net, a, z, layer=k.F_Cu, width=.15):
        t = k.PCB_TRACK(b)
        t.SetStart(pt(a)); t.SetEnd(pt(z)); t.SetLayer(layer)
        t.SetWidth(k.FromMM(width)); t.SetNet(b.FindNet(net))
        t.SetLocked(True); t.SetUuid(k.KIID(uid(key))); b.Add(t)

    def via(key, net, p):
        v = k.PCB_VIA(b)
        v.SetPosition(pt(p)); v.SetViaType(k.VIATYPE_THROUGH)
        v.SetLayerPair(k.F_Cu, k.B_Cu)
        v.SetWidth(k.FromMM(.4)); v.SetDrill(k.FromMM(.2))
        v.SetNet(b.FindNet(net)); v.SetLocked(True)
        v.SetUuid(k.KIID(uid(key))); b.Add(v)

    # ESD CC2 opposite pad joins the already routed header/Rd/USB CC2 net.
    seg('cc2-bridge', 'CC2', (7.0, 7.985), (5.2904, 7.985))
    # VBUS escapes north of the left contact group, avoiding the NPTH peg.
    seg('vbus-escape-a', 'VBUS', (8.3, 10.02), (8.3, 9.55), width=.2)
    seg('vbus-escape-b', 'VBUS', (8.3, 9.55), (8.2, 9.45), width=.2)
    seg('vbus-escape-c', 'VBUS', (8.2, 9.45), (8.2, 9.15), width=.2)
    via('vbus-via-a', 'VBUS', (8.2, 9.15))
    via('vbus-via-b', 'VBUS', (13.1, 8.9))
    seg('vbus-inner-a', 'VBUS', (8.2, 9.15), (12.85, 9.15), k.In1_Cu, .3)
    seg('vbus-inner-b', 'VBUS', (12.85, 9.15), (13.1, 8.9), k.In1_Cu, .3)
    seg('vbus-join', 'VBUS', (13.1, 8.9), (13.1, 8.1735), width=.2)

    for drawing in b.GetDrawings():
        if isinstance(drawing, k.PCB_TEXT) and drawing.GetText() == 'USB 5V':
            drawing.SetPosition(pt((10, 1.0)))

    spec = json.loads((OUT / 'circuit-spec.json').read_text())
    parts = {p['ref']: p for p in spec['parts'] if p['board'] == 'usb'}
    for f in b.GetFootprints():
        p = parts[f.GetReference()]
        lib, fp = p['footprint'].split(':')
        f.SetFPID(k.LIB_ID(lib, fp))
        for key, value in [('MPN', p['mpn']), ('LCSC', p.get('lcsc', '')),
                           ('Datasheet', p.get('datasheet', '')),
                           ('Description', p.get('role', ''))]:
            f.SetField(key, value); f.GetField(key).SetVisible(False)
    b.BuildConnectivity()
    k.ZONE_FILLER(b).Fill(b.Zones())
    k.SaveBoard(str(PCB), b)
    k.ExportSpecctraDSN(b, str(OUT / 'house-rules-usb.dsn'))
    print('Finished carrier CC2 and VBUS, moved rear silk; native DRC still required.')


if __name__ == '__main__':
    main()
