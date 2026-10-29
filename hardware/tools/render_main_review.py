#!/usr/bin/env python3
"""Render a read-only snapshot of the current main PCB using native KiCad.

Examples:
  python3 hardware/tools/render_main_review.py
  python3 hardware/tools/render_main_review.py --prefix main

The source board is never saved or edited. The bare-front copy hides only the
LED 3D models, leaving every footprint, pin-1 mark and copper pad intact.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
KICAD = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KICAD_MODELS = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'


def nodes(text):
    stack = []
    quoted = escaped = False
    found = []
    for i, c in enumerate(text):
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
            stack.append(i)
        elif c == ')':
            start = stack.pop()
            token = re.match(r'\(\s*([^\s()]+)', text[start:]).group(1)
            found.append((start, i + 1, token))
    if stack or quoted:
        raise ValueError('Incomplete KiCad source snapshot')
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prefix', default='main-review')
    ap.add_argument('--views', default='top,bottom,bare-front,edge')
    ap.add_argument('--width', type=int, default=1800)
    ap.add_argument('--height', type=int, default=600)
    a = ap.parse_args()
    source = ROOT / 'hardware/kicad/house-rules-main.kicad_pcb'
    original = source.read_text()
    checksum = hashlib.sha256(original.encode()).hexdigest()
    scratch = Path(tempfile.mkdtemp(prefix='house-rules-main-render-'))
    snapshot = original.replace('${KIPRJMOD}', str(source.parent))
    snapshot = snapshot.replace('${KICAD10_3DMODEL_DIR}', KICAD_MODELS)
    complete = scratch / 'house-rules-main.kicad_pcb'
    complete.write_text(snapshot)
    bare = snapshot
    for start, end, token in sorted(nodes(snapshot), reverse=True):
        if token == 'model' and 'LMD07057AUE-101B.wrl' in snapshot[start:end]:
            bare = bare[:start] + bare[end:]
    bare_path = scratch / 'house-rules-main-bare-front.kicad_pcb'
    bare_path.write_text(bare)
    output = ROOT / 'hardware/render'
    output.mkdir(exist_ok=True)

    def render(view):
        board = bare_path if view == 'bare-front' else complete
        side = {'top': 'top', 'bottom': 'bottom', 'bare-front': 'top',
                'edge': 'front'}[view]
        dest = output / f'{a.prefix}-{view}.png'
        command = [KICAD, 'pcb', 'render', str(board), '--output', str(dest),
                   '--width', str(a.width), '--height', str(a.height),
                   '--side', side, '--background', 'opaque', '--quality',
                   'high', '--zoom', '2.4', '--floor']
        result = subprocess.run(command, capture_output=True, text=True)
        (scratch / f'{view}.log').write_text(result.stdout + result.stderr)
        result.check_returncode()
        print(dest.relative_to(ROOT), flush=True)
        return {'view': view, 'file': str(dest.relative_to(ROOT)),
                'command': command, 'renderer_log': str(scratch / f'{view}.log')}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(render, a.views.split(',')))
    report = {'source_pcb_sha256': checksum, 'source': str(source),
              'snapshot_directory': str(scratch), 'renders': results,
              'source_board_untouched': True,
              'bare_front_note': 'Only LED model nodes removed in a temporary copy; pads and all other objects preserved.'}
    (ROOT / f'hardware/reports/{a.prefix}-render-source.json').write_text(
        json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
