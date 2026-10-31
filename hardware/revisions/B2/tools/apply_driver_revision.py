#!/usr/bin/env python3
"""Apply the reviewed TLC59283/7.15k identities to frozen F copper.

This deliberately edits only known non-geometric strings. Reversing the exact
substitutions must reproduce every byte of the frozen input, including all
copper, pad positions, holes, zones, models and rules. Native ERC/DRC and the
independent board/export audits remain mandatory; this is not an order release.
"""
import argparse
import hashlib
import json
from pathlib import Path

B2 = Path(__file__).resolve().parents[1]
SOURCE = B2 / 'manufacturing/B2_F_12p875_review_2026-10-31/source/house-rules-main-B2.kicad_pcb'
SOURCE_SHA = 'b42e3d59b40a2e9cc877f8c5595d58339a2c7b0797970fa826ea84c19b8105f1'
SUBSTITUTIONS = [
    ('TLC59282RGER', 'TLC59283RGER', 16),
    ('tlc59282.pdf', 'tlc59283.pdf', 4),
    ('C702074', 'C485815', 4),
    ('6k8 1%', '7k15 1%', 4),
    ('0603WAF6801T5E', '0603WAF7151T5E', 4),
    ('C23212', 'C25980', 4),
    ('Sets 7.42493mA nominal peak; Basic resistor avoids Extended setup fee',
     'Sets 7.40006mA nominal peak for TLC59283; Extended resistor setup included in quote', 4),
    ('16-bit current sinks; U4 OUT7..11 also sink PMOS gate current',
     '16-bit current sinks with precharge; U4 OUT7..11 also sink PMOS gate current', 4),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=B2 / 'kicad/house-rules-main-B2.kicad_pcb')
    args = parser.parse_args()
    original = args.source.read_bytes()
    assert sha(original) == SOURCE_SHA, 'Input is not the independently checked frozen F board'
    assert args.source.resolve() != args.output.resolve(), 'Never overwrite historical source'
    text = original.decode()
    for before, after, count in SUBSTITUTIONS:
        assert text.count(before) == count, before
        assert after not in text, after
        text = text.replace(before, after)
    reverse = text
    for before, after, count in reversed(SUBSTITUTIONS):
        assert reverse.count(after) == count, after
        reverse = reverse.replace(after, before)
    assert reverse.encode() == original, 'Unexpected geometry or other content changed'
    args.output.write_text(text)
    report = {
        'result': 'PASS for exact non-geometric identity substitutions',
        'predecessor_source': str(args.source.relative_to(B2)),
        'predecessor_pcb_sha256': sha(original),
        'updated_pcb_sha256': sha(text.encode()),
        'driver_references': ['U1', 'U2', 'U3', 'U4'],
        'resistor_references': ['R1', 'R2', 'R3', 'R4'],
        'substitutions': [{'from': a, 'to': b, 'occurrences': n} for a, b, n in SUBSTITUTIONS],
        'reversing_only_identity_strings_restores_every_source_byte': True,
        'copper_pads_holes_zones_models_outline_and_rules_unchanged': True,
        'nominal_current_equation_mA': '1.208 * 43.8 / 7.15',
        'nominal_peak_mA': 1.208 * 43.8 / 7.15,
        'scope': 'Represented geometry and metadata only; native checks and powered precharge/rail/optical/USB/thermal acceptance remain separate',
        'order_or_payment_submitted': False,
    }
    folder = B2 / 'reports/TLC59283-2026-10-31'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'identity-update.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
