# Final electrical file verification

The frozen native boards passed KiCad 10.0.7 DRC with zone refill, all severities and schematic parity enabled: **zero violations, zero unconnected items and zero parity issues on both boards**. No exclusions or ignored warnings were added. This checks the saved design files; it does not replace measurements on a prototype.

| Property | Main | USB carrier |
| --- | --- | --- |
| PCB SHA256 | `8b9df50fe0897db76a186902024ef12a80ff8da990d0e1d2d342f8fa2f86a830` | `fb01d3a1369278d2435762de07fb7607957e51fce6277dc55044a102059ed40f` |
| Layers / thickness | 6 / 1.6 mm | 4 / 1.0 mm |
| Footprints / factory placements | 50 / 37, bottom | 7 / 7, top |
| Tracks / ordinary F–B through vias | 2539 / 192 | 85 / 10 |
| Minimum signal track | 0.10 mm | 0.15 mm |
| Minimum +5V/VBUS track | 0.15 mm | 0.20 mm |

All **192 main vias** are explicitly marked filled and copper capped in the native file, with ordinary F.Cu–B.Cu through-hole spans. Order IPC-4761 Type VII resin-filled/copper-capped via-in-pad processing, also called VIPPO/POFV, for all main vias. The **84 LED mounting pads retain open 0.9 mm plated holes**; they are component holes and must not be filled. The USB socket's through-hole shell tabs also need open holes and factory soldering. No blind, buried or laser-drilled vias are used. [JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering), [JLC via-in-pad process](https://jlcpcb.com/help/article/via-in-pad-pofv-guide).

The main's global clearance floor is 0.10 mm, while Default and Power netclasses retain 0.15 mm clearance. Only VIA-to-PAD pairs intersecting the same U1–U4 courtyard receive the local 0.10 mm exception. A fresh negative control copied the board, project, schematic, valid rule units and local footprint libraries into a separate directory, then removed only that exception. It produced **exactly nine clearance errors**, each a nominal 0.10 mm QFN via-pad gap requiring the ordinary 0.15 mm clearance; it produced zero unconnected or parity issues. The actual board produced zero violations. Hash checks confirm that this control did not change the actual PCB, project, rules or schematic. The USB power-width rule also uses explicit `0.15mm` units and its fresh native DRC passed. This confirms that the local exception operates as intended. [KiCad rule documentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#_custom_design_rules).

R14 is a 2.2 kohm 1% 0603 resistor, UNI-ROYAL `0603WAF2201T5E`, LCSC `C4190`, between the `BOOT_BUTTON` and `BOOT_SWCLK` nets. Both physical SW1 pin1 lands connect to `BOOT_BUTTON`; pin2 remains +3.3 V. The PA14/SWCLK net retains its 10 kohm pull-down and direct MCU-to-SWD-test-pad connection. R14 limits contention to approximately 1.5 mA if the BOOT button is pressed while an SWD probe drives SWCLK low. The divider still gives a valid high level when BOOT is pressed. Firmware behavior is unchanged.

Measured native USB track centreline totals are:

| Board / signal | F.Cu | B.Cu | Total |
| --- | --- | --- | --- |
| Main USB_DM | 39.8134 mm | 2.6032 mm | 42.4166 mm |
| Main USB_DP | 38.8562 mm | 2.1411 mm | 40.9973 mm |
| Carrier USB_DM | 10.4221 mm | 4.1692 mm | 14.5913 mm |
| Carrier USB_DP | 11.8530 mm | 0 mm | 11.8530 mm |

These totals include pad/ESD escape branches and exclude the purchased internal harness; they are not a measured end-to-end delay or controlled-impedance result. Main front routing uses the upper edge corridor over the In1 ground plane. Confirm the manufacturer's actual 1 oz stack, the six-wire harness assembly and reliable full-speed USB enumeration/programming on the prototype. No 90-ohm channel guarantee is claimed.

Evidence is saved in `main-final-drc.json`, `usb-electrical-final-drc.json`, `main-final-local-rule-negative-drc.json`, `final-local-rule-control-inputs.json` and `final-electrical-verification.json`. The JSON records input/report hashes and the native measurements. User-owned LED fit/pinout verification, USB power/suspend measurements, case/harness trial and assembler placement/process review remain pre-order checks.
