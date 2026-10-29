#!/usr/bin/env python3
"""Render the actual B2 board using KiCad; never save or edit its source.

The bare-front preview removes LED model nodes only in a disposable snapshot.
Copper, holes, footprints, pin orientation and the manufacturing source survive
unchanged. These are CAD images of unbuilt hardware, not photographs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

B2 = Path(__file__).resolve().parents[1]
ROOT = B2.parents[2]
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--views', default='top,bottom,bare-front')
    args = parser.parse_args()
    views = args.views.split(',')
    assert set(views) <= {'top', 'bottom', 'bare-front'}
    source = B2 / 'kicad/house-rules-main-B2.kicad_pcb'
    before = source.read_bytes()
    module_spec = importlib.util.spec_from_file_location('a1_render_parser', ROOT / 'hardware/tools/render_main_review.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    out = B2 / 'render'
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='house-rules-b2-render-') as directory:
        temporary = Path(directory)
        snapshot = before.decode().replace('${KIPRJMOD}', str(source.parent))
        snapshot = snapshot.replace('${KICAD10_3DMODEL_DIR}', LIB)
        complete = temporary / 'main.kicad_pcb'
        complete.write_text(snapshot)
        bare = snapshot
        for start, end, token in sorted(module.nodes(snapshot), reverse=True):
            if token == 'model' and 'LMD07057AUE-101B.wrl' in snapshot[start:end]:
                bare = bare[:start] + bare[end:]
        bare_file = temporary / 'bare.kicad_pcb'
        bare_file.write_text(bare)

        def render(view):
            pcb = bare_file if view == 'bare-front' else complete
            image = out / ('main-' + view + '.png')
            command = [CLI, 'pcb', 'render', str(pcb), '--output', str(image),
                       '--width', '1800', '--height', '600', '--side',
                       'bottom' if view == 'bottom' else 'top', '--background',
                       'opaque', '--quality', 'high', '--zoom', '2.4', '--floor']
            result = subprocess.run(command, capture_output=True, text=True)
            (out / (view + '.log')).write_text(result.stdout + result.stderr)
            result.check_returncode()
            print(image, flush=True)
            return {'view': view, 'file': str(image.relative_to(B2)),
                    'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                    'command': command}

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(render, views))
    assert source.read_bytes() == before
    report = {'source': str(source.relative_to(B2)),
              'source_sha256': hashlib.sha256(before).hexdigest(),
              'native_renderer': 'KiCad CLI10; actual model/board snapshot',
              'source_board_untouched': True,
              'bare_front': 'LED 3D models hidden only in disposable snapshot; no geometry or fabrication changes',
              'renders': results}
    (B2 / 'reports/render-source.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
