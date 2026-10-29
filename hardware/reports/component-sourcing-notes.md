# Sourcing and USB protection checks

Checked 29 October 2026. `component-sourcing.csv` contains **candidate parts, not a purchase order or assembly-ready BOM**. Quantities describe one replica including its USB carrier. The final generated BOM and placement files must follow the finished schematic and PCB.

Stock and prices are values returned by public distributor listings/search results. Some results were indexed weeks or months earlier; they are not a live cart reservation. JLCPCB assembly stock is a separate check, and a distributor's available stock does not guarantee immediate Economic PCBA availability. Recheck exact manufacturer, package, sourcing and total cost in the assembly quote. Several unrelated brands sell similar part numbers; preserve the specified manufacturer.

## ESD pin and footprint review

The TI TPD4E05U06DQAR has protected channels on **pins 1, 2, 4 and 5**, and grounds on **3 and 8**. Pins **6, 7, 9 and 10 are not internally connected**. The [manufacturer datasheet, Table 4-2](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf) allows optional straight-through PCB routing using those pads; this does not make a connection inside the component.

With the KiCad footprint's standard orientation, pins 1-5 are down its left side at y=-1,-0.5,0,+0.5,+1 mm; pins 10,9,8,7,6 are opposite on the right. A trace using the NC pad as a continuation must be physically joined on the PCB: 1-to-10, 2-to-9, 4-to-7 or 5-to-6. Alternatively use short channel stubs and leave NC pins unused. Do not rely on the chip to carry USB data across an NC pad.

Verified installed KiCad footprint: `Package_SON:USON-10_2.5x1.0mm_P0.5mm`. Its courtyard is approximately **1.82 x 3.0 mm** and a matching STEP model is bundled. The existing `Power_Protection:TPD4E05U06DQA` symbol inherits another symbol; inspect its electrical pin types and explicit NC treatment if using it in generated schematics. Connect both ground pads directly to a nearby ground return.

The four channels can protect D+, D-, CC1 and CC2 on the USB carrier. A separate VBUS TVS protects supply transients. The listed SMF5.0A is a unidirectional TVS: cathode to VBUS, anode to ground. Its clamping voltage is above the normal rail's absolute limits, so it must not be described as protection against sustained accidental 9/12/20 V. The design never requests those voltages.

## USB programming and standalone power

STM32G0B1KBU6 is the GP UFQFPN32 part, not the N suffix variant. It supports internal-clock USB, embedded USB matching and pull-up, and BC1.2 primary/secondary detection. [ST datasheet, USB characteristics](https://www.st.com/resource/en/datasheet/stm32g0b1kb.pdf).

Blank-flash parts enter ROM bootloader on power-up. After first programming, set nBOOT0_SEL=0, nBOOT1=1, BOOT_LOCK=0 and leave RDP at level 0 to make the BOOT0/reset controls usable. Retain SWDIO, SWCLK, NRST, ground and 3.3 V reference pads for recovery. The [ST empty-check explanation](https://community.st.com/stm32-mcus-60/empty-check-mechanism-on-stm32-42) and [AN2606](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf) explain that factory default option bits otherwise ignore BOOT0 after flash is programmed. A power cycle may be needed when the documented blank-flash bootloader reset limitation is encountered.

USB-C's two separate 5.1 kohm Rd resistors allow ordinary 5 V attachment. Full display power should be granted only after USB enumeration grants the required current, a valid CC higher-current advertisement is measured, or BC1.2 positively identifies CDP/DCP. A charge-only USB-A adapter is not identified merely by waiting for a timeout. If the firmware has not implemented BC1.2 before enabling its USB data pull-up, its standalone A-to-C charger behaviour must remain conservatively dim and be documented; C-to-C higher-current advertisement can still work through CC sensing.

ST provides HAL_PCDEx_ActivateBCD, HAL_PCDEx_BCD_VBUSDetect and HAL_PCDEx_DeActivateBCD, with distinct callbacks for SDP/CDP/DCP. Integrate detection **before enumeration**, not while USB is already active. A pin-compatibility or register-level software model does not replace bench tests of this analogue detection path.

## Passive and pushbutton BOM mapping (29 October 2026)

`passive-parts.json` maps the circuit specification's exact value strings to verified manufacturer and LCSC/JLC identifiers. The five 0603 1% resistor values use UNI-ROYAL Basic parts. The 0603 100 nF / 50 V / X7R decoupler is **YAGEO CC0603KRX7R9BB104, C14663**. The optional smaller carrier decoupler is **Samsung CL05B104KB54PNC, C307331**, 0402, 100 nF / 50 V / X7R; this also appears as Basic in JLC's primary listing.

The selected **Walsin 0603B105K160CT, C108463** (1 uF / 16 V / X7R) and **KYOCERA AVX 0603ZC225KAT2A, C2179699** (2.2 uF / 10 V / X7R) are Extended parts listed for Economic and Standard assembly. They preserve the specified X7R dielectric. C15849 and C23630 are similarly familiar Basic capacitor codes but are X5R parts; substituting them requires a deliberate specification and effective-capacitance review.

Both side-operated buttons use **Panasonic EVQP7A01P, C79167**. JLC's public tactile-switch listing returned 10,104 pieces and USD 0.0820 at quantity 1+. Panasonic gives a 3.5 x 3.55 mm body, 1.35 mm height and 2.2 N operating force. Exact case access and actuator travel still need the physical case fit test.

The primary LCSC driver listing was checked again: **C2940549 / IS31FL3729-QFLS4-TR** returned stock 2,644 and USD 1.1957 at quantity 1+, or USD 0.9984 at quantity 10+. Twelve drivers for three replicas therefore have an indicative component subtotal of USD 11.9808 at that quantity break. This is not an assembly quote or a stock reservation. JLC's separate consigned placeholder C9900000836 is not a stocked low-quantity purchase substitute.

Primary part pages:

- [Walsin 1 uF X7R](https://jlcpcb.com/partdetail/Walsin_TechCorp-0603B105K160CT/C108463)
- [AVX 2.2 uF X7R](https://jlcpcb.com/partdetail/KyoceraAVX-0603ZC225KAT2A/C2179699)
- [Samsung 0402 100 nF X7R](https://jlcpcb.com/partdetail/CL05B104KB54PNC/C307331)
- [Panasonic pushbutton](https://jlcpcb.com/partdetail/PANASONIC-EVQP7A01P/C79167)
- [Panasonic manufacturer specification](https://na.industrial.panasonic.com/products/switches-encoders-interface-devices/lineup/switches/series/79247/model/79335)
- [IS31FL3729 LCSC](https://www.lcsc.com/product-detail/C2940549.html)

The public pages and search index can disagree about available quantities and minimum orders. All figures in these candidate files are observations to guide sourcing; the live PCBA cart must confirm component matches, assembly service, stock and price before payment.
