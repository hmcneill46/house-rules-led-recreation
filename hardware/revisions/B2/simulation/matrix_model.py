"""Independent B2 functional electrical model, not an analog/SPICE simulation.

The firmware's logical scan map is deliberately NOT imported. Output paths are
traced through physical package pins and the connection graph in electrical-spec.
Module diode polarity and TLC package terminals are independently transcribed
from manufacturer drawings; changing labels alone cannot change this model.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent/'electrical-spec.json'
# Manufacturer diode topology, visual left->right/top->bottom, normal view.
ANODES = (1,3,10,7,8)
CATHODES = (12,11,2,9,4,5,6)
# TI RGE physical terminal assignment; not taken from firmware or pin_names.
RGE = {'LAT':1,'OUT':tuple(range(2,18)),'BLANK':18,'SOUT':19,
       'IREF':20,'VCC':21,'GND':22,'SIN':23,'SCLK':24,'EP':25}
P_MOS = {'G':1,'S':2,'D':3}
# TI BQ24392 RSE0010A terminal map, independently transcribed from RevG p3.
BQ_RSE = {'SW_OPEN':1,'DM_HOST':2,'DP_HOST':3,'CHG_AL_N':4,'GOOD_BAT':5,
          'GND':6,'DP_CON':7,'DM_CON':8,'VBUS':9,'CHG_DET':10}

class CircuitError(ValueError): pass

@dataclass(frozen=True)
class Sink:
    ref: str
    output: int

@dataclass(frozen=True)
class PixelPath:
    module: str
    x: int
    y: int
    anode_pin: int
    cathode_pin: int
    mosfet: str
    gate: Sink
    cathode: Sink

def resistance(value):
    token=value.split()[0].lower()
    m=re.fullmatch(r'(\d+)([kMr]?)(\d*)',token)
    if not m:raise CircuitError(f'Unrecognized resistor value {value}')
    whole,unit,fraction=m.groups()
    scale={'':1,'r':1,'k':1000,'m':1000000}[unit]
    return float(whole+'.'+(fraction or '0'))*scale

class ModuleArray:
    def __init__(self,spec=None):
        self.spec=json.loads(SPEC.read_text()) if spec is None else spec
        self.parts={p['ref']:p for p in self.spec['parts']}
        if len(self.parts)!=len(self.spec['parts']):raise CircuitError('Duplicate component reference')
        self.drivers={r:p for r,p in self.parts.items() if p.get('mpn')=='TLC59282RGER'}
        self.mosfets={r:p for r,p in self.parts.items() if p.get('mpn')=='AO3401A'}
        self.modules=sorted((p for p in self.parts.values() if p['ref'].startswith('DS')),key=lambda p:int(p['ref'][2:]))
        if len(self.drivers)!=4 or len(self.mosfets)!=5 or len(self.modules)!=7:
            raise CircuitError('Expected4 TLC59282RGER,5 AO3401A and7 raw matrices')
        def net(part,pin):return part['pins'].get(str(pin))
        self.net=net
        self.sinks={}
        for ref,p in self.drivers.items():
            for signal,expected in [('LAT','LAT'),('BLANK','BLANK'),('SCLK','SCLK'),('VCC','SW_3V3'),('GND','GND'),('EP','GND')]:
                if net(p,RGE[signal])!=expected:raise CircuitError(f'{ref} physical {signal} terminal has wrong net')
            for output,pin in enumerate(RGE['OUT']):
                n=net(p,pin)
                if n is not None:
                    if n in self.sinks:raise CircuitError(f'Two current sinks shorted on {n}')
                    self.sinks[n]=Sink(ref,output)
        # Traverse actual SOUT/SIN nets, independent of the firmware's U-number order.
        chain=[]; wire='SIN'
        while len(chain)<4:
            following=[r for r,p in self.drivers.items() if net(p,RGE['SIN'])==wire]
            if len(following)!=1 or following[0] in chain:raise CircuitError('Invalid daisy-chain wiring')
            ref=following[0];chain.append(ref);wire=net(self.drivers[ref],RGE['SOUT'])
        if wire is not None:raise CircuitError('Last serial output must be intentionally unconnected')
        self.chain=tuple(chain)
        self.gates={};self.source_for_anode={};self.bleeds={};self.pullups={}
        for ref,p in self.mosfets.items():
            if net(p,P_MOS['S'])!='VLED_5V':raise CircuitError(f'{ref} source is not on VLED_5V; reversed PMOS/body diode risk')
            gate,anode=net(p,P_MOS['G']),net(p,P_MOS['D'])
            if gate not in self.sinks:raise CircuitError(f'{ref} gate has no physical TLC sink')
            if anode in self.source_for_anode:raise CircuitError('Multiple PMOS drains shorted on one column')
            self.gates[ref]=self.sinks[gate];self.source_for_anode[anode]=ref
            self.pullups[ref]=self._resistor_between(gate,'VLED_5V')
            self.bleeds[ref]=self._resistor_between(anode,'GND')
        paths=[];row_uses={}
        for module_idx,p in enumerate(self.modules):
            for col,anode_pin in enumerate(ANODES):
                anode=net(p,anode_pin)
                if anode not in self.source_for_anode:raise CircuitError(f'{p["ref"]} anode pin{anode_pin} has no PMOS source (polarity/wiring error)')
                mosfet=self.source_for_anode[anode]
                for row,cathode_pin in enumerate(CATHODES):
                    cathode=net(p,cathode_pin)
                    if cathode not in self.sinks:raise CircuitError(f'{p["ref"]} cathode pin{cathode_pin} has no current sink')
                    if cathode in self.source_for_anode:raise CircuitError('Cathode shorted to a sourced anode')
                    sink=self.sinks[cathode]
                    if sink in self.gates.values():raise CircuitError('A row cathode is wired to a PMOS gate sink')
                    row_uses.setdefault(sink,set()).add((module_idx,row))
                    paths.append(PixelPath(p['ref'],module_idx*5+col,row,anode_pin,cathode_pin,mosfet,self.gates[mosfet],sink))
        if len(row_uses)!=49 or any(len(v)!=1 for v in row_uses.values()):
            raise CircuitError('Shared cathode aliases physical rows; current would divide between LEDs')
        self.paths=tuple(paths)
        if len({(p.x,p.y) for p in paths})!=245:raise CircuitError('Pixel geometry is not245 unique diodes')
        self.row_sinks=frozenset(row_uses)
        self.used_sinks=frozenset(self.row_sinks|set(self.gates.values()))
        self.unused_sinks=frozenset(Sink(r,i) for r in self.drivers for i in range(16))-self.used_sinks
        self.peak_a={}
        for ref,p in self.drivers.items():
            r=self._resistor_between(net(p,RGE['IREF']),'GND')
            self.peak_a[ref]=1.205*41.9/r
        self.usb_frontend=self._validate_bc12()

    def _validate_bc12(self):
        matches=[p for p in self.parts.values()if p.get('mpn')=='BQ24392RSER']
        if len(matches)!=1:raise CircuitError('Expected one physical BQ24392 USB isolation/detector')
        p=matches[0]
        expected={'SW_OPEN':None,'DM_HOST':'USB_DM_HOST','DP_HOST':'USB_DP_HOST',
                  'CHG_AL_N':'BC_AL_N','GOOD_BAT':'+3V3','GND':'GND',
                  'DP_CON':'USB_DP','DM_CON':'USB_DM','VBUS':'+5V','CHG_DET':'BC_DET_5V'}
        for name,n in expected.items():
            if self.net(p,BQ_RSE[name])!=n:raise CircuitError('BQ physical '+name+' terminal has wrong net')
        for ref,n in [('J11','USB_DM_HOST'),('J12','USB_DP_HOST'),('J17','USB_DM'),
                      ('J18','USB_DP'),('J19','BC_DET'),('J20','BC_AL_N')]:
            if self.net(self.parts[ref],1)!=n:raise CircuitError('BQ wire-pad path bypassed or miswired at '+ref)
        upper=self._resistor_between('BC_DET_5V','BC_DET')
        lower=self._resistor_between('BC_DET','GND')
        pullup=self._resistor_between('BC_AL_N','+3V3')
        # Bound1% divider parts and1uA RP2040 input leakage against manufacturer
        # CHG_DET3.5Vmin/5.25Vmax and RP2040 VIH2.0V, not0.7*VDD.
        low_ratio=lower*.99/(upper*1.01+lower*.99)
        high_ratio=lower*1.01/(upper*.99+lower*1.01)
        leakage_drop=1e-6*(upper*1.01*lower*1.01)/(upper*1.01+lower*1.01)
        high_min=3.5*low_ratio-leakage_drop
        high_max=5.25*high_ratio+leakage_drop
        low_max=.4*high_ratio+leakage_drop
        if high_min<2 or high_max>3.3*.975 or low_max>.8:
            raise CircuitError('BC status divider violates conservative RP2040 logic/voltage limits')
        if pullup!=10000:raise CircuitError('BQ CHG_AL_N requires10k pullup on always3V3')
        return {'detector':p['ref'],'physical_map':'BQ24392 RSE0010A RevG',
                'raw_usb_pair_isolated_from_mcu_pair':True,'good_bat_always3V3':True,
                'BC_DET_high_min_V':round(high_min,6),'BC_DET_high_max_V':round(high_max,6),
                'BC_DET_low_max_V':round(low_max,6),'CHG_AL_N_pullup_ohm':pullup,
                'note':'Connectivity and static logic levels only;no charger/USB transactions simulated.'}

    def _resistor_between(self,a,b):
        matches=[p for p in self.parts.values() if p['ref'].startswith('R') and set(p['pins'].values())=={a,b}]
        if len(matches)!=1:raise CircuitError(f'Expected one resistor between {a} and {b}')
        return resistance(matches[0]['value'])

    @lru_cache(maxsize=65536)
    def latch_serial(self,serial):
        if len(serial)!=8:raise CircuitError('Exactly64 serial clock bits required')
        # Simulate four16-bit shift registers clocked together, first-to-last.
        # After64 clocks the result is independent of their power-on contents.
        shift={r:0 for r in self.chain}
        for byte in serial:
            for bit in range(7,-1,-1):
                carry=(byte>>bit)&1
                for ref in self.chain:
                    outgoing=(shift[ref]>>15)&1
                    shift[ref]=((shift[ref]<<1)|carry)&65535
                    carry=outgoing
        return tuple(shift[r] for r in self.chain)

    def _enabled(self,latched,sink):
        return bool(latched[self.chain.index(sink.ref)]&(1<<sink.output))

    @lru_cache(maxsize=65536)
    def decode_serial(self,serial,blank=False,driver_power=True,vled_power=True):
        if not vled_power:return bytes(35)
        if not driver_power:raise CircuitError('VLED powered while TLC unpowered: output state/leakage is not specified')
        if blank:return bytes(35)
        latched=self.latch_serial(serial)
        if any(self._enabled(latched,s) for s in self.unused_sinks):raise CircuitError('Unconnected TLC output set; forbidden extra supply current')
        active=[q for q,g in self.gates.items() if self._enabled(latched,g)]
        if len(active)>1:raise CircuitError('More than one anode column selected; one-hot gate contract violated')
        if not active:
            if any(self._enabled(latched,s) for s in self.row_sinks):raise CircuitError('Row sinks set without a selected column')
            return bytes(35)
        columns=bytearray(35)
        for p in self.paths:
            if p.mosfet==active[0] and self._enabled(latched,p.cathode):columns[p.x]|=1<<p.y
        return bytes(columns)

    def decode_frame(self,phases):
        if len(phases)!=5:raise CircuitError('A complete display frame has5 phases')
        frame=bytearray(35)
        for serial in phases:
            for x,column in enumerate(self.decode_serial(serial)):frame[x]|=column
        return bytes(frame)

    def led_peak_current_a(self,serial):
        frame=self.decode_serial(serial)
        return sum(self.peak_a[p.cathode.ref] for p in self.paths if frame[p.x]&(1<<p.y))
