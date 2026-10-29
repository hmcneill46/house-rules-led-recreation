#!/usr/bin/env python3
"""Build B2 only, with pinned Arduino-Pico, 2MB flash and effective 48MHz CPU."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from generate_contract import generate
from setup import CORE_SHA256

B2=Path(__file__).resolve().parents[2]
FIRMWARE=B2/'firmware'
FQBN='rp2040:rp2040:seeed_xiao_rp2040:flash=2097152_0,usbstack=tinyusb'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cli',type=Path,default=Path.home()/'.cache/house-rules-arduino/bin/arduino-cli')
    ap.add_argument('--cache',type=Path,default=Path.home()/'.cache/house-rules-b2-arduino')
    ap.add_argument('--unknown-off',action='store_true',help='Keep LEDs off until USB500mA, Type-C or BC1.2 charging qualification')
    args=ap.parse_args();generate();config=args.cache/'arduino-cli.yaml'
    cli_version=json.loads(subprocess.check_output([str(args.cli),'version','--format','json'],text=True))
    if cli_version.get('VersionString')!='1.5.1':raise SystemExit('B2 requires Arduino CLI1.5.1')
    platforms=json.loads(subprocess.check_output([str(args.cli),'core','list','--json','--config-file',str(config)],text=True))
    core=next((p for p in platforms.get('platforms',[]) if p['id']=='rp2040:rp2040'),{})
    if core.get('installed_version')!='6.3.1':raise SystemExit('Run setup.py for Arduino-Pico6.3.1 first')
    archive=args.cache/'downloads/packages/rp2040-6.3.1.zip'
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest()!=CORE_SHA256:
        raise SystemExit('Pinned core archive hash verification failed; rerun setup.py')
    source_paths=[p for p in sorted(FIRMWARE.rglob('*')) if p.is_file() and
         (p.parent==FIRMWARE/'HouseRulesB2' or p.name in {'scan-map.json','generated_sequence.h','sequence_columns.bin','sequence_manifest.json'})]
    source_hashes={str(p.relative_to(FIRMWARE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    sketch=args.cache/'build/HouseRulesB2';sketch.mkdir(parents=True,exist_ok=True)
    for p in (FIRMWARE/'HouseRulesB2').iterdir():
        if p.suffix in {'.ino','.h','.cpp','.c'}:shutil.copy2(p,sketch/p.name)
    shutil.copy2(FIRMWARE/'generated_sequence.h',sketch/'generated_sequence.h')
    out=FIRMWARE/('compiled-unknown-off' if args.unknown_off else 'compiled');out.mkdir(exist_ok=True)
    properties={'build.f_cpu':'48000000L','compiler.cpp.extra_flags':'-DUSB_CONFIG_POWER=500 -DHR_ALLOW_UNCONFIGURED_DIM='+str(int(not args.unknown_off)),
                'compiler.c.extra_flags':'-DUSB_CONFIG_POWER=500',
                'compiler.c.elf.extra_flags':'-Wl,--wrap=TinyUSB_Device_Init'}
    cmd=[str(args.cli),'compile','--config-file',str(config),'--fqbn',FQBN,
         '--build-path',str(args.cache/('objects-unknown-off' if args.unknown_off else 'objects')),'--output-dir',str(out)]
    for key,value in properties.items():cmd+=['--build-property',key+'='+value]
    cmd.append(str(sketch))
    result=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'build.log').write_text(result.stdout);print(result.stdout)
    if result.returncode:raise SystemExit(result.returncode)
    if any(hashlib.sha256((FIRMWARE/name).read_bytes()).hexdigest()!=digest for name,digest in source_hashes.items()):
        raise SystemExit('Firmware sources changed during compilation; rerun build.py before using the image')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in {'.uf2','.elf','.bin'}}
    metadata={'revision':'B2','arduino_cli':'1.5.1','arduino_pico_core':'6.3.1','fqbn':FQBN,
              'effective_cpu_hz':48000000,'flash_bytes':2097152,'usb_stack':'Adafruit TinyUSB',
              'usb_bus_powered':True,'usb_max_power_ma':500,'unknown_source_dim_enabled':not args.unknown_off,
              'status':'compiled prototype; no physical hardware executed; source/suspend current budgets unvalidated',
              'command':cmd,'sha256':hashes,
              'source_sha256':source_hashes}
    (out/'build-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    subprocess.run([sys.executable,str(Path(__file__).with_name('audit_binary.py')),'--output',str(out),'--cache',str(args.cache)],check=True)

if __name__=='__main__':main()
