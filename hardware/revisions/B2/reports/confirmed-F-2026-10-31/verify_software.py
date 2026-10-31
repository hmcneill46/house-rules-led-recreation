#!/usr/bin/env python3
"""Recheck unchanged B2 software/electrical logic after the confirmed-F resize.

The existing schematic and binaries are inspected; they are never rebuilt.
Native ERC/netlist and binary-audit side effects occur in temporary copies.
Host/pin-model checks refresh their normal reports, with prior evidence archived.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]
ROOT = B2.parents[2]
FW = B2 / 'firmware'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
REFERENCE = 'efad429'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def run(command, log):
    result = subprocess.run(command, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    result.check_returncode()
    return result


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    before = HERE / 'software-before'
    before.mkdir(exist_ok=True)
    report_paths = [B2 / 'reports' / n for n in (
        'schematic.erc.json', 'schematic.net.xml',
        'schematic-verification-summary.json')]
    report_paths += [FW / 'verification-summary.json',
                     FW / 'tests/verification.json',
                     B2 / 'simulation/verification.json']
    report_paths += [FW / folder / 'binary-audit.json'
                     for folder in ('compiled', 'compiled-unknown-off')]
    for source in report_paths:
        target = before / source.relative_to(B2)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    spec_path = B2 / 'electrical-spec.json'
    spec = json.loads(spec_path.read_text())
    prior_spec = json.loads(subprocess.check_output([
        'git', 'show', REFERENCE + ':hardware/revisions/B2/electrical-spec.json'],
        cwd=ROOT, text=True))
    assert spec['parts'] == prior_spec['parts'], 'Circuit part/pin map changed'
    source_hashes = {}
    for folder in ('compiled', 'compiled-unknown-off'):
        metadata = json.loads((FW / folder / 'build-metadata.json').read_text())
        for name, expected in metadata['source_sha256'].items():
            path = FW / name
            assert sha(path) == expected, 'Built firmware source changed: ' + name
            source_hashes[str(path.relative_to(B2))] = expected
        for name, expected in metadata['sha256'].items():
            path = FW / folder / name
            assert sha(path) == expected, 'Built firmware artifact changed: ' + str(path)
            source_hashes[str(path.relative_to(B2))] = expected
    sch = B2 / 'kicad/house-rules-main-B2.kicad_sch'
    project = sch.with_suffix('.kicad_pro')
    protected = {str(p.relative_to(B2)): sha(p)
                 for p in [spec_path, sch, project]}
    protected.update(source_hashes)
    erc_config = json.loads(project.read_text()).get('erc', {})
    assert not erc_config.get('erc_exclusions')
    assert not erc_config.get('rule_severities')

    with tempfile.TemporaryDirectory(prefix='house-rules-b2-F-software-') as directory:
        temporary = Path(directory)
        copy_sch = temporary / sch.name
        shutil.copyfile(sch, copy_sch)
        shutil.copyfile(project, copy_sch.with_suffix('.kicad_pro'))
        # Embedded symbols preserve drawing data, but ERC also resolves native
        # symbol/footprint library links. Keep the project-local libraries in
        # the disposable snapshot rather than suppressing those checks.
        for pattern in ('*-lib-table', '*.kicad_sym'):
            for source in sch.parent.glob(pattern):
                shutil.copyfile(source, temporary / source.name)
        shutil.copytree(sch.parent / 'footprints', temporary / 'footprints')
        erc = HERE / 'schematic.erc.json'
        net = HERE / 'schematic.net.xml'
        commands = [
            [CLI, 'sch', 'erc', '--format', 'json', '--severity-all', '--output',
             str(erc), '--exit-code-violations', str(copy_sch)],
            [CLI, 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
             str(net), str(copy_sch)]]
        run(commands[0], HERE / 'schematic-erc.log')
        run(commands[1], HERE / 'schematic-netlist.log')
        erc_data = json.loads(erc.read_text())
        violations = [v for sheet in erc_data.get('sheets', [])
                      for v in sheet.get('violations', [])]
        assert not violations
        tree = ET.parse(net)
        actual = {(p.attrib['ref'], p.attrib['pin']): n.attrib['name'].lstrip('/')
                  for n in tree.findall('./nets/net') for p in n.findall('node')
                  if not p.attrib['ref'].startswith('#')}
        expected = {(p['ref'], pin): net for p in spec['parts']
                    for pin, net in p['pins'].items() if net is not None}
        missing = {str(k): v for k, v in expected.items() if actual.get(k) != v}
        extra = {str(k): v for k, v in actual.items()
                 if k not in expected and not v.startswith('unconnected-')}
        components = {p.attrib['ref'] for p in tree.findall('./components/comp')}
        assert components == {p['ref'] for p in spec['parts']}
        assert not missing and not extra
        assert len(components) == 82 and len(expected) == 327
        schematic_summary = {
            'revision': 'B2', 'spec_sha256': sha(spec_path),
            'component_count': len(components), 'connected_pin_count': len(expected),
            'netlist_matches_spec': True, 'missing': missing, 'extra': extra,
            'erc_exit_code': 0, 'erc_violation_count': 0, 'erc_exclusions': False}
        dump(HERE / 'schematic-verification-summary.json', schematic_summary)

        def host_check():
            command = [sys.executable, str(FW / 'tests/test_host.py')]
            run(command, HERE / 'firmware-host.log')
            shutil.copyfile(FW / 'tests/verification.json',
                            HERE / 'firmware-host-verification.json')
            return command

        def model_check():
            command = [sys.executable, str(B2 / 'simulation/test_model.py')]
            run(command, HERE / 'pin-model.log')
            shutil.copyfile(B2 / 'simulation/verification.json',
                            HERE / 'pin-model-verification.json')
            return command

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(host_check), pool.submit(model_check)]
            commands += [future.result() for future in futures]

        binary_audits = {}
        for folder in ('compiled', 'compiled-unknown-off'):
            output = temporary / folder
            output.mkdir()
            for name in ('HouseRulesB2.ino.uf2', 'HouseRulesB2.ino.elf',
                         'HouseRulesB2.ino.bin', 'build-metadata.json'):
                shutil.copyfile(FW / folder / name, output / name)
            command = [sys.executable, str(B2 / 'tools/firmware-build/audit_binary.py'),
                       '--output', str(output)]
            run(command, HERE / (folder + '-audit.log'))
            commands.append(command)
            audit = json.loads((output / 'binary-audit.json').read_text())
            assert audit['result'] == 'PASS'
            binary_audits[folder] = audit
            dump(HERE / (folder + '-binary-audit.json'), audit)

    assert protected == {path: sha(B2 / path) for path in protected}, \
        'Protected schematic, specification, firmware source or binary changed during checks'
    for name in ('schematic.erc.json', 'schematic.net.xml',
                 'schematic-verification-summary.json'):
        shutil.copyfile(HERE / name, B2 / 'reports' / name)
    host = json.loads((FW / 'tests/verification.json').read_text())
    model = json.loads((B2 / 'simulation/verification.json').read_text())
    assert host['result'] == model['result'] == 'PASS'
    assert model['electrical_spec_sha256'] == sha(spec_path)
    summary = {
        'result': 'PASS', 'date_utc': datetime.now(timezone.utc).isoformat(),
        'reference_revision': REFERENCE,
        'electrical_parts_and_pins_unchanged_from_reference': True,
        'electrical_spec_sha256': sha(spec_path),
        'schematic_sha256': sha(sch),
        'protected_sources_and_compiled_images_unchanged': True,
        'protected_sha256': protected,
        'native_ERC_violations': 0, 'schematic_component_count': 82,
        'schematic_connected_pin_count': 327, 'schematic_netlist_matches_spec': True,
        'host_result': host['result'], 'host_artwork_frames': host['artwork_frames'],
        'host_all_245_single_pixels': host['all_245_single_pixels'],
        'host_random_frames': host['random_frames'],
        'physical_connection_model_result': model['result'],
        'model_walking_pixels': model['walking_pixels'],
        'model_artwork_frames': model['artwork_frames'],
        'model_per_phase_reconstructions': model['per_phase_reconstructions'],
        'injected_fault_cases_detected': model['fault_cases_detected'],
        'compiled_image_audits': binary_audits,
        'commands': commands,
        'limitations': [
            'Software/static binary checks only; no powered board or printer executed',
            'Routed PCB connectivity/geometry and case fit are separate fresh checks',
            'No real USB enumeration, current, scan-edge, optical or temperature measurement']}
    dump(HERE / 'software-verification-summary.json', summary)
    fw_summary = json.loads((FW / 'verification-summary.json').read_text())
    fw_summary['confirmed_F_reverification'] = {
        'date_utc': summary['date_utc'], 'result': 'PASS',
        'electrical_spec_sha256': sha(spec_path),
        'source_and_existing_images_unchanged': True,
        'report': '../reports/confirmed-F-2026-10-31/software-verification-summary.json'}
    dump(FW / 'verification-summary.json', fw_summary)
    print(json.dumps({k: summary[k] for k in (
        'result', 'electrical_spec_sha256', 'native_ERC_violations',
        'schematic_component_count', 'schematic_connected_pin_count',
        'host_artwork_frames', 'model_artwork_frames',
        'model_per_phase_reconstructions')}, indent=2))


if __name__ == '__main__':
    main()
