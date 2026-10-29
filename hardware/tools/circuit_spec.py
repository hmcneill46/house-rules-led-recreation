"""Single source of component pins, nets and placement for both KiCad boards.

Positions are millimetres from the top-left board corner, viewed from the front.
The main board is populated on B.Cu; displays are fitted later on F.Cu.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'hardware/kicad'
PARTS = []

def part(board, ref, value, footprint, x, y, pins, *, angle=0, side='B', mpn='', lcsc='', datasheet='', pin_names=None, role='', types=None):
    p = dict(board=board, ref=ref, value=value, footprint=footprint, x=x, y=y,
             angle=angle, side=side, pins={str(k):v for k,v in pins.items()},
             mpn=mpn or value, lcsc=lcsc, datasheet=datasheet,
             pin_names={str(k):v for k,v in (pin_names or {}).items()},
             role=role, types={str(k):v for k,v in (types or {}).items()})
    PARTS.append(p)
    return p

def passive(board, ref, value, a, b, x, y, angle=0, side='B', fp=None, **kwargs):
    lib = 'Resistor_SMD:R_0603_1608Metric' if ref.startswith('R') else 'Capacitor_SMD:C_0603_1608Metric'
    return part(board, ref, value, fp or lib, x, y, {1:a,2:b}, angle=angle, side=side, **kwargs)

def build():
    PARTS.clear()
    # Datasheet nominal lattice; breadboard supports 2.54 mm lead pitch only.
    # All-seven body/pin fit at 12.70 mm module repeat remains a physical check.
    anodes, cathodes = [1,3,10,7,8], [12,11,2,9,4,5,6]
    cs_pins = [30,31,32,1,2,3,4,5,6,7,8,10,11,12,13,14]
    sw_pins = [22,21,20,19,18,17,16,15]
    for m in range(7):
        d, slot = m//2+1, m%2
        pins = {pin:f'D{d}_SW{i+1}' for i,pin in enumerate(anodes)}
        pins.update({pin:f'D{d}_CS{slot*7+i+1}' for i,pin in enumerate(cathodes)})
        names = {pin:f'COL{i+1}_A' for i,pin in enumerate(anodes)}
        names.update({pin:f'ROW{i+1}_K' for i,pin in enumerate(cathodes)})
        part('main', f'DS{m+1}', 'LMD07057AUE-101B', 'HouseRules:LMD07057AUE-101B',
             6.1+12.7*m, 8.65, pins, side='F', mpn='LMD07057AUE-101B',
             datasheet='https://cdn.shopify.com/s/files/1/0695/1347/8453/files/LMD07057AUE.pdf',
             pin_names=names, role='Owner supplied; fit after factory assembly')
    for d,m in enumerate([0,2,4,6],1):
        x=6.1+12.7*m
        pins={p:None for p in range(1,34)}
        nrows=14 if d<4 else 7
        pins.update({p:f'D{d}_CS{i+1}' for i,p in enumerate(cs_pins[:nrows])})
        pins.update({p:f'D{d}_SW{i+1}' for i,p in enumerate(sw_pins[:5])})
        pins.update({9:'GND',24:'GND',33:'GND',23:'+5V',25:f'ISET{d}',26:'SDA',27:'SCL',28:['GND','SCL','SDA','+5V'][d-1],29:'LED_SDB'})
        names={p:f'CS{i+1}' for i,p in enumerate(cs_pins)}
        names.update({p:f'SW{i+1}' for i,p in enumerate(sw_pins)})
        names.update({9:'GND',24:'GND',33:'EP_GND',23:'VCC',25:'ISET',26:'SDA',27:'SCL',28:'AD',29:'SDB'})
        types={p:'passive' for p in range(1,34)}
        types.update({p:'output' for p in cs_pins+sw_pins})
        types.update({9:'power_in',24:'power_in',33:'power_in',23:'power_in',25:'passive',26:'bidirectional',27:'input',28:'input',29:'input'})
        part('main',f'U{d}','IS31FL3729-QFLS4-TR','Package_DFN_QFN:QFN-32-1EP_4x4mm_P0.4mm_EP2.65x2.65mm',x,8.65,pins,
             mpn='IS31FL3729-QFLS4-TR',lcsc='C2940549',pin_names=names,types=types,
             datasheet='https://www.lumissil.com/assets/pdf/core/IS31FL3729_DS.pdf',role=f'LED driver, address 0x{0x33+d:02X}')
        passive('main',f'R{d}','47k 1%',f'ISET{d}','GND',x,13.0)
        passive('main',f'C{2*d-1}','100n 50V X7R','+5V','GND',x-1.5,4.2)
        passive('main',f'C{2*d}','1u 16V X7R','+5V','GND',x+1.5,4.2)
    p={i:None for i in range(1,34)}
    p.update({4:'+3V3',5:'GND',33:'GND',6:'NRST',7:'CC1_ADC',8:'CC2_ADC',15:'LED_SDB',22:'USB_DM',23:'USB_DP',24:'SWDIO',25:'BOOT_SWCLK',30:'SCL',31:'SDA'})
    names={4:'VDD_VDDA',5:'VSS_VSSA',33:'EP_GND',6:'PF2_NRST',7:'PA0_ADC_CC1',8:'PA1_ADC_CC2',15:'PB0_LED_SDB',22:'PA11_USB_DM',23:'PA12_USB_DP',24:'PA13_SWDIO',25:'PA14_BOOT0_SWCLK',30:'PB6_I2C1_SCL',31:'PB7_I2C1_SDA'}
    types={4:'power_in',5:'power_in',33:'power_in',6:'input',7:'input',8:'input',15:'output',22:'bidirectional',23:'bidirectional',24:'bidirectional',25:'input',30:'bidirectional',31:'bidirectional'}
    part('main','U5','STM32G0B1KBU6','Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm',44.2,8.65,p,angle=90,mpn='STM32G0B1KBU6',lcsc='C5159549',pin_names=names,types=types,datasheet='https://www.st.com/resource/en/datasheet/stm32g0b1kb.pdf',role='USB controller / artwork storage')
    part('main','U6','TLV75533PDBVR','Package_TO_SOT_SMD:SOT-23-5',18.8,8.65,{1:'+5V',2:'GND',3:'+5V',4:None,5:'+3V3'},mpn='TLV75533PDBVR',lcsc='C404027',pin_names={1:'IN',2:'GND',3:'EN',4:'NC',5:'OUT'},types={1:'power_in',2:'power_in',3:'input',5:'power_out'},datasheet='https://www.ti.com/lit/ds/symlink/tlv755p.pdf')
    passive('main','C9','1u 16V X7R','+5V','GND',18.8,5.2)
    passive('main','C10','2u2 10V X7R','+3V3','GND',18.8,11.9)
    passive('main','C11','100n 50V X7R','+3V3','GND',44.2,13.0)
    passive('main','C12','100n 50V X7R','NRST','GND',37.85,3.0,90)
    passive('main','C13','1u 16V X7R','+5V','GND',25.15,7.4,90)
    passive('main','R5','2k2 1%','+3V3','SCL',25.15,10.5,90)
    passive('main','R6','2k2 1%','+3V3','SDA',25.15,13.5,90)
    passive('main','R7','100k 1%','LED_SDB','GND',12.45,13.2,90)
    passive('main','R8','10k 1%','NRST','+3V3',42.7,15.6)
    passive('main','R9','10k 1%','BOOT_SWCLK','GND',45.7,15.6)
    passive('main','R10','47k 1%','CC1','CC1_ADC',42.7,2.1)
    passive('main','R11','47k 1%','CC1_ADC','GND',42.7,4.0)
    passive('main','R12','47k 1%','CC2','CC2_ADC',45.7,2.1)
    passive('main','R13','47k 1%','CC2_ADC','GND',45.7,4.0)
    passive('main','R14','2k2 1%','BOOT_BUTTON','BOOT_SWCLK',14.3,0.9,role='BOOT button current limiting; SWD clock stays directly connected to MCU')
    passive('main','F1','750mA PPTC','VBUS','+5V',25.15,3.5,90,fp='Fuse:Fuse_1206_3216Metric',mpn='SMD1206B075TF/16',lcsc='C269118',role='Fault protection, not USB current authorisation')
    for ref,y,a,b,label in [('SW1',2.1,'BOOT_BUTTON','+3V3','BOOT'),('SW2',15.2,'NRST','GND','RESET')]:
        part('main',ref,label,'Button_Switch_SMD:SW_SPST_EVQP7A',18.8,y,{1:a,2:b},mpn='EVQP7A01P')
    harness={1:'VBUS',2:'USB_DM',3:'USB_DP',4:'GND',5:'CC1',6:'CC2','MP':'GND'}
    part('main','J1','USB CARRIER','Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical',69.0,12.2,harness,angle=270,mpn='BM06B-SRSS-TB(LF)(SN)',lcsc='C160392',datasheet='https://www.jst.com/wp-content/uploads/2021/01/eSH.pdf',role='Vertical 6 way straight-numbered harness to carrier; mated body clears LED leads')
    for i,(net,name) in enumerate([('GND','GND'),('+3V3','3V3'),('SWDIO','SWDIO'),('BOOT_SWCLK','SWCLK'),('NRST','NRST')],1):
        part('main',f'TP{i}',name,'TestPoint:TestPoint_Pad_D1.0mm',63.25,3.0+(i-1)*2.54,{1:net},role='SWD recovery test pad; do not externally power 3V3')
    part('main','TP6','5V','TestPoint:TestPoint_Pad_D1.0mm',12.45,8.65,{1:'+5V'})

    # USB carrier: all parts on F.Cu; the carrier sits behind the main board.
    part('usb','J1','USB-C 5V DATA','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',10.7,13.7,
         {'A1':'GND','A4':'VBUS','A5':'CC1','A6':'USB_DP','A7':'USB_DM','A8':None,'A9':'VBUS','A12':'GND','B1':'GND','B4':'VBUS','B5':'CC2','B6':'USB_DP','B7':'USB_DM','B8':None,'B9':'VBUS','B12':'GND','SH':'GND'},side='F',mpn='USB4105-GF-A',lcsc='C3020560',role='5V USB-C sink, USB2 FS data, no PD voltage request')
    part('usb','J2','MAIN BOARD','Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal',3.1,5.0,harness,angle=270,side='F',mpn='SM06B-SRSS-TB(LF)(SN)',lcsc='C160405')
    passive('usb','R1','5k1 1%','CC1','GND',1.4,12.0,90,'F')
    passive('usb','R2','5k1 1%','CC2','GND',4.5,12.0,90,'F')
    passive('usb','C1','100n 50V X7R 0402','VBUS','GND',14.6,2.0,90,'F',fp='Capacitor_SMD:C_0402_1005Metric')
    part('usb','U1','TPD4E05U06DQAR','Package_SON:USON-10_2.5x1.0mm_P0.5mm',8,7.6,
         {1:'USB_DM',2:'USB_DP',3:'GND',4:'CC1',5:'CC2',6:'CC2',7:'CC1',8:'GND',9:'USB_DP',10:'USB_DM'},side='F',angle=270,mpn='TPD4E05U06DQAR',lcsc='C138714',role='ESD shunt; opposite NC pads are externally joined by PCB copper, never assumed internally flow-through')
    part('usb','D1','SMF5.0A','Diode_SMD:D_SOD-123F',14.6,6.3,{1:'VBUS',2:'GND'},side='F',angle=90,mpn='SMF5.0A',lcsc='C151296',role='VBUS ESD transient shunt, not DC overvoltage protection')
    sourced=ROOT/'hardware/reports/passive-parts.json'
    if sourced.exists():
        db=json.loads(sourced.read_text())
        values=db.get('parts',db)
        for item in PARTS:
            key=item['value']
            candidate=values.get(key)
            if candidate:
                item['mpn']=candidate['mpn'];item['lcsc']=candidate['lcsc']
    # Junction pad numbers for USB4105 should always be audited against actual footprint.
    result={'revision':'A1','status':'engineering prototype; physical pin test and bench validation required',
            'boards':{'main':{'width':88.4,'height':17.3,'layers':6,'thickness':1.6},'usb':{'width':16.0,'height':16.8,'layers':4,'thickness':1.0}},'parts':PARTS,
            'harness':{'length_mm':'30-50','pin_order':['VBUS','USB_DM','USB_DP','GND','CC1','CC2'],'rule':'Pin1 to pin1 by number at both ends; verify before connection; keep data pair together'}}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'circuit-spec.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    spec=build()
    print('Components:',{b:sum(p['board']==b for p in PARTS) for b in spec['boards']})
