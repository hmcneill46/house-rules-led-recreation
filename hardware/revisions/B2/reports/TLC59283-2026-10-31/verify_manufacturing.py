#!/usr/bin/env python3
"""Inspect actual new Gerber/drill/BOM/CPL outputs; do not edit design files.

Reuse the independently reviewed confirmed-F output parser, then compare the
new fabrication commands to that frozen package with timestamps alone removed.
Run with KiCad's bundled Python. This does not approve factory rotations/CAM.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pcbnew as k
import wx

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]
OLD = B2 / 'manufacturing/B2_F_12p875_review_2026-10-31'
NEW = B2 / 'manufacturing/B2_F_TLC59283_7p15k_review_2026-10-31'
BOARD = B2 / 'kicad/house-rules-main-B2.kicad_pcb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commands(text):
    # Exclude only known KiCad timestamp records, preserving every aperture,
    # primitive, coordinate, tool and process/attribute record otherwise.
    return '\n'.join(line for line in text.splitlines() if not (
        line.startswith('%TF.CreationDate,')
        or line.startswith('G04 Created by KiCad (PCBNEW ')
        or line.startswith('; DRILL file KiCad ')
        or line.startswith('; #@! TF.CreationDate,')))


def main():
    wx.Log.EnableLogging(False)
    app = wx.App(False)
    source_hash = sha(BOARD)
    parser = B2 / 'reports/confirmed-F-2026-10-31/independent-hardware-verification.py'
    spec = importlib.util.spec_from_file_location('frozen_F_output_parser', parser)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = module.manufacturing_check(NEW, k.LoadBoard(str(BOARD)))
    equal = []
    for folder in ['fabrication', 'assembly']:
        for path in sorted((NEW / folder).iterdir()):
            if not path.is_file():
                continue
            text = path.read_text(errors='ignore')
            if '%FSL' not in text and path.suffix != '.drl':
                continue
            frozen = OLD / folder / path.name
            assert frozen.is_file(), path.name
            normalised = commands(text)
            assert normalised == commands(frozen.read_text()), 'Plotted geometry/process changed: ' + path.name
            equal.append({'file': str(path.relative_to(NEW)),
                          'timestamp_independent_sha256': hashlib.sha256(normalised.encode()).hexdigest()})
    assert len(equal) == 15, 'Expected 11 fabrication Gerbers, 2 paste Gerbers and 2 drill files'
    cpl = 'assembly/cpl-manufacturer-review.csv'
    assert (NEW / cpl).read_bytes() == (OLD / cpl).read_bytes(), 'CPL coordinates/angles changed'
    assert sha(BOARD) == source_hash
    result = {
        'result': 'PASS', 'canonical_PCB_sha256': source_hash,
        'package': str(NEW.relative_to(B2)), 'actual_output_inspection': actual,
        'plotted_copper_mask_silk_outline_paste_and_drill_commands_unchanged_except_timestamps': equal,
        'native_CPL_byte_identical_to_confirmed_F': True,
        'shared_output_parser_sha256': sha(parser),
        'verifier_sha256': sha(Path(__file__)),
        'scope': 'Actual saved CAD/CSV/Gerber/Excellon and manifest inspection. Factory CAM/feeder/pin1 review and physical acceptance remain pending.',
        'source_unchanged_during_read_only_check': True,
        'order_or_payment_submitted': False,
    }
    (HERE / 'manufacturing-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'result': result['result'], 'plot_and_drill_files_compared': len(equal),
                      'BOM_CPL_factory_references': actual['BOM_CPL_exact_factory_references'],
                      'native_CPL_identical': True}, indent=2))


if __name__ == '__main__':
    main()
