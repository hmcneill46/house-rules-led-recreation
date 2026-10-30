# B2 assembly and first test

**30 October: resolve the [new module-spacing trials](printing/pitch-tests-2026-10-30/README.md) before ordering the PCB.** The fitted strip bows at the current 12.70 mm repeat although each individual 12-hole group fits. The electrical pin map remains confirmed; the mechanical repeat and case fit need rechecking after a winning sample is selected.

The owner has identified an **ULTRICS UT0021YB** meter. Its diode-test mode can replace the two-AA/resistor tester: use the [specific meter and LED pin-test steps](led-diode-test.md). The owner has confirmed both complete probe sequences on one module: **all 12 pins match, with the part-number label on the left in front view**. Other modules still need consistent orientation and checks.

Start with one set of inexpensive stock electronics and a trial print. Test their fit and programming **before spending money on the custom PCB**. B2 remains an engineering prototype: files marked `UNRELEASED`, `UNROUTED` or `DO-NOT-ORDER` are quotation studies, not order files.

## 1. Buy and check the stock modules first

For one display, obtain these versions **without fitted headers**:

- [Seeed XIAO RP2040 Plus](https://www.unmannedtechshop.co.uk/products/seeed-studio-xiao-rp2040-plus): £4.49.
- [Adafruit 4090 USB-C downstream breakout](https://thepihut.com/products/adafruit-usb-c-breakout-board-downstream-connection-ada4090): £2.90.

The current combined estimate is **£14.78 delivered**, including the two shops' cheapest quoted UK delivery, as checked 29 October 2026. Final checkout determines the actual price. These are the only electronics needed for this first step; keep the custom PCB order for later. [Price evidence](../../cost-down/module-shipping-quote.json).

Print the small fit coupon and trial enclosure in the [mechanical guide](mechanical/README.md). Check the actual boards, screws and intended USB plug against the channels, posts and plug well. Do not force the modules into a tight print or scale the whole case to fix one fit.

With the XIAO **loose and unwired**, use its own USB socket and a USB data cable. Hold BOOT while connecting it, or hold BOOT and tap RESET. A drive called `RPI-RP2` should appear. Copy [HouseRulesB2.ino.uf2](firmware/compiled/HouseRulesB2.ino.uf2) onto it; the drive disconnects. Open its USB serial port at 115200 baud and send `i` to check that the application responds. No display is attached yet, so no artwork will be visible; loose CC-input readings have no qualification meaning.

Repeat BOOT/RESET and the UF2 copy to prove recovery works. Before wiring the loom, load the [unknown-source OFF image](firmware/compiled-unknown-off/HouseRulesB2.ino.uf2) for first-board checks; keep DIM disabled until its total current is measured. UF2 can be replaced repeatedly; no separate programmer is needed. See [firmware instructions](firmware/README.md).

## 2. Confirm the owned LEDs

Use the [UT0021YB diode-test procedure](led-diode-test.md) to check the remaining modules against the now-confirmed pin map. It needs no external resistor. The older [two-AA-cell and 1 kΩ tester procedure](../../assembly-and-test.md#2-make-a-low-current-tester-without-a-multimeter) remains an alternative; keep its resistor in series and use exactly two AA cells. Do not connect a loose matrix directly to USB or directly across batteries.

Label a group of seven and check their fit/orientation together. The successful plastic fit does not confirm electrical polarity. Resolve a reversed map, missing dot or mixed module variant before soldering anything permanently.

## 3. Prepare the PCB and wiring

When the finished PCB has passed release checks, order factory assembly of its **55 small components**. Leave the seven LED positions and 20 owner wire pads unpopulated, with all 84 LED holes open. There is no second custom USB PCB.

The owner work is **14 MCU wires plus 6 USB-breakout wires**: 40 wire-end solder joints, followed by 84 LED joints, **124 joints per display**. Follow the exact numbered tables in [Wiring and strain relief](mechanical/README.md#wiring-and-strain-relief); front and rear views reverse left/right. Use the specified flexible wire and pre-tin the small XIAO backside USB pads **before fitting it in the cradle**. The main board's rear surface pads need gentle handling and strain relief.

Use the UT0021YB for continuity and DC-voltage checks before powered PCB tests. Also prepare solder, flux, a fine-tip temperature-controlled iron, flush cutters, the existing [alignment tray](../../mechanical/alignment-tray.stl), 3 mm spacers and the screws listed in the mechanical guide. Keep power disconnected during wiring or soldering.

## 4. Check the wired board before fitting LEDs

1. Inspect the factory assembly and every wire destination. Check for adjacent solder bridges, an obvious sustained power-to-ground short, and swapped USB data wires. Capacitors can cause a brief continuity beep; an unexplained persistent near-zero reading needs investigation.
2. Check that raw USB data reaches the detector's connector side and downstream data reaches the XIAO. Use the wiring tables; never bridge around the BQ24392 switch.
3. Once wired, power/program through the **external USB-C socket only**. Do not connect the XIAO socket as a second source, and do not fit a battery. This version uses 5 V; it does not request higher PD voltages.
4. Use the preloaded unknown-source OFF UF2 for initial checks so they do not rely on the unmeasured DIM budget. With no LEDs fitted, check approximately 5 V at `+5V` and 3.3 V at `+3V3`, referenced to GND. Stop if a rail is wrong, current is unexpectedly high or a part rapidly heats. Both driver rails should be disabled during reset; BLANK's pull-up follows its switched rail.
5. Confirm USB serial operation and repeat BOOT/RESET→`RPI-RP2`→UF2 loading **through the external connector**. Its detector/data path has not yet been physically tested. If this fails, unplug power and investigate the loom; do not add a second USB connection. Isolate the XIAO from the loom before returning to a bare-module native-socket test.

## 5. Fit one matrix as a pilot

Use DS1 first, with its electrically confirmed orientation. Keep a **3.0mm body-to-PCB standoff**. The other six modules may sit loose in the tray for alignment: tack two opposite DS1 leads, let them cool, withdraw the spacer rails, then complete its remaining joints. Remove all loose modules before powering the pilot. Follow the confirmed module's soldering limits in the original LED guide; keep the iron away from the printed jig and factory parts.

Inspect all 12 joints and trim rear lead projections to **at most 1.0 mm**. Send `w` over USB serial for the walking-dot pattern: only the fitted module's 35 positions should light, in the correct order, without neighbouring ghosts. Unplug before fitting the next module. Add and retest the remaining six one at a time.

## 6. Measure before closing the case

Use `w` for walking dots, `a` for all-on, `c` for checkerboard and `p` for artwork. `d` requests DIM; `b` restores automatic brightness. `i` reports sampled CC/BC/USB state and requested duty; **it does not measure current**.

| Check | Required observation |
|---|---|
| All pixels/artwork | Correct orientation, no missing dots, flicker or ghosting |
| Whole-device current | Measure startup, unknown-source DIM and qualified full-white; include controller/driver overhead |
| USB suspend/reset/resume | Dark display, reliable recovery; measure the complete device against the 2.5 mA suspend target |
| Power/programming | Repeat external-port UF2 recovery; test known 5 V sources and both C-to-C plug orientations |
| Scan edges/inrush | Have bench equipment check startup charge and the 30 µs gate/anode settling interval |
| Enclosed temperature | Run qualified full-white in the case; check drivers, MCU regulator and nearby plastic |

Nominal LED-only averages are **341.99mA full-white** and **18.19mA DIM**, plus electronics overhead and component variation. These do not certify whole-device 500 mA/full or 100 mA/unconfigured budgets. Darkness alone does not prove suspend compliance, and a basic USB meter may lack the resolution or bandwidth for suspend/inrush checks. Record measurements before relying on those modes.

The conservative 800 mV CC threshold can leave some valid 1.5 A sources dim unless another USB/BC grant applies. Qualify/calibrate the actual supplies and ADC path before claiming all Type-C sources work at full brightness; [threshold review](reports/type-c-adc-threshold-review.md). Firmware can change after measurement without changing the PCB.

Once the pilot passes, secure the boards and loom exactly as described in the mechanical guide. Fit both the rear-cover tie and the removable tack on main-board soldermask: a tie on the lid alone cannot protect its surface pads. Keep wires out of screws and lips, leave a service loop, and never let the open lid hang from the loom. Complete the first unit's checks before assembling the other two.
