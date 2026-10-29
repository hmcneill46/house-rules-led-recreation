# Independent electrical and placement review

Review date: 29 October 2026. This review covers package pin assignments, intended net mapping and placement geometry. It does **not** qualify the prototype for fabrication by itself. The accompanying JSON records the specification and PCB SHA-256 hashes of the inspected snapshot.

## Results

| Check | Result |
| --- | --- |
| Main schematic ERC | 0 violations; no exclusions |
| USB schematic ERC | 0 violations; no exclusions |
| Main schematic exported netlist | All 277 connected pins match the shared specification |
| USB schematic exported netlist | All 36 connected pins match the shared specification |
| PCB numbered package pads | No missing package-pin definitions or pad/net mismatches on either board |
| MCU supply and selected functional pins | Match the installed official KiCad STM32G0B1KBUx symbol family |
| Four LED driver pin maps | Match the Lumissil QFN-32 pin table |
| Seven display electrical maps | All 245 pixels have the intended independent grouped mapping |
| USB-C A/B contacts and shield | Correct intended power/data/CC net assignments for both plug orientations |
| Harness pin numbering | Same net on the same numbered pin at both ends |
| Main board outline | 88.4 x 17.3 mm |
| USB carrier outline | 16.0 x 16.6 mm |
| Display holes / pads | All 84 use 0.9 mm drilled holes and 1.4 mm copper pads |

The JSON review snapshot contains a small number of tracks/vias because routing was already starting while this review ran. Copper routing, final DRC and continuity are intentionally excluded from the checks above and must have separate final reports.

## MCU power and programming-related pins

The KiCad `MCU_ST_STM32G0:STM32G0B1KBUx` symbol inherits `STM32G0B1K_B-C-E_Ux`. Its explicit package pins include:

| Package pin | Library function | Intended connection |
| --- | --- | --- |
| 4 | VDD | +3V3 |
| 5 | VSS | GND |
| 33 | VSS exposed pad | GND |
| 6 | PF2 / reset function | NRST |
| 7, 8 | PA0, PA1 | CC1_ADC, CC2_ADC |
| 15 | PB0 | LED_SDB |
| 22, 23 | PA9/PA11, PA10/PA12 | USB_DM, USB_DP |
| 24, 25 | PA13, PA14 | SWDIO, BOOT_SWCLK |
| 30, 31 | PB6, PB7 | SCL, SDA |

The complete MCU power map is therefore represented; there is no missing separate VDD pin in this chosen package. The exposed pad must actually join the ground plane through suitable copper/vias; assigning its net is only the schematic part of that requirement.

**USB remapping detail:** ST RM0444 says the default/reset mapping on these shared physical pins is PA11/PA12. Keep `PA11_RMP` and `PA12_RMP` clear when using USB. Setting those bits substitutes PA9/PA10 GPIO functions instead. A preliminary review message suggesting that USB needed the remap enabled was corrected before this report; the final recommendation is to retain the default USB pin functions.

References: [STM32G0B1 datasheet](https://www.st.com/resource/en/datasheet/stm32g0b1kb.pdf), [ST RM0444](https://www.st.com/resource/en/reference_manual/rm0444-stm32g0x1-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), and the installed KiCad 10 symbol library. ROM DFU boot conditions, option-byte provisioning and the firmware USB power policy need their own implementation and bench validation; ERC cannot establish them.

## LED drivers

Independently checked against the [Lumissil IS31FL3729 pin table](https://www.lumissil.com/assets/pdf/core/IS31FL3729_DS.pdf), also saved in `hardware/reference/`:

- CS1-CS3: pins 30,31,32; CS4-CS11: pins 1-8; CS12-CS15: pins 10-13.
- Pin 14 is the mode-dependent SW9/CS16 terminal and is unused in this design.
- SW1-SW8: pins 22,21,20,19,18,17,16,15; only SW1-SW5 are used.
- VCC pin 23; GND pins 9,24 and the exposed pad; ISET pin 25; SDA 26; SCL 27; address 28; shutdown 29.
- Address connections are respectively GND, SCL, SDA and VCC for the four driver instances.
- Each display pair shares five anodes but has fourteen independent cathode sinks. The seventh display uses only seven sinks on driver four.

The 47 kohm current-setting resistors are on the intended ISET pins and return to ground. The shutdown line has a default low pull-down. Both are useful safeguards, but actual pulse current, display brightness, scan behaviour and driver temperature still require measurements.

## Display physical orientation and dimensions

The custom footprint has the intended front-view physical order: left strip 1-6 downward; right strip 12-7 downward. Pad 1 is at local (-3.81,-6.35), pad 6 at (-3.81,+6.35), pad 7 at (+3.81,+6.35), and pad 12 at (+3.81,-6.35). Both inspected endpoint modules and all other module instances match this lattice.

The 0.9 mm holes and 1.4 mm pads give a nominal 0.25 mm annular ring. The main PCB is inset 0.25 mm on all sides of the nominal 88.9 x 17.8 mm LED body envelope. Its edge-stroke bounding box is slightly larger than the actual edge coordinates; use the edge coordinates for the manufactured outline dimensions.

The front-view pin-1 leader in the Wenrun drawing and the rotated rear photo support this orientation. Nevertheless, a sample electrical test is mandatory before fabrication. Identify physical pin 1 by its lead numbering, then confirm the pin-1-anode / pin-12-cathode pair lights the front upper-left dot at low current. Check further rows and columns as well.

**Full-array fit remains a release hold.** The reported approximately 90 mm overall body measurement differs from the 88.9 mm nominal body width. The breadboard check supports 2.54 mm lead pitch only; its five-hole groups prevented a reliable touching-module repeat measurement. The 12.7 mm centre pitch remains datasheet nominal. A 0.9 mm hole around a nominal 0.5 mm lead provides only approximately +/-0.2 mm position freedom. It cannot absorb an arbitrary accumulated width error. Fit all three selected groups of seven against the 100% template or pin-fit plate before fabrication.

## USB and enclosure

The USB receptacle's VBUS contacts A4/A9/B4/B9 share VBUS; A1/A12/B1/B12 and shield SH share ground; A6/B6 share D+; A7/B7 share D-; A5 and B5 remain separate CC1 and CC2. SBU pins A8/B8 are intentionally unconnected. The actual stock footprint uses `SH`, not `S1`, for its four shield stakes, and the shared specification now matches that footprint.

The input board has separate 5.1 kohm pull-downs on the two CC lines. The six-wire harness preserves pin numbering and keeps the data pair adjacent. This intended mapping supports either plug orientation but does not prove short-harness USB signal integrity or successful enumeration.

The revised 16.0 x 16.6 mm carrier can fit behind the main silhouette at the proposed offset (72.15,0.45), ending at (88.15,17.05). The final enclosure still needs to check socket opening position, cable overmould relief, mating force support, main-connector direction, harness bend space, solder-joint clearance and boot/reset access. A locally relieved port well is preferable to moving the PCB beyond the LEDs merely to meet a thick outer wall.

## Before manufacture

Required additional evidence: full-array physical fit and pin test; completed routing with clean final DRC and netlist/PCB parity; actual current/thermal tests on the first unit; USB programming and power-policy tests; carrier/harness continuity and enumeration; and the selected cable's enclosure fit. Schematics, emulation and 3D pictures cannot replace those physical tests.
