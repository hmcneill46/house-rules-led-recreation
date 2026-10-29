# Firmware and artwork for the physical display

This folder now contains **compiled prototype firmware** for the proposed STM32G0B1KBU6 board, plus its artwork data. It has not run on physical hardware. The source, compiled ELF/BIN/HEX and software checks are reviewable; they are not a claim of correct physical wiring, USB compliance, optical performance or manufacturing readiness.

## Prototype build

`HouseRules/HouseRules.ino` targets STM32G0B1KBUx with four IS31FL3729 drivers at 7-bit addresses 0x34-0x37. It uses:

| Signal | MCU pin |
| --- | --- |
| USB D- / D+ | PA11 / PA12 |
| I2C SCL / SDA | PB6 / PB7, alternate function 6 |
| Common driver shutdown | PB0, external pull-down required |
| CC1 / CC2 measurement | PA0 / PA1 through separate 47k/47k dividers |

The generic variant uses internal oscillators, including HSI48 for USB; no external crystal is assumed. A strong override of its weak USB pin map selects only PA11/PA12, preserving PA13/SWDIO instead of assigning optional USB_NOE functions. The core clears the G0B1 PA11_RMP/PA12_RMP bits for these pins, selecting USB rather than the alternate PA9/PA10 digital functions. Each 47k/47k CC divider has nominal 23.5 kohm Thevenin impedance; the ADC sampling-time build flag also selects 160.5 cycles. CC thresholds assume the specified 3.3 V supply and must be checked over resistor, regulator and ADC tolerances.

Pinned build tools: **Arduino CLI 1.5.1**, **STM32duino 3.0.0**, and its packaged Arm GCC 14.2.1 toolchain. These are installed in the separate `~/.cache/house-rules-arduino/` cache; existing Arduino profiles and installed core sources were not edited. The project uses STM32duino's ST-contributed community core, not a claim of commercial ST software support.

From the repository root:

```sh
# Already installed on this Mac. For another Intel Mac, optional setup:
python3 hardware/tools/firmware-build/setup.py

python3 hardware/tools/firmware-build/build.py
python3 hardware/firmware/test_player.py
```

The setup script verifies the pinned CLI archive SHA-256 and installs the exact core version. The build script stages copies of the sketch and generated header in the cache and leaves their source files intact. It selects the explicit G0B1KBUx board, native CDC USB, no LTO and ROM DFU as the intended upload method. It verifies the installed core version before compiling.

The current build uses **66,108 bytes of flash and 4,560 bytes of static RAM**, fitting the part's 128 KB flash. See `compiled/build.log`, `compiled/build-metadata.json` and `compiled/elf-audit.txt` for current counts and checksums. Rebuilding after source changes updates those results. `compiled/HouseRules.ino.bin` starts at flash address **0x08000000**; the ELF and HEX retain their addresses.

## USB power policy

The same USB-C connector provides 5 V power and USB2 data. No USB Power Delivery contract or higher voltage is requested. Native USB enumeration advertises a **bus-powered device requesting 500 mA**. The actual compiled full-speed configuration descriptor was inspected: `09 02 43 00 02 01 00 80 FA`; the last byte is 250 units of 2 mA, not 250 mA.

Driver SDB stays low during startup and charger detection. ISET=47k sets conservative physical peak current; firmware selects:

- **GCC 64** after USB configuration grants the 500 mA configuration, after a stable conservative Type-C >=1.5 A indication, or after positive BC1.2 CDP/DCP detection.
- **GCC 8** for an unconfigured/default-current source while not suspended: approximately 43 mA nominal average LED load. The MCU, regulators and four drivers must still be measured to confirm total input current below 100 mA, including startup transients.
- **Hardware shutdown** for host suspend, an I2C error, or a source state that permits no LED load. A fault remains latched dark until reset.

The Type-C ADC qualification requires a raw CC voltage within 0.8-2.2 V, stable for 100 ms. Each measured divider output is doubled to estimate raw CC voltage. The threshold is intentionally conservative; some valid low-edge 1.5 A sources may remain dim. Removal of the qualifying CC voltage clears that allowance on the next 10 ms sample. This is detection of a current advertisement, not a PD negotiation.

### BC1.2 before data attachment

The build uses GNU linker wrapping without changing the installed core. STM32duino normally starts CDC from `premain -> init -> hw_config_init`, before the sketch's setup. The project wraps that early `USBD_CDC_init` call with a no-op. Actual USB initialisation occurs only at `setup -> SerialUSB.begin -> CDC_init`, after SDB has been configured low, the drivers have been cleared and CC has been sampled for 120 ms. This prevents an early USB suspend from entering STOP before charger qualification.

