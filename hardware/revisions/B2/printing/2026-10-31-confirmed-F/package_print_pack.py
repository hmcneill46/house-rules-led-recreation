#!/usr/bin/env python3
"""Package only the independently verified confirmed-F printer files."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((HERE/'verification.json').read_text())
    assert report['result'] == 'PASS'
    files = {'PRINT_FIRST.txt':HERE/'PRINT_FIRST.txt','verification.json':HERE/'verification.json'}
    for job,record in report['jobs'].items():
        path = HERE/'gcode'/(job+'.gcode')
        assert sha(path) == record['Gcode_sha256']
        files[path.name] = path
    output = HERE/'B2_F_12p875_KE04_HyperPLA_PrintPack.zip'
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,path in files.items():archive.write(path,name)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None and set(archive.namelist()) == set(files)
        for name,path in files.items():assert archive.read(name) == path.read_bytes()
    manifest = {'date':'2026-10-31','bundle':output.name,'bundle_sha256':sha(output),
        'entry_sha256':{name:sha(path) for name,path in files.items()},
        'zip_integrity_and_entry_bytes_verified':True}
    (HERE/'bundle-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output)


if __name__ == '__main__':
    main()
