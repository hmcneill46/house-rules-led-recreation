#!/usr/bin/env python3
"""Host execution of B2 scan/power logic and independent artwork reference."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
FW=HERE.parent

def main():
    with tempfile.TemporaryDirectory(prefix='house-rules-b2-test-') as tmp:
        exe=Path(tmp)/'test'
        cmd=['c++','-std=c++11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-O2',
             '-I'+str(FW/'HouseRulesB2'),'-I'+str(FW),str(HERE/'host_test.cpp'),'-o',str(exe)]
        subprocess.run(cmd,check=True);output=subprocess.check_output([str(exe)])
    assert len(output)==60000*35
    manifest=json.loads((FW/'sequence_manifest.json').read_text());data=(FW/'sequence_columns.bin').read_bytes()
    index=scroll=flash=wraps=0
    for frame in range(60000):
        command=manifest['commands'][index]
        if command['kind']=='scrolling':scroll+=95;offset=scroll//120
        else:offset=0
        length=max(0,min(35,command['length']-offset));start=command['offset']+offset
        expected=data[start:start+length].ljust(35,b'\0')
        assert output[frame*35:(frame+1)*35]==expected,(frame,index)
        if command['kind']=='flash':flash+=1;done=flash>=command['flash_frames']
        else:done=offset>=max(0,command['length']-35)
        if done:
            if index==len(manifest['commands'])-1:wraps+=1;assert command['next_index']==1
            index=command['next_index'];scroll=flash=0
    assert wraps>=2
    provenance=json.loads((FW/'artwork-provenance.json').read_text())
    # Compare directly with the untouched A1 originals, in addition to the independent player model.
    a1=FW.parents[2]/'firmware'
    for name in ('generated_sequence.h','sequence_columns.bin','sequence_manifest.json'):
        assert (FW/name).read_bytes()==(a1/name).read_bytes(),name
    report={'result':'PASS','artwork_frames':60000,'complete_traversals':wraps,
      'frame_sha256':hashlib.sha256(output).hexdigest(),'scan_map_sha256':hashlib.sha256((FW/'scan-map.json').read_bytes()).hexdigest(),'all_245_single_pixels':True,
      'random_frames':1000,'scan_full_and_dim_us':[470,25],'phase_us':500,'frame_hz':400,
      'checks':['64-bit mapping and serial order','one gate selected and unused outputs off',
      '30us blank before every phase','frame swap only at phase0','late IRQ skips or latches dark',
      'SPI failure and invalid map fail dark','CC qualification and wraparound','BC1.2 DET/AL truth table, qualification, withdrawal and wraparound',
      'all64 source/suspend policy combinations; host suspend overrides every grant',
      '10ms switched-rail ramp and HiZ shutdown','245 walking dots and checkerboard','A1 artwork files byte-identical'],
      'limitations':'Host simulation only; analog gate timing, source current, USB suspend current and physical pixels require first-board measurement.'}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
