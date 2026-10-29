# Independent firmware power and programming review

Reviewed 29 October 2026. Scope: `hardware/firmware/HouseRules/`, the pinned STM32duino 3.0.0 sources, current circuit specification, build flags and actual compiled ARM ELF. This is a code and architecture review, not a physical USB compliance test.

**Result:** one P1 startup defect was found and corrected during review. The rebuilt application has no remaining P1 defect identified by this review. It is suitable for controlled prototype bring-up once the board and module checks are complete. Current consumption, analogue charger detection and STOP wake still require measurements.

## Findings and resolution

### P1 — premature USB startup could prevent standalone Type-C operation: corrected

The pinned core calls `USBD_CDC_init()` from `premain -> init -> hw_config_init`, before the sketch's `setup()`. In the earlier image this entered charger detection and attached USB before the sketch sampled CC. A Type-C source offering higher current without BC1.2 could then cause an early USB suspend while `ccHigh` was false. The suspend hook could enter STOP before CC qualification finished, leaving the display dark indefinitely on that supply.

The revised build wraps the automatic `USBD_CDC_init` with an empty function. Actual initialisation follows `setup -> SerialUSB.begin -> CDC_init`, after SDB is configured low, driver registers are cleared and CC is sampled for 120 ms. Independent disassembly confirmed both paths and that the setup loop precedes `USBSerial::begin()`.

The core's original weak `USBD_reenumerate()` also called `USB_DevConnect()` before PCD initialisation. The project's strong replacement now enables the USB peripheral clock, clears DPPU, waits 20 ms and leaves attachment disabled. Independent disassembly confirms the DPPU clear mask `0xffff7fff` and no reconnect. The first application attachment then occurs through the real `USBD_Start` after BC1.2 detection. This removes reliance on cold-start peripheral clock gating to suppress an early reconnect.

### P2 — CC ADC source-impedance margin: corrected in component values

The original 100k/100k divider was nominally at the ADC's 50 kohm source-impedance limit; component and source impedance could exceed it. R10–R13 have been changed to 47k/47k, with the same footprints and divide-by-two ratio. Nominal local Thevenin impedance is 23.5 kohm, comfortably below 50 kohm even when allowing source impedance and 1% tolerance. The 160.5-cycle sample setting remains appropriate. [ST DS13560, ADC Tables 63–64](https://www.st.com/resource/en/datasheet/stm32g0b1kb.pdf).

The powered-state CC termination includes the measurement network:

`5.1k || (47k + 47k) = 4.8375k`.

With all these resistors specified at 1%, its conservative extrema are approximately 4.789–4.886 kohm. This stays within the 4.59–5.61 kohm range for a 5.1 kohm ±10% current-detecting Rd implementation. The USB Type-C specification explicitly applies this requirement to the total equivalent termination, including internal resistances. [USB Type-C Release 2.4, Table 4-28](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/USB-Type_2D00_C-Spec-R2.4-_2D00_-October-2024.pdf).

**Recommended comment/design rule:** retain 47k/47k and separate 5.1k Rd on each CC line; calculate the combined termination whenever measurement components change. Do not treat the ADC divider as electrically invisible to CC.

### P2 — physical power and suspend validation: outstanding prototype checks

No software simulation establishes actual total current, suspend current, inrush or analogue BC1.2 accuracy. The README correctly leaves these unclaimed. Measure all-on current at both GCC levels; startup with a computer; positive DCP/CDP detection; both Type-C cable orientations; default and higher-current advertisements; and long host suspend/resume, including suspension during I2C traffic. An unsupported or unclassified source must remain at the conservative default setting. Verify that interrupted I2C either resumes correctly or latches the display dark.

## Checks that agree with the circuit

| Area | Review result |
| --- | --- |
| USB pins | Strong USB pin map contains PA11 and PA12 only, without PREMAP. Pinned core pin configuration explicitly clears the respective G0 remap bits. PA13 remains available for SWDIO. |
| Descriptor | Actual full-speed configuration bytes are `09 02 43 00 02 01 00 80 FA`: bus-powered, 250 × 2 mA = 500 mA. DTR/serial connection state is not used as a power grant. |
| Startup and DFU blanking | PB0/SDB is held low during driver initialisation and BC detection. External R7 pull-down provides blanking before the application runs and during reset/ROM DFU. |
| CC measurement | PA0/PA1 match the schematic. `analogReadResolution(12)` matches the denominator 4095. Eight samples per channel are summed in 32-bit integers, and `sum × 6600 / (8 × 4095)` correctly reconstructs raw CC voltage from the 1:2 divider and nominal 3.3 V reference. There is no accumulator overflow. |
| CC qualification | High-current allowance requires a reconstructed 0.8–2.2 V level for 100 ms; observations are spaced at least 10 ms. A failed low/out-of-range reading immediately clears the allowance on that sampling pass. |
| BC1.2 | Detection runs before application data attachment. Only a completed CDP/DCP result grants charger power. Error, timeout, unknown and SDP do not. The DCP branch remains detached; CDP/SDP continue enumeration. |
| Driver configuration | A0=0x40/0x41 selects five scan outputs with software shutdown/operation. GCC64 is the documented full-scale code. Scaling uses 14 current sinks on each paired chip and seven on the last; unused PWM/scaling positions are cleared. |
| Fault response | Any I2C transaction failure lowers SDB and latches the display dark until reset. SDB rising observes the manufacturer's quiet intervals before further I2C. |
| Host suspend | ISR lowers SDB before returning, marks the output state invalid, and enables STOP0 for a real host/default-current suspend. Host suspend overrides an earlier CC/charger allowance once a host has been seen. |
| Resume | Pinned core restores clocks before calling the wrapped resume function. That clears the suspend flag/low-power selection; the main loop re-evaluates grants and re-enables output through the normal sequence. GPIO output state is retained through STOP0. Actual wake and current remain bench checks. |

