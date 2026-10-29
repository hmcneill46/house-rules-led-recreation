#!/usr/bin/env python3
"""Inspect the built RP2040 image, UF2 records and linked USB startup path."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cache',type=Path,default=Path.home()/'.cache/house-rules-b2-arduino');a=ap.parse_args()
    out=a.output;uf2=out/'HouseRulesB2.ino.uf2';elf=out/'HouseRulesB2.ino.elf';binary=out/'HouseRulesB2.ino.bin'
    metadata=json.loads((out/'build-metadata.json').read_text())
    gcc=next((a.cache/'data/packages/rp2040/tools/pqt-gcc').glob('*/bin'))
    symbols=subprocess.check_output([str(gcc/'arm-none-eabi-nm'),'-C',str(elf)],text=True)
    asm=subprocess.check_output([str(gcc/'arm-none-eabi-objdump'),'-d','--demangle',str(elf)],text=True)
    def function(name):
        match=re.search(r'^\w+ <'+re.escape(name)+r'>:\n.*?(?=\n\n|\Z)',asm,re.M|re.S)
        assert match,name
        return match.group(0)
    strong=['initVariant','setup','__wrap_TinyUSB_Device_Init','tud_mount_cb','tud_umount_cb','tud_suspend_cb','tud_resume_cb']
    assert not re.search(r'^\w+ T (setup1|loop1)$',symbols,re.M),'Second core must remain parked'
    for name in strong:assert re.search(r'^\w+ T '+re.escape(name)+r'$',symbols,re.M),name
    snippets={name:function(name) for name in ['setup','main','initVariant','__wrap_TinyUSB_Device_Init','(anonymous namespace)::observeUsbBus()']}
    assert '<__wrap_TinyUSB_Device_Init>' in snippets['main']
    assert '<TinyUSB_Device_Init>' not in snippets['main']
    assert re.search(r'bx\s+lr',snippets['__wrap_TinyUSB_Device_Init'])
    assert '<set_sys_clock_48mhz>' in snippets['initVariant']
    # Actual machine code configures descriptor bytes7/8 under PRIMASK:80,FA.
    setup=snippets['setup'];i_disable=setup.index('cpsid');i_restore=setup.index('msr\tPRIMASK')
    protected=setup[i_disable:i_restore]
    assert 'Adafruit_USBD_Device::begin' in protected
    assert protected.index('Adafruit_USBD_Device::begin')<protected.index('irq_add_shared_handler')
    irq_source=(a.cache/'data/packages/rp2040/hardware/rp2040/6.3.1/pico-sdk/src/rp2_common/hardware_irq/irq.c').read_text()
    assert 'while (cur_slot->priority > order_priority)' in irq_source
    assert re.search(r'movs\s+r\d+, #128',protected)
    assert re.search(r'movs\s+r\d+, #250',protected)
    assert re.search(r'strb\s+r\d+, \[r\d+, #7\]',protected)
    assert re.search(r'strb\s+r\d+, \[r\d+, #8\]',protected)
    template=bytes.fromhex('09 02 09 00 00 01 00 a0 fa')
    image=binary.read_bytes();template_offset=image.find(template);assert template_offset>=0
    records=uf2.read_bytes();assert len(records)%512==0
    count=len(records)//512;addresses=[];payloads={}
    for i in range(count):
        block=records[i*512:(i+1)*512]
        magic0,magic1,flags,address,length,index,total,family=struct.unpack_from('<8I',block)
        assert (magic0,magic1)==(0x0a324655,0x9e5d5157)
        assert struct.unpack_from('<I',block,508)[0]==0x0ab16f30
        assert flags&0x2000 and family==0xe48bff56
        assert length==256 and index==i and total==count
        assert 0x10000000<=address<0x10200000 and address+length<=0x10200000
        assert address not in payloads
        addresses.append(address);payloads[address]=block[32:32+length]
    assert addresses==list(range(0x10000000,0x10000000+count*256,256))
    recovered=b''.join(payloads[address] for address in addresses)
    assert recovered[:len(image)]==image
    header=elf.read_bytes()[:52];assert header[:7]==b'\x7fELF\x01\x01\x01'
    assert struct.unpack_from('<H',header,18)[0]==40 # EM_ARM
    entry=struct.unpack_from('<I',header,24)[0];assert 0x10000000<=entry<0x10200000
    assert metadata['effective_cpu_hz']==48000000 and metadata['flash_bytes']==2097152
    for name,code in snippets.items():(out/(re.sub(r'[^A-Za-z0-9_-]','_',name.replace('__',''))+'-disassembly.txt')).write_text(code+'\n')
    report={'result':'PASS','target':'RP2040; XIAO RP2040 Plus2MB','uf2_blocks':count,
      'uf2_family_id':'0xe48bff56','flash_range_hex':[hex(addresses[0]),hex(addresses[-1]+256)],
      'elf_entry_hex':hex(entry),'usb_descriptor_max_current_ma':500,'usb_descriptor_attributes_hex':'0x80',
      'actual_binary_config_template_offset':template_offset,
      'usb_proof':'Linked main calls an empty wrapped early USB initializer; setup writes RAM descriptor attributes0x80 and maxPower0xFA between interrupt-disable/restore, after TinyUSB begin.',
      'strong_usb_callbacks':strong,'cpu48MHz_init_hook':True,'usb_pre_enumeration_suspend_observer':True,'unknown_source_dim_enabled':metadata['unknown_source_dim_enabled'],
      'uf2_sha256':hashlib.sha256(records).hexdigest(),
      'limitations':'Static binary audit only. No USB host capture, physical flashing, light output or electrical/suspend current measurement has been performed.'}
    (out/'binary-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
