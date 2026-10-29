# B2 BC1.2 restoration and independent policy review

29 October 2026. Adding U9 restores the A1 ability to use full brightness on a positively classified A-to-C charging port. The RP2040 alone cannot supply this detection; treating every powered USB cable as a500mA grant would not be an equivalent replacement. No charger, USB data path or suspend-current test has yet been performed on physical B2 hardware.

## Exact factory addition

U9 **BQ24392RSER / JLC C128408** is an automatic BC1.2 detector with a series USB2 isolation switch, TI **RSE0010A**. Body1.5×2.0×0.6mm maximum; native KiCad footprint `Package_DFN_QFN:Texas_UQFN-10_1.5x2mm_P0.5mm`, courtyard2.4×2.9mm. The TI drawing contains ten lands and **no separate EP11**, despite the JLC package description containing “EP”. Its pin map is:

| Pin | Function | B2 connection |
|---:|---|---|
|1|SW_OPEN open-drain output|Intentionally unused|
|2|DM_HOST|USB_DM_HOST→J11→XIAO TP12|
|3|DP_HOST|USB_DP_HOST→J12→XIAO TP4|
|4|CHG_AL_N open-drain output|BC_AL_N→J20→D6/GP0/pad7; R23=10k to always3V3|
|5|GOOD_BAT input|Always-on+3V3 hard tie|
|6|GND|GND|
|7|DP_CON|Raw USB_DP from external port/ESD|
|8|DM_CON|Raw USB_DM from external port/ESD|
|9|VBUS supply|Always-on+5V after U8 soft start; C15=100n and C16=1u bypass|
|10|CHG_DET push-pull output|BC_DET_5V→R21=10k→BC_DET→J19→D5/GP7/pad6; R22=15k from BC_DET to GND|

GOOD_BAT must stay high during LED shutdown and host suspend; tying it to SW_3V3 would open the USB path. Raw and downstream USB pairs are now separate nets. The chip automatically connects SDP/CDP data after detection, allowing normal USB programming and RP2040 boot-ROM recovery; DCP data stays isolated. [TI datasheet RevG, terminal map and functional modes](https://www.ti.com/lit/ds/symlink/bq24392.pdf).

The divider is necessary because CHG_DET HIGH is specified from3.5V toVBUS. For10k/15k1%,1µA GPIO leakage, detector3.5…5.25V and the conservative3.3V regulator minimum, calculated HIGH is2.077…3.181V and LOW at most0.248V. RP2040's specified VIH at3.3V is **2.0V** and VIL0.8V. Do not substitute an equal47k/47k divider or connect the5V output directly. [RP2040 datasheet Table625](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf).

## Authoritative status interpretation

The following is the detector's settled classification with GOOD_BAT HIGH. “High” on AL_N is its pulled-up high-impedance state:

| Source/class | AL_N | DET | USB switch | B2 BC grant |
|---|---:|---:|---|---|
|SDP|0|0|Closed|None; normal enumeration can separately grant500mA|
|CDP|0|1|Closed|Yes; project still capped at500mA|
|DCP|0|1|Open|Yes; project still capped at500mA|
|Recognized Apple/TomTom charger|0|1|Open|Yes; project still capped at500mA|
|Noncompliant/open-data or PS/2 source|0|0|Open|None|
|Invalid VBUS|1|0|Open|None|
|Any AL_N HIGH state, including inconsistent DET HIGH|1|Any|Not a current grant|None, fail closed|

TI explicitly defines AL_N HIGH as “charging not allowed” regardless of DET. **DET HIGH alone is insufficient.** The device does not report a numerical1500mA contract; B2 uses a positive classification only to permit its existing500mA target. [TI EVM guide Tables1–2](https://www.ti.com/lit/ug/slvua61/slvua61.pdf).

The revised `Bc12Qualifier` was independently read after correction: it begins Unknown, accepts only `chargeDetected && !allowanceN`, requires100ms stable, withdraws immediately on either input becoming invalid, and handles unsigned-millisecond rollover. The complete source policy gives a real host suspend precedence over BC, Type-C and USB-configuration grants. There is no AL_N HIGH fallback grant. Tests exercise all four input combinations, qualification timing, withdrawal through each input, rollover and all64 source/suspend combinations.

The chip handles data-contact/primary/secondary detection. Its normal detection has130ms debounce and can take600ms; a very slow insertion can conservatively fail qualification. The project starts unqualified and waits for positive settled status rather than assuming that elapsed time grants current. A weak or unknown charger remains dim; a reset starts a new software qualification. The actual full device must still demonstrate correct SDP/CDP/DCP attachment, data enumeration, boot-ROM reflash and suspend/resume through this added switch.

## Cost, placement and assembly effect

Live JLC assembly search independently showed **937 in-stock, zero idle, Extended, $0.4226 qty1** for C128408 on29 October. Availability is not reserved. [Official JLC part](https://jlcpcb.com/partdetail/TexasInstruments-BQ24392RSER/C128408). R22 is verified Basic15k **0603WAF1502T5E / C22809**; all new small parts are factory fitted.

The final source contains82 parts:55 factory SMT, seven owner matrices and20 owner wire pads. New factory refs are U9,C15,C16,R21,R22,R23; new owner pads J19/J20. All previous parts/nets remain except the necessary upstream/downstream USB split. Native schematic ERC is zero with no exclusions and all327 connected pins match the source graph.

Placement is U9(63.25,11.3), C15(68,10.7), C16(71.2,10.7), R21(25.15,6.1), R22(25.15,11), R23(12.45,11), J19(23.88,0.85), J20(26.42,0.85), all0°. Only existing R15 moves to(12.45,6.1). The independent native-footprint RAM check reports no new courtyard/pad/case-stop conflicts and at least0.20mm pad-box spacing. It does not claim clearance to existing routes/vias; routing integration and final native DRC remain separate. See `../mechanical/bc-placement-audit.json`.

The additional status pullup draws about0.33mA on an SDP/CDP and the detector itself remains powered to retain USB connection. Include both in the **whole-device2.5mA suspend acceptance measurement**. Its1.1µF bypass is behind U8 soft start, so it does not bypass the controlled input ramp. Source-derived static voltage/model checks do not demonstrate USB timing, inrush or suspend-current compliance.

The approved1µF cost substitution is Samsung **CL10A105KB8NNNC / C15849**,1µF±10%,50V,X5R−55…85°C,0603 with0.80±0.10mm thickness, in C5/C6/C7/C14/C16. Same pads/nets/positions; no additional owner assembly. The manufacturer confirms these values on its [exact product page](https://product.samsungsem.com/mlcc/CL10A105KB8NNN.do). DC bias, tolerance and temperature still affect effective capacitance; this change does not turn a nominal capacitance sum into an inrush measurement.
