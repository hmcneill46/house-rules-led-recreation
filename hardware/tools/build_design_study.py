#!/usr/bin/env python3
"""Generate an electrical connection study and nominal front-view drawing.

No physical pad orientation or manufacturing output is inferred here.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "hardware" / "design"
ANODES = [1, 3, 10, 7, 8]
CATHODES = [12, 11, 2, 9, 4, 5, 6]
SW_PINS = [22, 21, 20, 19, 18]
CS_PINS = [30, 31, 32, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    connections, pixels = [], []
    for m in range(7):
        driver, slot = m // 2, m % 2
        for col, pin in enumerate(ANODES):
            connections.append([m + 1, pin, "anode", col + 1, driver + 1,
                                f"SW{col + 1}", SW_PINS[col]])
        for row, pin in enumerate(CATHODES):
            cs = slot * 7 + row
            connections.append([m + 1, pin, "cathode", row + 1, driver + 1,
                                f"CS{cs + 1}", CS_PINS[cs]])
        for col in range(5):
            for row in range(7):
                cs = slot * 7 + row + 1
                pixels.append([m * 5 + col, row, m + 1, driver + 1,
                               f"0x{0x34 + driver:02X}", col + 1, cs,
                               f"0x{col * 16 + cs:02X}"])
    assert len(connections) == 84
    assert len(pixels) == 245
    assert len({(p[3], p[7]) for p in pixels}) == 245, "Pixel address alias"
    assert {(p[0], p[1]) for p in pixels} == {(x, y) for x in range(35) for y in range(7)}
    for name, header, rows in [
        ("module-connections.csv", ["module", "module_pin", "polarity", "visual_axis_index_1based", "driver", "driver_signal", "driver_package_pin"], connections),
        ("pixel-map.csv", ["x_0based", "y_0based", "module_1based", "driver_1based", "i2c_7bit_address", "SW_1based", "CS_1based", "PWM_register"], pixels),
    ]:
        with (OUT / name).open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
    contract = {
        "status": "proposed electrical mapping; actual pin orientation and hardware untested",
        "driver": "IS31FL3729-QFLS4-TR",
        "driver_datasheet": "https://www.lumissil.com/assets/pdf/core/IS31FL3729_DS.pdf",
        "modules_per_driver": [2, 2, 2, 1],
        "address_AD_connections": ["GND", "SCL", "SDA", "VCC"],
        "i2c_7bit_addresses": ["0x34", "0x35", "0x36", "0x37"],
        "scan_phases": 5,
        "ISET_ohms_provisional": 47000,
        "GCC_maximum": "0x40",
        "unused_outputs": "unconnected, PWM/scaling disabled; SW6-8 and CS16/SW9 also unused",
        "support_pins": {"VCC": 23, "GND": [9, 24, "exposed pad"], "ISET": 25, "SDA": 26, "SCL": 27, "AD": 28, "SDB": 29},
        "important": "This is not a complete schematic. Add power, decoupling, shutdown, logic, USB, MCU and test circuitry before layout. Register addresses do not specify an initialization sequence.",
    }
    (OUT / "driver-contract.json").write_text(json.dumps(contract, indent=2) + "\n")

    sequence = json.loads((ROOT / "sequence.json").read_text())
    manifest = json.loads((ROOT / "hardware/firmware/sequence_manifest.json").read_text())
    idx = next(i for i, cmd in enumerate(sequence) if cmd.get("word") == "pleeze")
    cmd = manifest["commands"][idx]
    data = (ROOT / "hardware/firmware/sequence_columns.bin").read_bytes()
    frame = data[cmd["offset"]:cmd["offset"] + 35]
    colors = ["#277e81", "#397ab8", "#8061b4", "#a86c2e"]
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="640" viewBox="0 0 1120 640">',
         '<rect width="1120" height="640" fill="#f4f2eb"/>',
         '<g font-family="Arial, sans-serif" fill="#222">',
         '<text x="60" y="49" font-size="30" font-weight="700">House Rules / physical design study</text>',
         '<text x="60" y="78" font-size="16">Nominal geometry and proposed wiring. Component placement and PCB outline remain to be verified.</text>',
         '<path d="M60 106H1038 M60 100V112 M1038 100V112" stroke="#444"/>',
         '<text x="549" y="101" font-size="15" text-anchor="middle">88.9 mm nominal</text>']
    for m in range(7):
        x = 60 + m * 139.7
        s.append(f'<rect x="{x:.2f}" y="126" width="139.7" height="195.8" fill="#151515" stroke="#666" stroke-width="1"/>')
        for c in range(5):
            for r in range(7):
                on = frame[m * 5 + c] & (1 << r)
                fill = "#ef3e31" if on else "#343434"
                s.append(f'<circle cx="{x + 13.97 + c * 27.94:.2f}" cy="{140.08 + r * 27.94:.2f}" r="10.45" fill="{fill}"/>')
        s.append(f'<text x="{x + 69.85:.2f}" y="347" text-anchor="middle" font-size="15">Module {m + 1}</text>')
    for g, (start, count) in enumerate([(0, 2), (2, 2), (4, 2), (6, 1)]):
        x = 60 + start * 139.7
        w = count * 139.7
        s.extend([f'<path d="M{x + 5:.2f} 359V371H{x + w - 5:.2f}V359" fill="none" stroke="{colors[g]}" stroke-width="3"/>',
                  f'<rect x="{x + 5:.2f}" y="390" width="{w - 10:.2f}" height="75" rx="8" fill="{colors[g]}"/>',
                  f'<text x="{x + w / 2:.2f}" y="418" fill="white" text-anchor="middle" font-size="17">Driver {g + 1}</text>',
                  f'<text x="{x + w / 2:.2f}" y="444" fill="white" text-anchor="middle" font-size="14">I2C 0x{0x34 + g:02X}</text>',
                  f'<path d="M{x + w / 2:.2f} 465V493" stroke="{colors[g]}" stroke-width="2"/>'])
    s.extend(['<path d="M150 493H971" stroke="#555" stroke-width="2"/>',
              '<rect x="450" y="510" width="220" height="55" rx="7" fill="#333"/>',
              '<text x="560" y="544" text-anchor="middle" fill="white" font-size="17">USB-capable controller</text>',
              '<path d="M560 493V510 M300 538H450" stroke="#555" stroke-width="2"/>',
              '<text x="285" y="544" text-anchor="end" font-size="17">USB-C power + data</text>',
              '<text x="60" y="599" font-size="16">All electronics sit behind the display. Driver boxes show electrical groups, not physical chip sizes or positions.</text>',
              '<text x="60" y="624" font-size="14">Seven upright modules touch along their long edges. PCB must remain inside the measured LED envelope.</text>',
              '</g></svg>'])
    (OUT / "physical-concept.svg").write_text("\n".join(s) + "\n")
    print("Generated 84 connections and 245 unique pixel addresses; nominal SVG written.")


if __name__ == "__main__":
    main()
