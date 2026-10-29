# B2 prototype firmware

This firmware is for the **XIAO RP2040 Plus, 2 MB**, four TLC59282 sinks, five PMOS scan columns, BQ24392 charger/data switch and three TPS22918 switches on revision B2. Two switches control the driver rails; the third limits input startup slew. It preserves the A1 artwork, scrolling speed, flash durations and 35 × 7 pixel orientation. The artwork data/header/manifest are byte-for-byte copies of A1; `artwork-provenance.json` records their hashes.

**Do not flash this image to A1 hardware.** B2 uses a different controller, driver interface and power arrangement. No physical B2 has been connected or tested yet. The final PCB net map must be compared with `scan-map.json` before a manufacturing release. Host simulation and compilation do not validate LED pin polarity, switching edges, USB current, mounting or soldering.

## Loading and using it

Use a USB-C **data** cable. On the loose stock XIAO Plus, hold BOOT while connecting USB, or hold BOOT and tap RESET. The RP2040 boot ROM exposes a drive named `RPI-RP2`. Copy `compiled/HouseRulesB2.ino.uf2` onto it; the drive disconnects and the artwork starts. This method does not require an external programmer. Re-enter BOOT mode to recover from a bad firmware image. After initial programming, the included USB CDC interface also supports the Arduino core's 1200-baud bootloader reset.

The normal image uses a dim prototype mode on an unqualified supply. `compiled-unknown-off/HouseRulesB2.ino.uf2` instead leaves the LEDs off until a 500 mA USB configuration, suitable Type-C current advertisement or valid BC1.2 charging-source indication is recognized. This alternative is available if first-board current measurements require it.

The same connector provides 5 V power and USB programming/diagnostics; no USB Power Delivery negotiation is needed. Firmware requests 500 mA in a bus-powered USB descriptor. A separate BQ24392 qualifies a compatible charging port when using an A-to-C cable, while its USB switch retains the data path for a computer. A charge-only cable can power the display but cannot program it.

A serial terminal can send single characters at any line ending; 115200 baud is a conventional setting for USB CDC:

| Character | Action |
|---|---|
| `p` | Original artwork |
| `w` | Walk through all 245 dots, 100 ms per dot |
| `a` | All dots lit, within the current power policy |
| `c` | Checkerboard |
| `r` | Restart the selected pattern |
| `d` | Cap brightness at the dim level |
| `b` | Restore normal automatic brightness |
| `i` | Print the most recently sampled CC values, source grants, USB state and requested light time |

The `i` response is a short line such as `CC=950,0 C=1 B=0 USB=1 H=1 S=0 ON=470`. CC values are estimated raw millivolts before the divider; `C` and `B` are qualified Type-C and BC1.2 grants, `USB` is the configured host grant, `H` means a host was observed, and `S` is the USB suspend flag. `ON` is the requested microseconds of light within each 500 µs phase. This reports firmware observations, **not measured supply current or electrical compliance**. The print is skipped if the USB output buffer lacks space; repeat `i` if needed. A standalone charger supplies no serial host, so a USB computer is required to read diagnostics. Do not attach a second USB source to the XIAO socket.

The artwork engine advances at an exact average 60 frames/s independently of the multiplex scan. The display scans five 500 µs phases: **400 complete frames/s**, with 30 µs blank time before each phase. Qualified full brightness lights for 470 µs per phase; dim lights for 25 µs. The SPI clock is 8 MHz; shifting 64 bits takes 8 µs and the latch pulse is 1 µs, within the blank interval. All five 64-bit words are prepared in the foreground so the timer interrupt only copies a prepared word and shifts it. The next image is committed only at the first phase to avoid tearing.

## Electrical contract and power

`scan-map.json` is the mapping source. `tools/firmware-build/generate_contract.py` checks it and generates the C++ header. The current arrangement maps modules 0/1 to U1 OUT0–13, modules 2/3 to U2 OUT0–13, modules 4/5 to U3 OUT0–13 and module6 to U4 OUT0–6. U4 OUT7–11 pull down the five PMOS gates. Exactly one gate bit is active per scan phase; all unused outputs stay zero. The 64 serial bits go to the farthest chip first, U4 through U1, MSB first.

| Function | Raw RP2040 GPIO |
|---|---:|
| SIN / SCLK / LAT / BLANK | 3 / 2 / 4 / 28 |
| Both switched-rail enables | 6 |
| CC1 / CC2 ADC | 26 / 27 |
| BC1.2 CHG_DET / CHG_AL_N | 7 / 0 |

Each CC ADC is behind a 47k/47k divider. The firmware conservatively accepts raw CC of 0.80–2.20 V on exactly one orientation for 100 ms, allowing some 1.5 A and 3 A advertisements. It immediately withdraws that qualification when the input becomes invalid or changes orientation. ADC/divider tolerance and the actual source advertisements need bench checks. A configured 500 mA host also enables full brightness.

The BQ24392 has GOOD_BAT tied to the always-on 3.3 V rail. Its CHG_DET output passes through a 10k/15k divider to GPIO7; its open-drain CHG_AL_N output has a 10k pull-up to always-on 3.3 V and reaches GPIO0. TI's truth table permits a separate charging grant only when **CHG_DET is HIGH and CHG_AL_N is LOW**. Both must remain in that state for 100 ms. Either invalid indication withdraws the grant immediately at the next 10 ms policy sample. CHG_AL_N HIGH/HiZ always rejects the BC grant, including when CHG_DET is HIGH. CHG_DET LOW with CHG_AL_N LOW identifies the low-current/SDP case and requires USB configuration or an independent Type-C grant. Do not reinterpret DET alone as permission to draw 500 mA.

