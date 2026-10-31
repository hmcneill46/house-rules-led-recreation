# TLC59283 adoption — independent electrical review

31 October 2026. **Static compatibility review passed; physical qualification remains pending.** No schematic or routing hard block was identified for TLC59283RGER/C485815 with 7.15 kΩ IREF resistors. This does not establish measured USB compliance, optical performance or safe analogue transients. No order or powered test was performed.

## Checks against the actual updated sources

A read-only comparison against Git `01789e4` finds exactly eight changed part identities: U1–U4 and R1–R4. All 82 parts retain their pin graphs and physical assignments. The RGE signal map was independently transcribed from TI and asserted against all four updated devices, including OUT0–15 on pads 2–17 and both ground terminals 22/25. IREF resistors retain their IREF-to-ground connections. The USB wiring, MCU pins and 500/30/470 µs scan timings remain unchanged.

The entire updated PCB is byte-for-byte identical to the old PCB after only the enumerated part-value, MPN, catalogue, datasheet and description substitutions. Thus copper, pad geometry, vias, outlines, LED pitch and component placement have not changed. This is stronger evidence of preserved geometry than checking a few dimensions alone. Source hashes and detailed assertions are in the [JSON record](independent-electrical.json).

The current TI RGE0024C drawing matches the existing 4 mm package, 0.5 mm pitch, 2.1 mm EP and stencil geometry. LAT remains level-sensitive while HIGH. The existing 8 MHz transfer, full 64-bit refresh and 1 µs latch pulse have ample represented timing margin. Waveform integrity still requires a physical board. [TLC59283 datasheet, pin/package and timing sections](https://www.ti.com/lit/ds/symlink/tlc59283.pdf).

## Current and heat calculations

The independently calculated nominal current is `1.208 × 43.8 / 7.15 = 7.400055944 mA`, 0.335% below the original 7.424926471 mA. Forty-nine lit LEDs draw 362.602741 mA instantaneously and 340.846577 mA averaged over the 94% phase light time. IREF resistor dissipation is approximately 0.204 mW.

Reusing the existing conservative planning method gives these subtotals:

| Quantity | Full, 470 µs | DIM, 25 µs |
| --- | ---: | ---: |
| LED average current | 340.85 mA | 18.13 mA |
| Four driver logic allowance | 34.80 mA | 17.00 mA |
| Gate, anode bleed and BLANK pullups | 2.13 mA | 0.11 mA |
| MCU/module allowance | 30.00 mA | 30.00 mA |
| Subtotal before other loads | **407.78 mA** | **65.24 mA** |

These are approximately 24.19/8.86 mA below the old planning figures. The substituted driver-current test values apply at a different IREF setting; precharge pulses, real MCU workloads and remaining loads are not a certified product maximum. Neither subtotal proves a 500 mA configured or 100 mA unconfigured USB limit.

For a fourteen-row driver, illustrative 5 V/2 V LED operation gives about 0.321 W at full duty including its logic allowance. The 5.5 V short-load sink term is approximately 0.570 W instantaneous before logic. TI lists RGE θJA as 42.9 °C/W on its standardized test board; that is not the thermal resistance of this narrow carrier inside its printed case. Retain the twelve filled/capped ground thermal vias and measure enclosed all-on temperature.

## Precharge and the five PMOS gates

BLANK HIGH switches the regulated sinks off **and enables precharge on every output**, including U4's gate-control outputs. It must not be described as making every output high impedance. Powered high-voltage leakage data support the existing 5 V gate pullups; treating precharge as a simple bidirectional clamp to 3.3 V would be incorrect. At a 1 V gate, the 4.7 kΩ pullup supplies only about 0.85 mA, leaving plausible pull-down margin. This remains an engineering inference for the PMOS load.

The existing shared-enable QOD rails, zero-latch before shutdown, low data signals and BLANK high impedance reduce exposure during shutdown. **They do not prove power-off behaviour:** no necessary VCC=0 reverse-current guarantee was found. Relative rail ramps, precharged cathodes and gate/anode settling need measurement. If those fail, sequencing or discharge changes could require a real circuit revision.

TI also discusses current-loop ringing with large parasitic inductance. Its example controls common-line PNPs with driver outputs, supporting the broad topology but not qualifying our PMOS implementation. No concrete need for extra RC networks was established for this single-board layout. [TI stability application note](https://www.ti.com/lit/an/slvafp4/slvafp4.pdf), [load-switch QOD behaviour](https://www.ti.com/lit/ds/symlink/tps22918.pdf).

The replacement's accuracy limits differ from the original and its output headroom is lower. Retain brightness-uniformity, ghosting and supply/transient checks; do not promise that every electrical specification is identical. [Original driver datasheet](https://www.ti.com/lit/ds/symlink/tlc59282.pdf).

## Physical checks still open

The owner's complete current-case print check is pending. Confidence in the fit is not recorded as a completed measurement. Factory CAM/pin-1 approval is also separate.

The first powered assembly needs current-limited bring-up; both USB-C orientations; USB configuration/programming, suspend/resume and source-policy measurements; rail/gate/anode/cathode waveforms during startup, reset, unplug and shutdown; all 245 walking pixels; optical comparison; output ringing checks; and an all-on enclosed thermal soak. A digital pin model does not simulate analogue precharge, and no trusted analogue chip model or physical prototype was exercised in this review.
