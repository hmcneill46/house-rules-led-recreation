#!/usr/bin/env python3
"""Ensure stale driver/current identities cannot silently generate a contract."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]


def main():
    path = B2 / 'tools/firmware-build/generate_contract.py'
    spec = importlib.util.spec_from_file_location('contract_generator', path)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    mapping = json.loads((B2 / 'firmware/scan-map.json').read_text())
    circuit = json.loads((B2 / 'electrical-spec.json').read_text())
    detected = []
    with tempfile.TemporaryDirectory(prefix='house-rules-contract-') as tmp:
        generator.B2 = root = Path(tmp)
        (root / 'firmware/HouseRulesB2').mkdir(parents=True)

        def fixture(m, c):
            # Keep the original map bytes so its embedded hash is reproducible.
            if m == mapping:
                (root / 'firmware/scan-map.json').write_bytes((B2 / 'firmware/scan-map.json').read_bytes())
            else:
                (root / 'firmware/scan-map.json').write_text(json.dumps(m))
            (root / 'electrical-spec.json').write_text(json.dumps(c))

        fixture(mapping, circuit)
        generator.generate()
        assert (root / 'firmware/HouseRulesB2/board_contract_generated.h').read_bytes() == \
            (B2 / 'firmware/HouseRulesB2/board_contract_generated.h').read_bytes()

        wrong_resistor = copy.deepcopy(circuit)
        next(p for p in wrong_resistor['parts'] if p['ref'] == 'R1')['value'] = '6k8 1%'
        wrong_driver = copy.deepcopy(circuit)
        next(p for p in wrong_driver['parts'] if p['ref'] == 'U1')['lcsc'] = 'C702074'
        stale_map = copy.deepcopy(mapping)
        stale_map['iref_ohms'] = 6800
        for m, c, reason in [(mapping, wrong_resistor, 'Old6.8kohm IREF resistor'),
                             (mapping, wrong_driver, 'Original driver procurement code'),
                             (stale_map, circuit, 'Stale firmware current contract')]:
            fixture(m, c)
            try:
                generator.generate()
            except ValueError:
                detected.append(reason)
            else:
                raise AssertionError('Expected rejection: ' + reason)
    result = {'result': 'PASS', 'baseline_generated_header_matches': True,
              'stale_identity_faults_detected': detected,
              'limitations': 'Source identity checks only; not circuit or powered-device validation'}
    (HERE / 'contract-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
