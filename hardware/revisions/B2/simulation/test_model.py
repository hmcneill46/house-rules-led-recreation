#!/usr/bin/env python3
"""Firmware-to-electrical pin-graph test, including intentional broken circuits."""
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from matrix_model import ModuleArray,CircuitError,SPEC,RGE,Sink

HERE=Path(__file__).resolve().parent
FW=HERE.parent/'firmware'
ROOT=HERE.parents[3]
RECORD=75

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def reject(call,reason):
    try:call()
    except CircuitError:return reason
    raise AssertionError('Expected model to reject: '+reason)

def swapped(spec,ref,pin1,pin2):
    result=copy.deepcopy(spec);p=next(p for p in result['parts'] if p['ref']==ref)
    p['pins'][str(pin1)],p['pins'][str(pin2)]=p['pins'][str(pin2)],p['pins'][str(pin1)]
    return result

def flip_sink(serial,model,sink):
    # Fault injection mutates serialized output bits, separately from decoding.
    words=list(model.latch_serial(serial));words[model.chain.index(sink.ref)]^=1<<sink.output
    return b''.join(w.to_bytes(2,'big') for w in reversed(words))

def expected_artwork(manifest,data,count):
    index=manifest['initial_command'];scroll=flash=wraps=0;seen=set()
    for _ in range(count):
        seen.add(index);command=manifest['commands'][index]
        if command['kind']=='scrolling':scroll+=95;offset=scroll//120
        else:offset=0
        length=max(0,min(35,command['length']-offset));start=command['offset']+offset
        frame=data[start:start+length].ljust(35,b'\0')
        yield frame,index
        if command['kind']=='flash':flash+=1;done=flash>=command['flash_frames']
        else:done=offset>=max(0,command['length']-35)
        if done:index=command['next_index'];scroll=flash=0

