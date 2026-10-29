#!/usr/bin/env python3
"""Verify USB descriptor bytes and linker hooks in the actual ARM ELF."""
import hashlib
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "hardware/firmware/compiled"
ELF = OUT / "HouseRules.ino.elf"
PREFIX = Path.home() / ".cache/house-rules-arduino/data/packages/STMicroelectronics/tools/xpack-arm-none-eabi-gcc/14.2.1-1.1/bin/arm-none-eabi-"
data = ELF.read_bytes()
header = struct.unpack_from("<16sHHIIIIIHHHHHH", data)
assert header[0][:7] == b"\x7fELF\x01\x01\x01", "Expected little-endian ELF32"
sections = [struct.unpack_from("<IIIIIIIIII", data, header[6] + i * header[11]) for i in range(header[12])]
strings = sections[header[13]]
names = data[strings[4]:strings[4] + strings[5]]
ds = next(s for s in sections if names[s[0]:].split(b"\0")[0] == b".data")
nm = subprocess.check_output([str(PREFIX) + "nm", str(ELF)], text=True)
address = int(re.search(r"([0-9a-f]+) d USBD_CDC_CfgFSDesc", nm).group(1), 16)
start = ds[4] + address - ds[3]
descriptor = data[start:start + 9]
assert descriptor[:2] == bytes([9, 2]) and descriptor[7] == 0x80 and descriptor[8] == 250, descriptor.hex()
pinmap_address = int(re.search(r"([0-9a-f]+) [rRVv] PinMap_USB(?:_DRD_FS)?$", nm, re.M).group(1), 16)
pinmap_section = next(s for s in sections if s[3] <= pinmap_address < s[3] + s[5] and s[1] != 8)
pinmap_start = pinmap_section[4] + pinmap_address - pinmap_section[3]
pin1 = struct.unpack_from("<I", data, pinmap_start)[0]
pin2 = struct.unpack_from("<I", data, pinmap_start + 12)[0]
assert (pin1, pin2) == (11, 12), (pin1, pin2)
disassembly = subprocess.check_output([str(PREFIX) + "objdump", "-d", str(ELF)], text=True)

def body(name):
    found = re.search(r"^\w+ <" + name + r">:\n(.*?)(?=\n\w+ <|\Z)", disassembly, re.M | re.S)
    assert found, name
    return found.group(1)

checks = [("hw_config_init", "__wrap_USBD_CDC_init"),
          ("setup", "_ZN9USBSerial5beginEv"),
          ("_ZN9USBSerial5beginEv", "CDC_init"),
          ("loop", "_Z20handleSerialCommandsv"),
          ("CDC_init", "__wrap_USBD_Start"),
          ("USBD_LL_Init", "USBD_reenumerate"),
          ("USBD_LL_Init", "__wrap_HAL_PCD_Init"),
          ("HAL_PCD_SuspendCallback", "__wrap_USBD_LL_Suspend"),
          ("HAL_PCD_ResumeCallback", "__wrap_USBD_LL_Resume"),
          ("__wrap_USBD_Start", "HAL_PCDEx_BCD_VBUSDetect")]
for caller, callee in checks:
    assert "<" + callee + ">" in body(caller), (caller, callee)
assert "<CDC_init>" not in body("__wrap_USBD_CDC_init")
assert "<USB_DevConnect>" not in body("USBD_reenumerate")
report = ("USB full-speed configuration bytes: " + descriptor.hex(" ")
          + "\nBus powered: bmAttributes=0x80; bMaxPower=250 x 2 mA=500 mA.\n"
          + "Actual USB pin-map entries: PA_11=11, PA_12=12, no PREMAP flag.\n"
          + "Automatic premain USB start is a no-op; setup starts CDC after pin/CC preparation.\n"
          + "The strong re-enumeration helper detaches only; no pre-BCD reconnect.\n"
          + "Link-wrapper call-flow verified in actual ARM ELF:\n"
          + "\n".join(f"- {a} -> {b}" for a, b in checks) + "\n"
          + "\nSHA-256:\n" + "\n".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name
                                             for p in sorted(OUT.glob("HouseRules.ino.*"))) + "\n")
(OUT / "elf-audit.txt").write_text(report)
print(report)