A real host's suspend state takes precedence over every source grant; its display goes dark. An idle charger with no observed USB bus reset/mount can retain the unqualified dim behavior or qualified Type-C/BC1.2 behavior. The detector keeps its USB data switch closed for a valid SDP/CDP after detection; the initial detection delay and both normal UF2/CDC programming paths require physical verification through the external socket.

A small shared USB IRQ observer records hardware bus reset/suspend/resume before TinyUSB clears the status. This covers host suspend before the first SETUP packet, which the library's ordinary suspend callback intentionally skips. It uses the verified handler insertion order of the pinned SDK and requires physical reset/enumeration/suspend/resume testing.

Both driver 3.3 V and LED 5 V are switched off for host suspend. TLC BLANK alone does not reduce chip quiescent current enough. Startup holds control data low and BLANK high impedance while the external pull-up follows the switched 3.3 V rail; after 10 ms it asserts BLANK, latches all-zero outputs, then starts scanning. Shutdown asserts BLANK, latches zeros including the gate bits, waits 30 µs, parks SIN/SCLK/LAT low, makes BLANK high impedance and removes both rails. Cancelling startup never drives high logic into a partially powered driver rail.

The CPU runs at **48 MHz**, the WS2812 power pin GPIO11 stays off, GPIO12 stays low, GPIO25 stays low to switch off the green user LED through its N-MOS gate and BAT_EN GPIO24 stays low. The Plus board's power/charging indicators and regulator draw cannot all be disabled in software. Host suspend changes the system clock to 12 MHz, preserves USB's 48 MHz PLL/clock and uses the SDK's SLEEP_EN/SLEEPDEEP clock gating around WFI. Only the two USB-controller clock destinations plus timer/watchdog timekeeping remain enabled in sleep; the prior masks and processor sleep state are restored before IRQ handlers run. WAKE_EN is unchanged so SRAM/XIP/bus clocks return on wake. Core1 stays parked and no DMA is used. Dormant mode is avoided because it would stop the USB clock. A 250 ms watchdog resets an active stalled foreground; timing/SPI/map errors latch the display dark. A lost scan callback is also checked in the foreground. The scan alarm has higher interrupt priority than the USB task so ordinary CDC traffic cannot hold off the dim-pulse turn-off; stress this timing on the prototype.

**Current budgets remain unvalidated.** At the specified 6.8k current-setting resistors the electrical target is about 7.425 mA peak per selected LED. Default unknown-source dim gives about 18.191 mA average LED current. Together with driver and stock-module current, the design target is below the USB unconfigured 100 mA allowance, but code cannot prove this. Measure the whole device before relying on that default. Measure the entire device during real USB suspend and after reset as well; rail shutdown and low clock do not establish the 2.5 mA suspend limit. If the stock module cannot meet it, hardware or further verified power management must change before release. Scope PMOS/anode turn-off to qualify the physical 30 µs blank interval.

## Rebuilding and verification

The build is isolated from A1 and from the user's normal Arduino installation. It uses Arduino CLI 1.5.1 and official Arduino-Pico 6.3.1, with its bundled Adafruit TinyUSB stack. The selected Arduino board is `seeed_xiao_rp2040`; the Plus shares that software target but requires explicitly selecting **2 MB** flash and using its different onboard LED pins. The build overrides `F_CPU` to 48 MHz rather than using the target's 125 MHz default. A linker wrapper defers the core's early USB initialization so setup can install the bus-powered 500 mA descriptor before host requests are served. Neither the installed core nor A1 files are patched.

From the repository root:

```sh
python3 hardware/revisions/B2/tools/firmware-build/setup.py
python3 hardware/revisions/B2/firmware/tests/test_host.py
python3 hardware/revisions/B2/tools/firmware-build/build.py
python3 hardware/revisions/B2/tools/firmware-build/build.py --unknown-off
```

`setup.py` reuses the existing pinned CLI executable and installs the core in `~/.cache/house-rules-b2-arduino`. `build.py` saves the build log, hash metadata, UF2, BIN and ELF. Its static binary audit validates every UF2 record/family/flash address and confirms the actual linked early-USB wrapper, strong suspend/resume callbacks, 48 MHz init hook and descriptor writes under disabled interrupts. Small disassembly excerpts make that evidence reviewable. The full descriptor is created in RAM at runtime, so this audit is not a substitute for a real host capture.

The host verification executes 60,000 artwork frames against an independent manifest/data reference, all 245 individual pixels and 1,000 random patterns. It checks serial order, unused outputs, one gate per phase, full/dim scan timing, frame boundaries, missing/late interrupts, SPI faults, CC qualification, the BQ status truth table and withdrawal, all 64 source/suspend policy combinations, switched-rail sequencing and the diagnostics. Results are in `tests/verification.json` and `compiled/binary-audit.json`.

Primary references: [Seeed Plus hardware/pin details](https://wiki.seeedstudio.com/XIAO-RP2040/), [Seeed Arduino and BOOT procedure](https://wiki.seeedstudio.com/XIAO-RP2040-with-Arduino/), [TI BQ24392 datasheet, Tables 2–3](https://www.ti.com/lit/ds/symlink/bq24392.pdf), [Arduino-Pico USB stacks](https://arduino-pico.readthedocs.io/en/latest/usb.html), [USB serial reset behavior](https://arduino-pico.readthedocs.io/en/latest/serial.html), [official package index](https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json), [Raspberry Pi SDK power/clock functions](https://www.raspberrypi.com/documentation/pico-sdk/high_level.html).
