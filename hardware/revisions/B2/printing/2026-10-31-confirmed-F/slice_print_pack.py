#!/usr/bin/env python3
"""Slice the three prepared confirmed-F jobs without opening or printing them."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SLICER = '/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer'
TEMP = Path('/tmp/house-rules-B2-confirmed-F-2026-10-31')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slice_job(job):
    folder = TEMP/job
    folder.mkdir(parents=True,exist_ok=True)
    project = HERE/'projects'/(job+'.3mf')
    command = [SLICER,'--datadir',str(folder/'user'),'--slice','0',
        '--arrange','0','--orient','0','--outputdir',str(folder),
        '--export-3mf',job+'-sliced.3mf',str(project)]
    result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    log = HERE/'logs'/(job+'-orca.log')
    log.write_text(result.stdout+result.stderr)
    result.check_returncode()
    gcode = HERE/'gcode'/(job+'.gcode')
    sliced = HERE/'sliced-projects'/(job+'.3mf')
    shutil.copyfile(folder/'plate_1.gcode',gcode)
    shutil.copyfile(folder/(job+'-sliced.3mf'),sliced)
    with zipfile.ZipFile(sliced) as archive:
        assert archive.read('Metadata/plate_1.gcode') == gcode.read_bytes()
    return job,{'command':command,'exit_code':result.returncode,
        'prepared_project_sha256':sha(project),'sliced_project_sha256':sha(sliced),
        'Gcode_sha256':sha(gcode),'embedded_Gcode_byte_identical':True,
        'log':str(log.relative_to(HERE))}


def main():
    preparation = json.loads((HERE/'preparation.json').read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = dict(pool.map(slice_job,preparation['jobs']))
    report = {'date_utc':datetime.now(timezone.utc).isoformat(),
        'slicer':'Installed OrcaSlicer 2.4.2','jobs':jobs,
        'owner_UI_state':'Existing unsaved Orca scene was not opened, replaced or saved.',
        'printer_execution':'None; no printer connection or print start.'}
    (HERE/'slice-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Successfully sliced all three confirmed-F jobs; embedded G-code bytes match.')


if __name__ == '__main__':
    main()