The project's strong override of the core's weak `USBD_reenumerate` helper **detaches D+ only**, waits 20 ms and leaves the data pull-up off. The original helper's reconnect is suppressed so there is no data attachment before charger detection, including after a reset from an already running USB session.

`__wrap_USBD_Start` then runs after the official core has initialised PCD and registered its CDC class, but **before** enabling the USB data pull-up. It calls the pinned HAL's `HAL_PCDEx_ActivateBCD` and `HAL_PCDEx_BCD_VBUSDetect`. The project's strong implementation of the HAL's documented weak BCD notification callback records SDP, CDP, DCP, error and completion results. Only a completed positive CDP or DCP classification grants charger current. A timeout or an idle cable never becomes proof of a charger.

For DCP, the USB data function remains detached and the artwork uses the charger allowance. For CDP/SDP, the wrapper continues normal USB attachment. The pinned G0 HAL algorithm includes 350 ms settling, 50 ms primary detection and its secondary checks; physical detection behaviour must be tested with real adapters. These software hooks were verified in actual ARM disassembly, not only by searching source text.

### Suspend and wake

The USB suspend hook immediately drives PB0/SDB low in interrupt context. The HAL-PCD initialisation hook enables the core's existing USB wake EXTI setup. On host suspend, or unqualified default-current suspend, the hook selects STM32G0 STOP0; the core's suspend callback gates the PHY and enters deep sleep on interrupt exit. Its resume callback restores the internal USB/system clocks and clears sleep-on-exit. Dedicated chargers remain data-detached; positively authorised charger/CC power with no enumerated host is kept distinct from host suspend.

**STOP entry, wake, I2C recovery, total suspend current, enumeration and source transitions need measurement on the real board.** Compiling and inspecting call flow cannot establish USB compliance. In particular, test suspend during an I2C update, long suspend, resume and re-enumeration. The SDB pull-down keeps the display dark during ROM DFU and MCU reset independently of application firmware.

## Programming

Native CDC is the running application's serial interface; it is **not** a USB flashing bootloader. Programming uses the STM32's factory system-memory **USB DFU bootloader** or the SWD recovery pads.

### Actual USB diagnostic commands

Open the application's USB serial port in a terminal at 115200 baud; CDC ignores the physical baud rate. Send a single lowercase character; a line ending is optional. The terminal receives a short confirmation when DTR is active.

| Command | Display mode |
| --- | --- |
| `w` | One walking pixel, 100 ms per dot, down each column then across; repeats after all 245 |
| `a` | All 245 pixels on, through normal PWM/current control |
| `c` | Alternating checkerboard |
| `p` | Return to artwork and restart its initial lead-in |
| `r` | Restart the current mode; walking returns to the first dot |

Artwork remains the power-on default. Diagnostic selections live only in RAM and reset on power cycling. All modes retain the same source qualification, GCC limit, fault shutdown and USB suspend behaviour. `a` cannot force full current from an unqualified source. A dedicated charger has no serial host, so select diagnostics while powered from a configured computer for the all-on bench tests. Separate charger-classification tests can use normal artwork. Do not substitute a continuously powered source-swap test without implementing reclassification first.

A blank flash device normally enters the factory bootloader. Connect with a USB **data** cable to a computer and use STM32CubeProgrammer's USB connection to load the addressed ELF/HEX or the BIN at 0x08000000. Confirm the exact part, detected bootloader and option bytes before writing. The application's SDB output remains low until initialisation and power checks complete; in DFU the external pull-down performs this job.

**On this exact MCU, BOOT0 is PA14/SWCLK, physical pin 25. It is not PB8.** The boot input shares the SWD clock pad, so the PCB's momentary BOOT pull-up and programming fixture must preserve normal SWD operation.

After the first application is loaded, physical BOOT entry depends on the G0 boot-selection options. In STM32CubeProgrammer's **Option Bytes** panel, verify/set the hardware-pin selection `nBOOT_SEL` (called `nBOOT0_SEL` in AN2606) to 0, `nBOOT1` to 1, `BOOT_LOCK` to 0, and leave `nBOOT0` at 1 (ignored in hardware-pin mode). Keep `RDP=0xAA`, level 0, for bring-up. Apply and read back these settings on the identified G0B1 device; do not substitute option-byte names from another STM32 family. The application does **not** change them automatically.

To test recovery after first programming: hold BOOT0/PA14 high through the board's BOOT control, assert RESET low, release RESET, then release BOOT after bootloader entry. Confirm USB DFU reconnects before fitting the enclosure. Pressing BOOT alone does not reset the MCU. Retain SWD recovery and test it as well. The source is [AN2606 system-memory boot mode](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf), Pattern 11, together with the G0B1 datasheet's UFQFPN32 pinout; see ST's [empty-check explanation](https://community.st.com/stm32-mcus-60/empty-check-mechanism-on-stm32-42).

