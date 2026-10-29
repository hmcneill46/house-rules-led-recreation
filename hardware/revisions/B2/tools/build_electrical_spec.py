"""B2 electrical source, intentionally isolated from the A1 generator.

PCB placement is owned by build_pcbs.py; these x/y values are placeholders only.
Run with Python 3. No KiCad dependency is required.
"""
import json
from pathlib import Path

DEST = Path(__file__).resolve().parents[1]
parts = []

def part(ref, value, footprint, pins, *, mpn='', lcsc='', datasheet='', role='', pin_names=None, types=None, assembly='factory', **extra):
    p = dict(board='main', ref=ref, value=value, footprint=footprint, pins={str(k):v for k,v in pins.items()},
             x=0, y=0, angle=0, side='B', mpn=mpn or value, lcsc=lcsc, datasheet=datasheet, role=role,
             pin_names={str(k):v for k,v in (pin_names or {}).items()}, types={str(k):v for k,v in (types or {}).items()}, assembly=assembly)
    p.update(extra); parts.append(p); return p

def passive(ref, value, a, b, mpn, lcsc, role=''):
    lib = 'Resistor_SMD:R_0603_1608Metric' if ref.startswith('R') else 'Capacitor_SMD:C_0603_1608Metric'
    return part(ref, value, lib, {1:a,2:b}, mpn=mpn, lcsc=lcsc, role=role)

