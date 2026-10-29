# Cost-down architecture options — 29 October 2026

Initial read-only engineering comparison. The frozen A1 CAD and manufacturing files were not changed. **Implementation update:** [B2](../revisions/B2/README.md) is now the authoritative chosen and routed design: four TLC59282RGER QFNs (the SSOP clearance study failed), five PMOS switches driven by spare TLC sinks, three power switches, a BC1.2 detector and stock XIAO/USB modules. The finished board uses **six layers, 0.30 mm filled/capped vias and 55 factory SMT parts**. It passes native DRC/parity and the independent board audit. The current observed cost is about £113 for two complete displays delivered, VAT included, before coupons and minor assembly supplies; see B2 for quotation scope and remaining physical/factory checks.

The sections below preserve the initial alternatives and planning targets. Their two/four-layer and SSOP recommendations were investigated and superseded; they are not instructions for building B2 or achieved quotations. Since this comparison, the seven-module printed fit passed and the owner confirmed the complete pin map/orientation of one module.

## Recommendation

Keep the custom **88.4 × 17.3 mm LED mounting PCB**, factory-fit its small components, and move programming/USB/MCU onto a small ready-made controller plus a properly supported bottom-right USB breakout. For the driver redesign, first investigate **four TLC59282DBQR constant-current sink drivers and five high-side scan switches**, targeting two layers, ordinary 0.30 mm drill / 0.60 mm vias, no via-in-pad. This retains the present five-phase geometry and independently sets safe LED current. It needs more firmware timing work, but avoids the current and refresh compromises of a bare three-HT16K33 substitution.

Three HT16K33A-28SSOP chips are a cheaper, autonomous-scanning alternative, **conditional on current limiting and a brightness/flicker trial**. They should not yet be described as a 30-component replacement with identical optical behaviour. Stock HT/MAX boards do not fit the present outline flat. None of these candidates has a routed/DRC-checked fit yet.

## What must remain electrically and physically true

The owned matrix has five column **anodes** (pins **1,3,10,7,8**) and seven row **cathodes** (**12,11,2,9,4,5,6**). Seven modules give 245 dots. The existing nominal module repeat is 12.70 mm; all-seven fit and actual suffix/polarity still need physical confirmation. Its datasheet rates 20 mA continuous and 80 mA only for pulses **≤1 ms and duty ≤1/10**. The previous chat shorthand “0.1 ms” was incorrect. Current should remain below a conservatively chosen peak; dimming alone does not reduce peak current. [Owned-module manufacturer PDF, saved locally](../reference/LMD07057AUE.pdf).

A1 uses four 4 × 4 mm QFNs in groups 2+2+2+1: each pair shares five anode scans and has fourteen independent cathodes. The compact package's 0.4 mm pitch, 84 LED holes, MCU, USB routing and ground/power planes led to the implemented six-layer layout, 192 filled/capped 0.20/0.40 mm vias and local clearance exceptions. These facts explain its manufacturing cost; they do **not** prove that six layers are mathematically necessary for the display. See the local [circuit source](../tools/circuit_spec.py), [A1 review](../reports/final-hardware-review.md) and [driver datasheet](../reference/IS31FL3729_DS.pdf).

Changing to the larger eTQFP version could ease escape routing, but changes pinout/footprint and exposes the LED-lead collision problem. It still has an exposed pad. It is not a footprint-only cost reduction or a proven two-layer solution. A two-layer layout must be demonstrated with actual pads, traces and solder envelopes.

## Driver comparison

| Candidate | Needed | Advantages | Main tradeoff |
| --- | ---: | --- | --- |
| Existing IS31FL3729 QFN | 4 | Autonomous scan, adjustable current, per-dot PWM | Current implementation's expensive vias/layers and two PCBA jobs |
| MAX7219 | 7 | Autonomous scan, resistor-set current, familiar software | Seven packages, 5 V logic translation, difficult stock-module packing |
| HT16K33A 28SSOP | 3 | Cheap, autonomous refresh, I²C, fewer driver ICs | External current-limit assessment, slower scan, 3.3/5 V translation |
| TLC59282 DBQ + scan switches | 4 + 5 switches | Regulated current, ordinary SSOP, 3.3 V logic, retain five phases | MCU supplies scan/blanking timing and safe high-side gate control |
| Plain 74HC595/TPIC shift registers | Several | Cheap, familiar | Need resistors and power stages; HC595 pins cannot directly supply a full matrix; no clear overall advantage |

### MAX7219

Connect five SEG source outputs to module anodes and seven DIG sinks to cathodes; scan-limit is seven digits and decode is disabled. One 8×8 chip cannot serve two unmodified 5×7 modules. Daisy-chain seven chips, with common clock/load and serial DOUT→DIN. At 5 V the specified input-high minimum is 3.5 V, so a 3.3 V MCU needs an appropriate 5 V AHCT/HCT translator on DIN/CLK/LOAD. DOUT must not feed a non-5-V-tolerant MCU input. Choose the current resistor for a conservative peak, accounting for seven-phase multiplexing and the module's ratings. Include local bulk/100 nF decoupling. [Analog Devices MAX7219/MAX7221 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX7219-MAX7221.pdf).