The project includes a usable compiled image for later bench bring-up; no attached hardware has been programmed, no option bytes have been modified and no physical USB test has been performed.

## Playback and verification

The portable `player.h` consumes the generated data directly and advances at nominal 60 fps using rational column offsets. `test_player.py` compiles it for the host, compares **60,000 frames** with an independent schedule generated from the exported metadata, verifies two complete traversals and the initial lead-in/repeat contract, and checks every driver's encoded pixel allocation. The actual board's refresh/timing, four-chip update artefacts and scroll speed still need an optical bench comparison.

The I2C bus runs at 400 kHz. Failed transactions latch SDB low. Writes use bounded chunks; only the 80 active PWM bytes per chip are refreshed. Unused outputs are zeroed at initialisation. Before enabling SDB, the code observes more than the manufacturer's 10 microsecond I2C quiet interval on each side of its rising edge, then releases software shutdown. Actual rise times, clock stretching, current accuracy and ghosting remain hardware checks.

Primary implementation sources: [STM32duino 3.0.0](https://github.com/stm32duino/Arduino_Core_STM32/tree/3.0.0), [G0 HAL BCD implementation](https://github.com/stm32duino/Arduino_Core_STM32/blob/3.0.0/system/Drivers/STM32G0xx_HAL_Driver/Src/stm32g0xx_hal_pcd_ex.c), [core CDC initialisation](https://github.com/stm32duino/Arduino_Core_STM32/blob/3.0.0/libraries/USBDevice/src/cdc/usbd_cdc_if.c), [core PCD suspend/resume](https://github.com/stm32duino/Arduino_Core_STM32/blob/3.0.0/libraries/USBDevice/src/usbd_conf.c), and the manufacturer driver datasheet saved under `hardware/reference/`.

## Artwork data

Regenerate from the existing recreation, using Python 3.9 or newer and no additional packages:

```sh
python3 hardware/tools/export_sequence.py
python3 -m unittest discover -s hardware/tests -v
```

The exporter parses selected constant assignments in `main.py`; it does not import the program or run pygame, display detection, or its event loop. `sequence.json` remains the source for the text and command order. Changing the source and regenerating updates the data; rebuild the firmware afterwards.

| File | Use |
| --- | --- |
| `generated_sequence.h` | C/C++ arrays for a microcontroller with memory mapped program flash, such as an RP2040 or STM32. AVR targets need a separate `PROGMEM` adapter. |
| `sequence_columns.bin` | The same packed column bytes without C syntax. Pair with the manifest if loading from storage. |
| `sequence_manifest.json` | Command types, offsets, lengths, flash frame counts, next-command indexes, timing constants, and source checksum. |
| `verification.txt` | Recorded host checks and SHA-256 hashes for this export; refresh the record after changing the artwork or exporter. |

The current export has **39 commands and 23,574 column bytes**. Each byte represents one column: bit 0 is the top pixel and bit 6 the bottom pixel; bit 7 is unused. A full display frame is therefore 35 bytes. The export stores each scrolling strip once and each flash screen once, rather than storing every rendered frame. It includes the exact variable width font from `main.py`, including a blank column after every character, the phrase gaps, and the absolute punctuation positions. Punctuation replaces existing columns, as in the original helper.

### Playback data contract

Start at command 0. Run the artwork scheduler at a nominal **60 frames per second**, independently of the driver's much faster multiplex scan. The scrolling rate is **47.5 columns per second** (95/2). Advance scrolling time before drawing each frame, as `main.py` does. Read 35 bytes beginning at the integer part of the scrolling offset and pad beyond the command length with zeroes. Draw the terminal scrolling frame before moving to the next command when the integer offset reaches `length - 35`. Short scrolling strips render one frame before advancing.

A flash command draws its stored 35 columns for `flash_frames` scheduler frames. The source's `flash-duration` is a frame count, so 12 frames means approximately 200 ms at 60 fps, not 12 seconds. Follow each command's `next_index`: the final scrolling command returns to **command 1**, so command 0 acts as the initial lead-in. A final flash command would wrap to command 0. This asymmetry is copied deliberately from the recreation and should be checked against the reference before changing it.

The prototype player implements these exported timing constants and transitions using a monotonic microsecond scheduler. A real device must still confirm motion against the reference. The desktop's elapsed-time scrolling, nominal frame cap, floating point rounding, and the browser's refresh rate can produce small timing differences. The host checks compare every generated pixel against the existing Python helpers and preserve the source parameters; they do not establish physical brightness, refresh performance, or exact wall-clock synchronization with the reference.