def build():
    parts.clear()
    anodes, cathodes = [1,3,10,7,8], [12,11,2,9,4,5,6]
    for m in range(7):
        bank, slot = m//2+1, m%2
        pins = {p:f'COL{i+1}_A' for i,p in enumerate(anodes)}
        pins.update({p:f'D{bank}_ROW{slot*7+i+1}_K' for i,p in enumerate(cathodes)})
        part(f'DS{m+1}', 'LMD07057AUE-101B', 'HouseRules:LMD07057AUE-101B', pins,
             datasheet='https://cdn.shopify.com/s/files/1/0695/1347/8453/files/LMD07057AUE.pdf',
             role='Owner supplied, front fitted after factory assembly', assembly='owner', side='F')
    # DBQR failed native pad-clearance study. RGER has a DIFFERENT pin map;
    # never change only the footprint or MPN to substitute it.
    package_options = {
        'DBQR': {'mpn':'TLC59282DBQR','lcsc':'C129352','footprint':'Package_SO:SSOP-24_3.9x8.7mm_P0.635mm',
                 'signals':{'GND':1,'SIN':2,'SCLK':3,'LAT':4,'BLANK':21,'SOUT':22,'IREF':23,'VCC':24}, 'out_pins':list(range(5,21))},
        'RGER': {'mpn':'TLC59282RGER','lcsc':'C702074','footprint':'TI:RGE0024C',
                 'signals':{'LAT':1,'BLANK':18,'SOUT':19,'IREF':20,'VCC':21,'GND':22,'SIN':23,'SCLK':24,'EP_GND':25}, 'out_pins':list(range(2,18))}
    }
    pkg = package_options['RGER']
    for bank in range(1,5):
        s = pkg['signals']; pins = {p:None for p in range(1,25)}
        pins.update({s['GND']:'GND',s['VCC']:'SW_3V3',s['IREF']:f'IREF{bank}',s['LAT']:'LAT',s['SCLK']:'SCLK',s['BLANK']:'BLANK',
                     s['SIN']:'SIN' if bank == 1 else f'SERIAL_{bank-1}_{bank}',s['SOUT']:f'SERIAL_{bank}_{bank+1}' if bank < 4 else None})
        if 'EP_GND' in s:pins[s['EP_GND']]='GND'
        names = {p:n for n,p in s.items()}
        for i,p in enumerate(pkg['out_pins']):
            names[p] = f'OUT{i}'
            if i < (14 if bank < 4 else 7): pins[p] = f'D{bank}_ROW{i+1}_K'
            elif bank == 4 and 7 <= i <= 11: pins[p] = f'COL{i-6}_GATE'
        part(f'U{bank}',pkg['mpn'],pkg['footprint'],pins,mpn=pkg['mpn'],lcsc=pkg['lcsc'],pin_names=names,
             datasheet='https://www.ti.com/lit/ds/symlink/tlc59282.pdf',role='16-bit current sinks; U4 OUT7..11 also sink PMOS gate current',
             types={**{p:'open_collector' for p in pkg['out_pins']},s['GND']:'power_in',s['VCC']:'power_in',s['IREF']:'passive',s['SIN']:'input',s['SCLK']:'input',s['LAT']:'input',s['BLANK']:'input',s['SOUT']:'output',**({s['EP_GND']:'power_in'} if 'EP_GND' in s else {})})
        passive(f'R{bank}','6k8 1%',f'IREF{bank}','GND','0603WAF6801T5E','C23212','Sets 7.42493mA nominal peak; Basic resistor avoids Extended setup fee')
        passive(f'C{bank}','100n 50V X7R','SW_3V3','GND','CC0603KRX7R9BB104','C14663','Place at corresponding TLC VCC/GND')
    for col in range(1,6):
        part(f'Q{col}','AO3401A','Package_TO_SOT_SMD:SOT-23',{1:f'COL{col}_GATE',2:'VLED_5V',3:f'COL{col}_A'},
             mpn='AO3401A',lcsc='C15127',datasheet='https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf',
             pin_names={1:'G',2:'S',3:'D'},role='High-side common-anode column switch, gate active LOW')
        passive(f'R{4+col}','4k7 1%',f'COL{col}_GATE','VLED_5V','0603WAF4701T5E','C23162','Default OFF; U4 selected gate sink draws about1.06mA')
        passive(f'R{9+col}','10k 1%',f'COL{col}_A','GND','0603WAF1002T5E','C25804','Discharge inactive anode capacitance; 0.5mA selected column overhead')
    passive('R15','4k7 1%','BLANK','SW_3V3','0603WAF4701T5E','C23162','Default blank during MCU reset; no always-on pullup/backfeed')
    passive('R16','100k 1%','DRIVER_EN','GND','0603WAF1003T5E','C25803','Default OFF on MCU reset/high impedance')
    # Both switches must be fitted: VCC=0 output leakage is not specified by TLC.
    for ref, vin, out, ct in [('U5','+3V3','SW_3V3','CT_3V3'),('U6','+5V','VLED_5V','CT_5V')]:
        part(ref,'TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:vin,2:'GND',3:'DRIVER_EN',4:ct,5:out,6:out},
             mpn='TPS22918DBVR',lcsc='C131941',datasheet='https://www.ti.com/lit/ds/symlink/tps22918.pdf',
             pin_names={1:'VIN',2:'GND',3:'ON',4:'CT',5:'QOD',6:'VOUT'},
             types={1:'power_in',2:'power_in',3:'input',4:'passive',5:'passive',6:'power_out'},
             role='Active HIGH rail switch; QOD tied to VOUT, 1nF CT soft start')
    passive('C5','1u 50V X5R','+3V3','GND','CL10A105KB8NNNC','C15849','Input bypass U5')
    passive('C6','1u 50V X5R','+5V','GND','CL10A105KB8NNNC','C15849','Input bypass U6; included in raw VBUS input-capacitance audit')
    passive('C7','1u 50V X5R','SW_3V3','GND','CL10A105KB8NNNC','C15849','Switched TLC bulk bypass')
    passive('C8','4u7 16V X5R','VLED_5V','GND','CL10A475KO8NNNC','C19666','Switched LED bulk bypass; X5R rated-55..85C, account for DC bias in bench ripple test')
    passive('C9','1n 50V X7R','CT_3V3','GND','CL10B102KB8NNNC','C1588','1nF rise-time setting')
    passive('C10','1n 50V X7R','CT_5V','GND','CL10B102KB8NNNC','C1588','1nF rise-time setting')
    for ref,a,b in [('R17','CC1','CC1_ADC'),('R18','CC1_ADC','GND'),('R19','CC2','CC2_ADC'),('R20','CC2_ADC','GND')]:
        passive(ref,'47k 1%',a,b,'0603WAF4702T5E','C25819','CC high-impedance divider; stock USB breakout already carries Rd')
    for ref,net in [('C11','CC1_ADC'),('C12','CC2_ADC')]:
        passive(ref,'10n 50V X7R',net,'GND','0603B103K500NT','C57112','ADC filter')
    part('F1','750mA PPTC','Fuse:Fuse_1206_3216Metric',{1:'VBUS',2:'FUSED_VBUS'},mpn='SMD1206B075TF/16',lcsc='C269118',role='Fault protection only, never grants USB current')
    part('D1','SMF5.0A','Diode_SMD:D_SOD-123F',{1:'VBUS',2:'GND'},mpn='SMF5.0A',lcsc='C151296',role='VBUS ESD transient shunt, not DC overvoltage protection')
    part('U7','TPD4E05U06DQAR','Package_SON:USON-10_2.5x1.0mm_P0.5mm',
         {1:'USB_DM',2:'USB_DP',3:'GND',4:'CC1',5:'CC2',6:'CC2',7:'CC1',8:'GND',9:'USB_DP',10:'USB_DM'},
         mpn='TPD4E05U06DQAR',lcsc='C138714',datasheet='https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf',
         role='4-channel USB data/CC ESD shunt; pads6/7/8/9/10 are external copper joins to matching protected nodes, never assumed internal flow-through')
    part('U8','TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:'FUSED_VBUS',2:'GND',3:'FUSED_VBUS',4:'CT_INPUT',5:'+5V',6:'+5V'},
         mpn='TPS22918DBVR',lcsc='C131941',datasheet='https://www.ti.com/lit/ds/symlink/tps22918.pdf',
         pin_names={1:'VIN',2:'GND',3:'ON',4:'CT',5:'QOD',6:'VOUT'},
         types={1:'power_in',2:'power_in',3:'input',4:'passive',5:'passive',6:'power_out'},
         role='Always enabled from fused VBUS; controlled5V input rise includes stock XIAO capacitance; QOD tiedVOUT')
    passive('C13','1n 50V X7R','CT_INPUT','GND','CL10B102KB8NNNC','C1588','USB input soft start; waveform must be qualified')
    passive('C14','1u 50V X5R','FUSED_VBUS','GND','CL10A105KB8NNNC','C15849','Only raw main VBUS input bulk bypass; downstream capacitances behind controlled-rise U8')
    # Restore A1 BC1.2 CDP/DCP qualification while retaining a USB data path.
    # RSE0010A has TEN lands and no separate EP11, despite retailer EP labels.
    part('U9','BQ24392RSER','Package_DFN_QFN:Texas_UQFN-10_1.5x2mm_P0.5mm',
         {1:None,2:'USB_DM_HOST',3:'USB_DP_HOST',4:'BC_AL_N',5:'+3V3',6:'GND',7:'USB_DP',8:'USB_DM',9:'+5V',10:'BC_DET_5V'},
         mpn='BQ24392RSER',lcsc='C128408',datasheet='https://www.ti.com/lit/ds/symlink/bq24392.pdf',
         pin_names={1:'SW_OPEN',2:'DM_HOST',3:'DP_HOST',4:'CHG_AL_N',5:'GOOD_BAT',6:'GND',7:'DP_CON',8:'DM_CON',9:'VBUS',10:'CHG_DET'},
         types={1:'open_collector',2:'passive',3:'passive',4:'open_collector',5:'input',6:'power_in',7:'passive',8:'passive',9:'power_in',10:'output'},
         role='Automatic BC1.2 detector and USB isolation; GOOD_BAT always3V3, never switched driver rail; CHG_DET is5V logic through divider')
    passive('C15','100n 50V X7R','+5V','GND','CC0603KRX7R9BB104','C14663','Local U9 high-frequency bypass, behind U8 input soft start')
    passive('C16','1u 50V X5R','+5V','GND','CL10A105KB8NNNC','C15849','Local U9 supply bypass, behind U8 input soft start')
    passive('R21','10k 1%','BC_DET_5V','BC_DET','0603WAF1002T5E','C25804','CHG_DET5V upper divider resistor; never wire raw detector output to RP2040')
    passive('R22','15k 1%','BC_DET','GND','0603WAF1502T5E','C22809','Lower detector divider;0.6 ratio gives guaranteed logic HIGH above RP2040 2V VIH')
    passive('R23','10k 1%','BC_AL_N','+3V3','0603WAF1002T5E','C25804','CHG_AL_N open-drain pullup to always3V3; HIGH means no charger grant')
    # Wire pads are soldered by the owner; actual footprint positions owned by PCB generator.
    mcu_nets = ['+5V','GND','+3V3','SIN','SCLK','LAT','BLANK','DRIVER_EN','CC1_ADC','CC2_ADC','USB_DM_HOST','USB_DP_HOST']
    for i,net in enumerate(mcu_nets,1):
        part(f'J{i}',net,'HouseRules:WirePad_B2',{1:net},assembly='owner',role='Owner hand-soldered28AWG wire on rear1.8x1.1mm SMD pad; no drill or paste; wire to XIAO RP2040 Plus')
    for i,net in enumerate(['VBUS','GND','CC1','CC2','USB_DM','USB_DP'],13):
        part(f'J{i}',net,'HouseRules:WirePad_B2',{1:net},assembly='owner',role='Owner hand-soldered28AWG wire on rear1.8x1.1mm SMD pad; no drill or paste; USB breakout data pair runs past U7 ESD shunt')
    for i,net in [(19,'BC_DET'),(20,'BC_AL_N')]:
        part(f'J{i}',net,'HouseRules:WirePad_B2',{1:net},assembly='owner',role='Owner hand-soldered28AWG BC status wire; rear1.8x1.1mm SMD pad; pre-tin and strain-relieve')
    gpio = {'SIN':{'gpio':3,'label':'D10','module_pad':11},'SCLK':{'gpio':2,'label':'D8','module_pad':9},
            'LAT':{'gpio':4,'label':'D9','module_pad':10},'BLANK':{'gpio':28,'label':'D2','module_pad':3},
            'DRIVER_EN':{'gpio':6,'label':'D4','module_pad':5},'CC1_ADC':{'gpio':26,'label':'D0','module_pad':1},
            'CC2_ADC':{'gpio':27,'label':'D1','module_pad':2},
            'BC_DET':{'gpio':7,'label':'D5','module_pad':6},'BC_AL_N':{'gpio':0,'label':'D6','module_pad':7}}
    result = {'revision':'B2','status':'engineering prototype; not released for manufacture',
      'boards':{'main':{'width':88.4,'height':17.3,'layers':6,'thickness':1.6,
               'placement_owner':'root PCB generator/finalizer; x/y here placeholders; do not regenerate routed PCB from placement seed',
               'via_process':{'drill_mm':0.30,'majority_pad_mm':0.60,'selected_escape_pad_mm':0.45,
                              'cover':'All0.30mm vias epoxy filled and capped; includes exposed-pad thermal vias',
                              'thermal_vias':{'total':12,'per_driver':3,'net':'GND'},
                              'owner_led_holes':{'count':84,'drill_mm':0.90,'filled':False,'requirement':'Keep every LED through-hole open'}},
               'plane_intent':{'In2.Cu':'Primarily GND with CT_5V timing-capacitor bridge only, maximum12mm; GND fill remains connected',
                               'In4.Cu':'GND only, unbroken USB reference',
                               'In3.Cu':'Signals including USB plus GND fill'},
               'quiet_plane_exception':{'net':'CT_5V','layer':'In2.Cu','maximum_total_length_mm':12.0,
                    'validated_reference_length_mm':9.753863,'validated_reference_segments':19,
                    'new_vias':0,'track_width_mm':0.11,'copper_clearance_mm':0.15,
                    'reason':'Existing CT captures could not escape through four signal layers; quiet load-switch timing-capacitor bridge only. No USB/clock/other plane exceptions.',
                    'ground_requirement':'In2 filled GND remains one connected outline; In4 remains GND-only'},
               'historical_cost_study':'Four-layer prices are retained as an earlier alternative study, not the selected fabrication process'}},
      'driver_package':'RGER','driver_package_options':package_options,'parts':parts,'gpio':gpio,
      'owned_module_verification':{'date':'2026-10-29','source':'reports/owner-led-diode-test-2026-10-29.json',
          'module_marking':'LMD07057AUE-101B-02','verified_module_count':1,'remaining_unverified_count':20,
          'method':'Owner-reported diode-test observations: eleven independent lit dots cover all12 terminals',
          'front_orientation':'Printed part-number label on LEFT with seven-dot axis vertical and chosen TOP uppermost',
          'left_to_right_positive_anodes':[1,3,10,7,8],
          'top_to_bottom_negative_cathodes':[12,11,2,9,4,5,6],
          'pin_graph_change_required':False,'powered_board_validation':False},
      'mcu_wire_pads':{**{f'J{i}':{'net':net,'xiao_pad':14 if net=='+5V' else 13 if net=='GND' else 12 if net=='+3V3' else 'TP12' if net=='USB_DM_HOST' else 'TP4' if net=='USB_DP_HOST' else gpio[net]['module_pad']} for i,net in enumerate(mcu_nets,1)},
                       **{f'J{i}':{'net':net,'xiao_pad':gpio[net]['module_pad']} for i,net in [(19,'BC_DET'),(20,'BC_AL_N')]}},
      'usb_breakout_wire_pads':{f'J{i}':{'net':net,'breakout_pad':bp} for i,(net,bp) in enumerate([('VBUS',2),('GND',1),('CC1',4),('CC2',8),('USB_DM',3),('USB_DP',5)],13)},
      'usb_data_wires':{'D+':{'breakout_pad':5,'main_raw_pad':'J18','raw_net':'USB_DP','detector_upstream_pin':7,'detector_downstream_pin':3,'host_net':'USB_DP_HOST','main_mcu_pad':'J12','xiao_pad':'TP4'},'D-':{'breakout_pad':3,'main_raw_pad':'J17','raw_net':'USB_DM','detector_upstream_pin':8,'detector_downstream_pin':2,'host_net':'USB_DM_HOST','main_mcu_pad':'J11','xiao_pad':'TP12'}},
      'bc12':{'detector':'U9','mpn':'BQ24392RSER','datasheet':'https://www.ti.com/lit/ds/symlink/bq24392.pdf',
              'good_bat':'Always-on +3V3 hard tie; keeps SDP/CDP USB switches connected during display-rail shutdown and host suspend',
              'supply':'+5V after U8 input soft start, never VLED_5V','sw_open':'Pin1 intentionally no-connect; switch closes automatically for SDP/CDP when GOOD_BAT HIGH',
              'detector_logic':'CHG_DET HIGH is3.5V..VBUS; R21/R22 translate it to BC_DET; CHG_AL_N open-drain LOW means allowed',
              'gpio':{'BC_DET':7,'BC_AL_N':0},'data_contact_detection_timeout_ms':600,'detection_debounce_min_ms':130,'stable_qualification_ms':100,
              'grant_rule':'Grant project500mA/full brightness only for BC_DET HIGH AND BC_AL_N LOW after a positive stable detector state; real host suspend overrides BC and CC',
              'truth_table':[{'BC_AL_N':0,'BC_DET':0,'result':'Low-current/SDP or unqualified; no BC high-current grant; configured host or CC handled independently'},
                             {'BC_AL_N':0,'BC_DET':1,'result':'Positive high-current charger classification; cap project current at500mA'},
                             {'BC_AL_N':1,'BC_DET':0,'result':'Charging not allowed by detector; withdraw BC grant immediately'},
                             {'BC_AL_N':1,'BC_DET':1,'result':'Charging not allowed/inconsistent; fail closed, never grant500mA'}],
              'source_classes_good_bat_high':{'SDP':{'AL_N':0,'DET':0,'usb_switch':'closed'},'CDP':{'AL_N':0,'DET':1,'usb_switch':'closed'},'DCP':{'AL_N':0,'DET':1,'usb_switch':'open'},'Apple_or_TomTom':{'AL_N':0,'DET':1,'usb_switch':'open'},'noncompliant_or_PS2':{'AL_N':0,'DET':0,'usb_switch':'open'},'VBUS_invalid':{'AL_N':1,'DET':0,'usb_switch':'open'}},
              'qualification_notes':'Power-up/reset begins unqualified; require valid stable status before raising load; withdraw on either status changing. Slow insertion beyond600ms can conservatively remain dim.'},
      'protocol':{'bits':64,'chain':['U1','U2','U3','U4'],'wire_word_order':['U4','U3','U2','U1'],'wire_bit_order':'MSB first (OUT15 first within each word)',
                  'row_bits':[list(range(0,14)),list(range(16,30)),list(range(32,46)),list(range(48,55))],
                  'column_gate_bits':[55,56,57,58,59],'unused_bits':[14,15,30,31,46,47,60,61,62,63],
                  'gate_bit_polarity':'1=sink enabled=PMOS gate LOW=column ON; exactly one gate bit in active phases',
                  'row_bit_polarity':'1=cathode sink ON','blank_polarity':'HIGH=all outputs OFF','latch':'level-sensitive HIGH, LOW while shifting; pulse HIGH then LOW while BLANK is HIGH'},
      'scan':{'frame_hz':400,'phases':5,'phase_us':500,'blank_min_us':30,'full_on_us':470,'peak_led_mA':1.205*41.9/6.8,
              'default':'Prototype unknown-source DIM at25us light per500us phase; measured<100mA budget not yet qualified; compile-time unknown-source OFF alternative available','unknown_source_on_us':25,'initial_rail_settle_ms':10},
      'power':{'usb_voltage_V':5,'pd_requested':False,'raw_input_fuse_mA':750,'rated_usb_configuration_mA':500,
               'input_soft_start':{'ref':'U8','mpn':'TPS22918DBVR','input':'FUSED_VBUS','output':'+5V','enable':'FUSED_VBUS','ct_pF':1000,'raw_main_input_cap_uF':1.0,'typical_5V_rise_us':2540,'qualification':'Measure whole assembly USB input current/charge, including stock XIAO mux and LDO startup'},
               'switched_rails':['SW_3V3','VLED_5V'],'switch_enable_gpio':6,'initial_output_state':'DRIVER_EN pulled LOW; both LED rails OFF',
               'suspend':'BLANK HIGH; wait>=30us; SIN/SCLK/LAT LOW; BLANK input high-Z no pulls; DRIVER_EN LOW; MCU USB suspend/clock/power policy still requires bench qualification',
               'wake':'BLANK input high-Z no pulls; SIN/SCLK/LAT LOW; DRIVER_EN HIGH; wait>=10ms; BLANK HIGH; shift/latch 64 zero bits; begin authorized scan',
               'off_input_rule':'Never drive a logic HIGH into an unpowered TLC; BLANK pullup is to SW_3V3 only'},
      'release_gates':['Confirm current JLC assembly availability including adequate TLC and BQ stock','QFN pad-map and ordinary-via routing/thermal proof','USB inrush and suspend bench qualification including BQ and10k status pullup','BC1.2 SDP/CDP/DCP classification, data isolation and USB programming through U9','Scope gate/anode off within30us and no ghosting','Measure full-white current and enclosed-board temperatures','Check other20 LED modules against owner-verified full terminal map and orientation; complete full-size body/pin fit and powered245-pixel test']}
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'electrical-spec.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'B2: {len(parts)} parts, {sum(p["assembly"]=="factory" for p in parts)} factory SMT parts, package={result["driver_package"]}')
    return result

if __name__=='__main__': build()