def run():
    spec=json.loads(SPEC.read_text());model=ModuleArray(spec)
    with tempfile.TemporaryDirectory(prefix='house-rules-b2-pin-model-') as tmp:
        exe=Path(tmp)/'bridge'
        command=['c++','-std=c++11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
                 '-I'+str(FW/'HouseRulesB2'),'-I'+str(FW),str(HERE/'firmware_bridge.cpp'),'-o',str(exe)]
        subprocess.run(command,check=True)
        output=subprocess.check_output([str(exe)])
    assert output[:8]==b'HRB2PIN1'
    records=output[8:];assert len(records)==(245+2+60000)*RECORD
    walking=[];all_phases=None;artwork_digest=hashlib.sha256();artwork_commands=set();wraps=0;last_command=None
    manifest=json.loads((FW/'sequence_manifest.json').read_text());columns=(FW/'sequence_columns.bin').read_bytes()
    reference=iter(expected_artwork(manifest,columns,60000))
    for index in range(60247):
        raw=records[index*RECORD:(index+1)*RECORD];frame=raw[:35];phases=tuple(raw[35+p*8:43+p*8] for p in range(5))
        reconstructed=model.decode_frame(phases)
        assert reconstructed==frame,('physical pixel mismatch',index,reconstructed.hex(),frame.hex())
        # Each phase must light only the intended visual column within modules.
        for phase,serial in enumerate(phases):
            expected=bytes(c if x%5==phase else 0 for x,c in enumerate(frame))
            assert model.decode_serial(serial)==expected,('wrong physical scan column',index,phase)
        if index<245:
            desired=bytearray(35);desired[index//7]=1<<(index%7)
            assert frame==desired;walking.append(phases)
        elif index==245:
            assert frame==bytes([127]*35);all_phases=phases
        elif index==246:assert frame==bytes(0x2a if x%2 else 0x55 for x in range(35))
        else:
            expected,command_index=next(reference);assert frame==expected,('artwork player mismatch',index-247,command_index)
            artwork_digest.update(reconstructed);artwork_commands.add(command_index)
            if last_command==len(manifest['commands'])-1 and command_index==1:wraps+=1
            last_command=command_index
    assert wraps>=2 and len(artwork_commands)==len(manifest['commands'])
    # Preserve provenance against A1, independent of B2's copied generated files.
    for name in ('generated_sequence.h','sequence_columns.bin','sequence_manifest.json'):
        assert (FW/name).read_bytes()==(ROOT/'hardware/firmware'/name).read_bytes(),name
    assert all_phases is not None
    faults=[]
    faults.append(reject(lambda:ModuleArray(swapped(spec,'DS1',1,12)),'LED anode/cathode polarity swap'))
    shared=copy.deepcopy(spec)
    ds1=next(p for p in shared['parts'] if p['ref']=='DS1');ds2=next(p for p in shared['parts'] if p['ref']=='DS2')
    ds2['pins']['12']=ds1['pins']['12']
    faults.append(reject(lambda:ModuleArray(shared),'Cathodes accidentally shared across modules'))
    faults.append(reject(lambda:ModuleArray(swapped(spec,'Q1',2,3)),'PMOS source/drain reversal'))
    faults.append(reject(lambda:ModuleArray(swapped(spec,'U9',2,8)),'BQ USB upstream/downstream terminals swapped'))
    bq_power=copy.deepcopy(spec)
    next(p for p in bq_power['parts']if p['ref']=='U9')['pins']['5']='SW_3V3'
    faults.append(reject(lambda:ModuleArray(bq_power),'BQ GOOD_BAT on switched rail would disconnect USB during suspend'))
    bq_divider=copy.deepcopy(spec)
    next(p for p in bq_divider['parts']if p['ref']=='R21')['value']='47k 1%'
    faults.append(reject(lambda:ModuleArray(bq_divider),'BQ detector divider cannot meet RP2040 input-high threshold'))
    faults.append(reject(lambda:model.decode_serial(flip_sink(all_phases[0],model,model.gates['Q2'])),'Two column gates enabled simultaneously'))
    faults.append(reject(lambda:model.decode_serial(flip_sink(all_phases[0],model,model.gates['Q1'])),'Row bits set with no selected gate'))
    unused=sorted(model.unused_sinks,key=lambda s:(s.ref,s.output))[0]
    faults.append(reject(lambda:model.decode_serial(flip_sink(all_phases[0],model,unused)),'Unconnected sink enabled'))
    faults.append(reject(lambda:model.decode_serial(all_phases[0],False,False,True),'LED supply remains on while driver unpowered'))
    # A wrong physical OUT mapping is detected despite unchanged firmware metadata.
    miswired=ModuleArray(swapped(spec,'U1',RGE['OUT'][0],RGE['OUT'][1]))
    assert miswired.decode_frame(walking[0])!=bytes([1]+[0]*34)
    faults.append('Swapped TLC physical OUT pins change the independently reconstructed pixel')
    # Pin labels are cosmetic; do not let self-consistent mislabelling hide wiring errors.
    cosmetic=copy.deepcopy(spec)
    for p in cosmetic['parts']:
        if p['ref'] in model.drivers:p['pin_names']={k:'WRONG_LABEL' for k in p['pins']}
    assert ModuleArray(cosmetic).decode_frame(walking[0])==bytes([1]+[0]*34)
    # Reverse the transmitted chip words and prove it cannot pass as a valid image.
    reversed_serial=b''.join(all_phases[0][i:i+2] for i in range(6,-1,-2))
    try:wrong=model.decode_serial(reversed_serial);assert wrong!=model.decode_serial(all_phases[0])
    except CircuitError:pass
    faults.append('Reversed serial chip order is rejected or produces a different physical image')
    # Hardware BLANK and supply removal defeat even deliberately all-one shift data.
    assert model.decode_serial(bytes([255]*8),blank=True)==bytes(35)
    assert model.decode_serial(bytes([255]*8),driver_power=False,vled_power=False)==bytes(35)
    assert model.decode_serial(bytes(8))==bytes(35)
    peak=max(model.led_peak_current_a(p) for p in all_phases)
    assert abs(peak-49*1.205*41.9/6800)<1e-12
    report={
      'result':'PASS','date_utc':datetime.now(timezone.utc).isoformat(),'model':'Independent physical diode/TLC/PMOS connectivity model',
      'electrical_spec_sha256':sha(SPEC),'firmware_source_sha256':{str(p.relative_to(FW)):sha(p) for p in [FW/'HouseRulesB2/scan_engine.h',FW/'HouseRulesB2/board_contract_generated.h',FW/'HouseRulesB2/player.h',FW/'generated_sequence.h']},
      'package':'TLC59282RGER RGE0024C; physical output pins2..17, EP25=GND',
      'module_count':7,'physical_diode_paths':len(model.paths),'daisy_chain_from_actual_nets':model.chain,
      'walking_pixels':245,'diagnostic_frames':2,'artwork_frames':60000,'artwork_commands_covered':len(artwork_commands),
      'complete_artwork_traversals':wraps,'artwork_frame_sha256':artwork_digest.hexdigest(),
      'per_phase_reconstructions':60247*5,'nominal_single_LED_peak_mA':peak*1000/49,'nominal_all_white_LED_peak_A':peak,
      'nominal_all_white_LED_average_A_at470of500us':peak*.94,
      'nominal_all_white_LED_average_A_at25of500us':peak*.05,
      'fault_cases_detected':faults,'blank_and_both_rails_off_force_dark':True,'cosmetic_pin_labels_ignored':True,
      'usb_frontend_static_check':model.usb_frontend,
      'limitations':['Functional connectivity only; no MOSFET gate charge, ghosting, current compliance or thermal simulation',
                    'No real USB enumeration, suspend current or startup inrush measurement',
                    'One owned module full pin map/orientation is owner-verified; other20 modules and powered-board operation remain unverified',
                    'Uses schematic electrical-spec connections, not routed-PCB extraction; final PCB net parity is a separate check']}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()
