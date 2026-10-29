#!/usr/bin/env python3
"""Stage the generated data and compile the pinned STM32duino prototype."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "hardware/firmware"
parser = argparse.ArgumentParser()
parser.add_argument("--cli", type=Path, default=Path.home() / ".cache/house-rules-arduino/bin/arduino-cli")
parser.add_argument("--config", type=Path, default=Path.home() / ".cache/house-rules-arduino/arduino-cli.yaml")
args = parser.parse_args()
installed = json.loads(subprocess.check_output([str(args.cli), "core", "list", "--json",
                                               "--config-file", str(args.config)], text=True))
core = next((p for p in installed.get("platforms", []) if p["id"] == "STMicroelectronics:stm32"), {})
if core.get("installed_version") != "3.0.0":
    raise SystemExit("This build requires STM32duino core 3.0.0; run setup.py first.")
cache = Path.home() / ".cache/house-rules-arduino/build"
sketch = cache / "HouseRules"
sketch.mkdir(parents=True, exist_ok=True)
for p in (FIRMWARE / "HouseRules").iterdir():
    if p.suffix in {".ino", ".h", ".cpp", ".c"}: shutil.copy2(p, sketch / p.name)
shutil.copy2(FIRMWARE / "generated_sequence.h", sketch / "generated_sequence.h")
out = FIRMWARE / "compiled"
out.mkdir(exist_ok=True)
fqbn = "STMicroelectronics:stm32:GenG0:pnum=GENERIC_G0B1KBUX,usb=CDCgen,opt=osstd,upload_method=dfuMethod"
command = [str(args.cli), "compile", "--config-file", str(args.config), "--fqbn", fqbn,
           "--build-path", str(cache / "objects"), "--output-dir", str(out),
           "--build-property", "build.extra_flags=-DUSBD_SELF_POWERED=0 -DUSBD_MAX_POWER=250 -DADC_SAMPLINGTIME=ADC_SAMPLETIME_160CYCLES_5",
           "--build-property", "compiler.c.elf.extra_flags=-Wl,--wrap=USBD_Start -Wl,--wrap=USBD_LL_Suspend -Wl,--wrap=USBD_LL_Resume -Wl,--wrap=HAL_PCD_Init -Wl,--wrap=USBD_CDC_init",
           str(sketch)]
print("Compiling STM32G0B1KBUx with bus-powered, 500 mA USB descriptor and BC1.2 hooks.", flush=True)
result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(out / "build.log").write_text(result.stdout)
print(result.stdout)
if result.returncode: raise SystemExit(result.returncode)
metadata = {"arduino_cli": "1.5.1", "stm32_core": "3.0.0", "fqbn": fqbn,
            "usb_bMaxPower": 250, "usb_bus_powered": True, "link_time_optimisation": False,
            "build_command": command, "status": "compiled; hardware untested"}
(out / "build-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
subprocess.run([sys.executable, str(Path(__file__).with_name("audit_elf.py"))], check=True)