Standard modules also have the wrong display footprint and need an adapter. One current UK listing is **£5.68 each**, **50 × 32 × 15 mm**: seven cost £39.76 before the MCU/custom adapter. They cannot sit flat inside an 88.9 × 17.8 silhouette. Cheap alternative listings are not evidence that a named genuine MAX IC has the advertised ratings. [Switch Electronics module at Maplin Pro](https://pro.maplin.co.uk/products/8-x-8-dot-led-matrix-display-control-module-max7219).

### HT16K33A

Use three groups **3+3+1 modules**. Within each group, seven cathode rows share seven COM sinks; each module's five anodes use distinct ROW sources. **Do not tie different chips' COM outputs together.** Use the 28-pin version. Its 16×8 RAM, 16 global brightness steps and autonomous scan can represent the present binary artwork, though it has no per-dot PWM. [Holtek product page](https://holtek.com.cn/page/vg/HT16K33A).

Manufacturer Rev.1.10 specifies 4.5–5.5 V, SDA/SCL high ≥0.7VDD, 1/9 duty and 7.6–11.4 ms frame time. ROW drive is 25–30 mA typical, up to 40–50 mA under its table conditions; COM sink capability is at least 160 mA. Thus three modules can load fifteen sources simultaneously. Do not assume an adjustable 7 mA peak or that PWM fixes overcurrent. Use verified current limiting, assess the aggregate sink load, and translate I²C bidirectionally; address selection uses the manufacturer's multiplexed-pin circuit, not arbitrary permanent straps. SSOP-28 is 9.90 × 6.00 mm, 0.635 pitch, maximum height 1.75 mm. [Manufacturer-authored PDF hosted by LCSC, pp.9,42](https://datasheet.lcsc.com/datasheet/pdf/48e2fa197ee7f58779ac2333ff4433d3.pdf?productCode=C5444738).

The likely extra limits are **35 independent anode resistors**, or equivalent isolated resistor arrays. One shared COM resistor would make brightness depend on how many dots are lit. Conservative limiting can reduce brightness; test before selecting this route. The approximately 88–132 Hz refresh and three independent oscillators may change motion/camera behaviour. These are reasons for measurement, not proof it will look poor.

A stock Adafruit breakout is **35.77 × 20.37 × 4.03 mm**, so three cannot fit flat behind the LEDs. With the existing front stack ending at z=10.9 mm, even turning the 20.37 dimension into depth reaches z≈31.3 mm before back/connector clearance; a ~35 mm or deeper enclosure would need a new packing study. [Adafruit dimensions](https://www.adafruit.com/product/1427). UK stock costs **£7.70 each**, £23.10 for three, before wiring/MCU. [Pi Hut listing](https://thepihut.com/collections/all/products/adafruit-16x8-led-matrix-driver-backpack-ht16k33-breakout).

### TLC59282 candidate

Four devices provide 64 regulated sinks for **49 independent cathodes**; share the five matching anodes across all seven modules and scan those five phases. Run driver logic at 3.3 V and LEDs at 5 V. TI permits that separate LED rail, provides resistor-set 2–35 mA sinks at 3.3 V, serial cascading, BLANK and latch controls. Its DBQ package is **8.65 × 6 mm**, 24 pins, with no QFN exposed-pad process. Set approximately 7 mA peak initially. [TI product information](https://www.ti.com/product/TLC59282), [TI datasheet](https://www.ti.com/lit/ds/symlink/tlc59282.pdf).

Each high-side scan switch must handle up to **49 × chosen peak current**, about 0.35 A at 7.25 mA. A 5 V P-channel MOSFET gate cannot be driven safely off by a direct 3.3 V GPIO: use a suitable gate stage, default-off pulls and reset-safe BLANK. Firmware must blank, turn all scans off, load/latch new sink data, select exactly one scan, then unblank. Use timer/PIO/DMA rather than web/UI-driven refresh; test startup, stalls, ghosting and USB power qualification. At a stalled scan, a deliberately <20 mA per-dot hardware limit protects LEDs, but firmware must still blank during faults. Five-phase regulated drive can match A1 brightness more directly.

## Prices and targets

Current component-only observations: **HT16K33A-28SSOP C5444738 $0.5894 each at 1+**, so three $1.7682; **TLC59282DBQR C129352 $1.1762 each**, so four $4.7048. LCSC stock is not JLC assembly stock; check actual assembler sourcing before committing. [HT listing](https://www.lcsc.com/de/product-detail/LCD-Drivers_Holtek-Semicon-HT16K33A-28SSOP_C5444738.html), [TLC listing](https://www.lcsc.com/fr/product-detail/C129352.html).

**Planning targets, not quotes:** keep all driver/support components below roughly £8–12 per replica; aim for £50–80 delivered for a first complete working prototype with the factory's minimum batch, or £70–110 for the three-replica electronics batch including stock controllers/USB parts. These exclude tools and existing LEDs. Setup/feeder fees, stock, routing success, shipping/VAT and module packaging can move them materially. Savings should mainly come from **one standard two-layer PCBA job**, removing custom MCU/USB carrier complexity, not pretending a £1 IC alone determines board cost.

## Before choosing the replacement

Finish controller/USB fit using actual vendor dimensions and preserve the bottom-right port, then place the real SSOP lands against all 84 lead pads. Prefer 0.15–0.20 mm tracks/clearances and ordinary 0.30/0.60 vias; use four layers only if the demonstrated layout requires them. The current 24 mm case is plausible for a custom low-profile main plus separate MCU, but stock headers, wire bend radii and USB pigtails need a complete collision check. Reuse the pin-level simulator's independent diode model with a new encoder; confirm all 245 walking pixels and frame equivalence. Do not place an order until routing/DRC, source stock, physical fit and power/current limits are actually checked.
