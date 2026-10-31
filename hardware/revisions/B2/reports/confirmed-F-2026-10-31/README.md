# Confirmed F geometry — 31 October 2026

The owner printed the fine fitting strips and selected **F / P12.875 / +0.175**. The revised electronics and case use that nominal module pitch. This replaces the earlier 12.700 mm spacing assumption; it does not change the individual 12-hole pattern, polarity, scan map or program.

| Item | Earlier B2 | Confirmed F |
|---|---:|---:|
| Module centre pitch | 12.700 mm | **12.875 mm** |
| Increase across six joins | — | **1.050 mm** |
| PCB | 88.400 × 17.300 × 1.600 mm | **89.450 × 17.300 × 1.600 mm** |
| Case exterior | 93.600 × 22.600 × 24.000 mm | **94.650 × 22.600 × 24.000 mm** |
| Factory components | 55 | **55**, same exact parts |
| LED mounting holes | 84 open Ø0.90 mm | **84 open Ø0.90 mm**, same individual patterns |
| Through vias | 276 filled/capped Ø0.30 mm | **276**, same process |

DS1 stays fixed. DS2…DS7 move right by 0.175/0.350/0.525/0.700/0.875/1.050 mm. The PCB retains its original inset behind the nominal LED silhouette. Stock MCU and USB breakout poses stay fixed, preserving the port position; one upper internal PCB support moves 0.8 mm to clear the relocated J12 solder pad. The case uses a separate conservative 12.9 × 18.0 mm housing clearance allowance based on the owner's approximate measurements.

## Routing and electrical checks

The update moves every component footprint rigidly. It widens only the clear X corridors between existing component banks and splits crossing tracks at mapping boundaries. This preserves the routed topology and every track width/layer, with no new vias or relaxed rules. The exact source and mapping are recorded in [pitch-update.json](pitch-update.json); [apply_confirmed_pitch.py](../../tools/apply_confirmed_pitch.py) reproduces a candidate from the frozen earlier manufacturing snapshot. A candidate still needs native DRC before promotion.

- Fresh native KiCad DRC: **0 violations, 0 unconnected items, 0 schematic parity issues**.
- Native schematic ERC: **0 violations**, all **82 references / 327 connected pins** match.
- Frozen-source comparison: all 84 LED terminals are the original per-module patterns plus exact integer translations, with the same orientation, pads, nets and open drills.
- Six-layer 1.6 mm board, 55 factory parts, 276 ordinary filled/capped vias and 12 driver thermal vias retained. No custom DRC exclusions added.
- Physical drill-edge clearances include same-net pairs: **0.482589 mm minimum via-to-LED** (required 0.45) and **0.265685 mm minimum via-to-via** (required 0.25).
- In4 stays GND-only. In2's timing-capacitor connection is **9.856275 mm** (maximum 12); both ground fills remain connected.
- Independent checks inspect the actual exported **84 LED and 276 via drill coordinates**, **89.45 × 17.3 mm Gerber outline**, 55-part BOM/CPL, native placement angles, and all package hashes.
- Fresh host/model tests reproduce **60,000 artwork frames and all 245 pixels**; the independent model reconstructs 301,235 phases and detects 12 injected faults. Both existing compiled UF2/BIN/ELF variants pass source/binary audits. Firmware sources and images are unchanged.

The main evidence is [final-verification-summary.json](../final-verification-summary.json), [independent-hardware-verification.json](independent-hardware-verification.json), [software-verification-summary.json](software-verification-summary.json), [native DRC](../final-drc.json), [native PCB audit](../board-audit.json), and [mechanical verification](../../mechanical/geometry-verification.json). These are software/CAD checks, not measurements of powered hardware.

## Use these files

- [Current editable PCB](../../kicad/house-rules-main-B2.kicad_pcb), [schematic](../../kicad/house-rules-main-B2.kicad_sch), [native board renders](../../render/).
- [New fabrication and assembly review package](../../manufacturing/B2_F_12p875_review_2026-10-31/README.md), including Gerbers, drill files, exact BOM/CPL and portable source snapshot.
- [Revised case models and assembly guide](../../mechanical/README.md).
- [Ender-3 V3 KE / 0.4 mm / grey Hyper PLA case and fit-test G-code](../../printing/2026-10-31-confirmed-F/README.md). Earlier print files are preserved separately.

The original `manufacturing/B2_review/` package remains byte-for-byte historical at 12.700 mm pitch. Earlier current reports are retained in `reports/pre-confirmed-F-2026-10-31/`; software reports have their own dated `software-before/` snapshot. The old case source/models are in `mechanical/archive-12p700-2026-10-29/`, with their original print projects/G-code preserved.

## Before ordering

Print the new fit/case parts and check the actual purchased MCU, USB breakout and cable. Check the other two seven-module groups against the selected geometry. Obtain a **fresh quote for the new package**; the 29 October prices use the earlier board. Factory review must confirm pin1/rotations, exact parts, removable external assembly rails, all vias filled/capped and all LED holes open. First-board current, USB/programming, scan/ghosting and enclosed temperature tests remain in the [assembly guide](../../assembly-and-test.md). No order, payment or remote print has been submitted.