The conservative 0.8 V CC threshold lies above the specification's maximum default-current CC voltage of 0.612 V. Resistor ratio, regulator and ADC errors have substantial room before bridging that gap. It intentionally exceeds the 0.746 V minimum of a valid 1.5 A indication, so a valid low-edge source can remain dim. Every 3 A advertisement remains in the accepted nominal range. The 47k measurement load is already included in total Rd, so the ±10% tables apply; this must still be checked on the populated board. [USB Type-C Release 2.4, Table 4-36](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/USB-Type_2D00_C-Spec-R2.4-_2D00_-October-2024.pdf).

## Current budget and the hardware limit

Using the manufacturer's equation with R_ISET=47k, GCC64 and scaling255 gives approximately **7.25 mA nominal peak per active LED**. For all 245 pixels at PWM255, five scan phases and the stated blanking intervals, nominal LED average input is approximately **341.6 mA**. GCC8 reduces that LED contribution to approximately **42.7 mA**. Add four drivers' quiescent current, MCU, pull-ups and regulator consumption when judging the 500 mA and unconfigured 100 mA budgets. These figures are calculations, not measured maxima. [Lumissil driver datasheet, saved reference](/Users/harrymcneill/Projects/house-rules-led-recreation/hardware/reference/IS31FL3729_DS.pdf).

R_ISET independently limits peak LED current even if software chooses full-scale GCC. GCC controls average brightness/current but does not substitute for the correct physical current-setting resistor. The selected peak is below the owned module's stated continuous LED rating. The PPTC protects faults and must not be described as granting USB current or providing a precise 500 mA limit.

## Source transitions and programming

CC allowance is re-evaluated throughout normal execution. USB configuration is read directly from the stack each loop, so reset/deconfiguration removes that grant. BC classification and `hostSeen` are intentionally latched for this power session; the BC attempt is made once. Normal unplug/replug of this exclusively USB-powered board power-cycles the MCU and repeats all classification. **Continuous-VBUS source substitution, auxiliary powering through a debugger, or a future battery supply is outside that assumption.** Such an extension requires explicit detach/VBUS detection, grant invalidation and fresh BC detection before attachment. Do not imply runtime BC reclassification is already implemented.

Programming documentation correctly distinguishes running CDC from ROM DFU. It names PA14/SWCLK, physical pin25, as BOOT0 and retains SWD recovery. Hardware BOOT entry after first flash requires nBOOT_SEL/nBOOT0_SEL=0, nBOOT1=1, BOOT_LOCK=0 and RDP level0; nBOOT0 is ignored in this pin-selected mode. The documented BOOT/reset sequence and addressed image base 0x08000000 agree with that architecture. Verify option-byte names and readback on the actual identified device. [ST AN2606, Pattern11](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf).

## Evidence

- Independently inspected startup-fix ELF SHA-256 `93fc70421c5eb5575997ea0c906fae7eed359fa3b550f1838b528723e7ed62ec`. A subsequent compiled image adds bounded CDC diagnostic patterns; its ELF is `4caa8af008cab2ab12c6d3d00505e0666718723b43b0d98b9a0b38096927e89f`, BIN `6ea619cf4bf5c18033a87964acfd9ac2c68c241575a8528b129d5185226f01c6`. The diagnostic handler selects framebuffer patterns without changing GPIO/GCC or the reviewed startup/power hooks. This update is not a new physical test. See `hardware/firmware/compiled/elf-audit.txt` for the current build's hashes.
- Inspected pinned core `hw_config.c`, `main.cpp`, `usbd_conf.c`, `usbd_if.c`, `usbd_cdc_if.c`, ADC/pin mapping and STM32G0 HAL USB sources.
- Independently ran `python3 hardware/firmware/test_player.py`: 60,000 player frames, two traversals, power-policy assertions and driver mapping passed.
- No attached board, charger, USB analyser or oscilloscope was available; no physical measurements or programming were performed.


## BOOT pushbutton series resistor added during final hardware review

R14 is now 2.2 kohm between the BOOT pushbutton and PA14/SWCLK. The MCU-to-SWD-clock testpad connection remains direct; R9 remains a 10 kohm pull-down at that net. This limits pushbutton-versus-debug-clock contention without changing firmware or boot option bytes. Including 1% resistor tolerance and a conservative 25 kohm internal pull-down, the asserted boot level is approximately 0.761 × VDD, above the conservative 0.7 × VDD high threshold; short-circuit contention at 3.3 V is limited to approximately 1.52 mA. The switch's 3.3 V side is unchanged. The exact resistor is the existing C4190/0603WAF2201T5E, so it introduces no new assembly part type.
