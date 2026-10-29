#!/usr/bin/env python3
"""Validate the PCB/firmware data contract and generate a deterministic header."""
import hashlib,json
from pathlib import Path

B2=Path(__file__).resolve().parents[2]

def generate():
    path=B2/'firmware/scan-map.json'; data=path.read_bytes(); spec=json.loads(data)
    rows=[pin for module in spec['module_row_outputs'] for pin in module]
    gates=spec['column_gate_outputs']
    if len(spec['module_row_outputs'])!=7 or any(len(m)!=7 for m in spec['module_row_outputs']):
        raise ValueError('Exactly seven modules with seven row outputs are required')
    if len(gates)!=5 or len(set(rows+gates))!=54 or any(not 0<=v<64 for v in rows+gates):
        raise ValueError('The 49 row and five gate channels must be distinct and inside 0..63')
    expected={'phase_us':500,'deadtime_us':30,'full_on_us':470,'dim_on_us':25}
    if any(spec[k]!=v for k,v in expected.items()): raise ValueError('Scan timing contract changed; review engine/tests first')
    pins=spec['gpio']
    if len(set(pins.values()))!=len(pins) or any(not 0<=v<30 for v in pins.values()):
        raise ValueError('GPIOs must be distinct raw RP2040 GPIO numbers')
    if {pins['cc1_adc'],pins['cc2_adc']}!={26,27}: raise ValueError('CC ADC channels must remain GPIO26/27')
    if (pins['sin'],pins['sclk'])!=(3,2): raise ValueError('SPI0 backend requires SIN GPIO3 and SCLK GPIO2; update hardware backend before changing')
    if spec['rail_settle_us']<10000: raise ValueError('TPS22918 rail ramp requires at least10ms startup qualification delay')
    text='// Generated from scan-map.json; do not edit this header.\n#pragma once\n#include "scan_engine.h"\nnamespace hrb2 {\n'
    text+='static constexpr Layout kBoardLayout = {{'+','.join(map(str,rows))+'},{'+','.join(map(str,gates))+'}};\n'
    for key,value in pins.items(): text+=f'static constexpr uint8_t PIN_{key.upper()} = {value};\n'
    text+=f'static constexpr uint32_t RAIL_SETTLE_US = {spec["rail_settle_us"]};\n'
    text+='static constexpr const char *CONTRACT_SHA256 = "'+hashlib.sha256(data).hexdigest()+'";\n}\n'
    out=B2/'firmware/HouseRulesB2/board_contract_generated.h';out.write_text(text)
    return spec

if __name__=='__main__':generate()
