# Assembly and first-test guide

This guide is for the **engineering prototype**, not a declaration that it is ready to order. Check the current KiCad reports and [design summary](design-summary.html) first. The two useful checks you can do before owning a PCB or multimeter are **paper fit** and **low-current LED identification**.

## 1. Check the seven-module fit before ordering

1. Select and label three groups of seven modules. Keep their printed markings and orientation consistent. Do not assume all 21 have identical dimensions or polarity.
2. Print [pin-fit-template.svg](mechanical/pin-fit-template.svg) on A4 at **100% / actual size**. Disable “fit to page”. Measure its **50 mm check scale** with a ruler before trusting any other dimension.
3. The template includes front and rear views. Match the stated view; a rear view is horizontally mirrored. The front view shows holes through the module outlines, not holes visible through the plastic.
4. Arrange all seven bodies touching along their long edges, with the short five-dot edges at the top. Compare every lead position with the relevant diagram. A thin paper/card copy with carefully made holes can help check insertion, but do not force or bend the leads to make the drawing fit.
5. Check that the main PCB outline remains hidden behind the actual group. Record the combined width, individual body widths, lead-strip spacing and any gap or interference. A caliper is helpful; the full-size lead fit is more decisive than the earlier approximate ruler measurement.
6. Repeat for all three selected groups. If the first modules align but the last ones progressively drift off the holes, the module pitch needs revision before fabrication. Do not compensate by forcing the last display into place.

The current PCB uses **0.9 mm holes and 1.4 mm copper pads** for nominal 0.5 mm leads. That gives insertion clearance, not permission to ignore accumulated body/pitch tolerances. The temporary [alignment tray](mechanical/alignment-tray.stl) keeps the fronts level; it is not proof of the PCB footprint or pin numbering.

## 2. Make a low-current tester without a multimeter

Use a **two-AA battery holder** with insulated leads, two cells, one **1 kohm resistor** (a common 1/4 W type is suitable), and two probe leads or small clips. A breadboard or insulated clips can join these without soldering.

```text
Two-AA holder +  ---- 1 kohm resistor ---- red probe   → LED anode
Two-AA holder -  ------------------------ black probe → LED cathode
```

Keep the resistor permanently in the positive lead so it cannot be accidentally bypassed. Two fresh alkaline cells are roughly 3–3.2 V. Even a short between the probes is limited to approximately 3.2 mA; a red dot normally receives around 1 mA. Disconnect the battery holder between changes.

**Do not connect a loose module directly to 5 V or directly across the batteries.** The assembled board accepts USB power because its drivers limit LED current. This simple tester uses its series resistor instead. Use exactly two AA cells; do not substitute a higher-voltage battery or USB supply for this procedure.

### Confirm the variant and physical numbering

The supplier document is for **LMD07057AUE-101B**; the photographs show an additional suffix. That suffix and the actual pin-1 corner still require confirmation. The nominal electrical map is:

| LED function | Visual order | Datasheet terminal numbers |
| --- | --- | --- |
| Positive column anodes | Left to right | 1, 3, 10, 7, 8 |
| Negative row cathodes | Top to bottom | 12, 11, 2, 9, 4, 5, 6 |

If the physical numbering/orientation has been confirmed, red on **pin 1** and black on **pin 12** should light the top-left dot in the datasheet's front view. Test briefly. If it does not, do not raise the voltage or conclude that the module is defective: first check the view, batteries, resistor connections and variant.

If pin numbering remains uncertain, use temporary labels instead of guessing:

1. Mark one short edge as **TOP**. Photograph the front and rear with this same edge at the top.
2. On the rear-view sketch, label the six leads on the left **A–F**, top to bottom, and the right **G–L**, top to bottom. These are your temporary labels, not datasheet pin numbers.
3. Put red on A and briefly touch black to each other lead, one at a time. Record every lit dot. Repeat with red on B, C and so on. Keep clips from touching adjacent leads.
4. A matching module should reveal **five positive column connections and seven negative row connections**, forming all 35 dots. Record the front-view row/column for each successful pair. Use this [blank table](#led-identification-record) to make the results unambiguous.
5. Compare the observed topology and orientation with the datasheet/template before assigning physical pin numbers. If the polarity is opposite, a dot is missing, or the sets do not match, stop and resolve the variant before ordering.

This is a low-current identification test, not a brightness or maximum-current test. Repeat enough checks on the other modules to detect mixed parts; ideally walk all 35 dots on each of the 21 before committing them to an assembly.

### LED identification record

| Module label / printed suffix | Red lead | Black lead | Lit dot, front view (column 1–5 / row 1–7) | Photo / note |
| --- | --- | --- | --- | --- |
| | | | | |
| | | | | |

## 3. Prepare for PCB assembly

Have the factory assemble the small surface-mount components. Keep the LED positions unpopulated, with their through-holes open. Prepare the main PCB, USB carrier, correctly pinned six-wire harness, seven checked LEDs, alignment tray, 3 mm spacers, electronics solder, flux, a fine-tip temperature-controlled iron and flush cutters.

The battery tester needs no meter. **Powered PCB bring-up does need a basic multimeter** for rail and harness checks; borrow one if necessary. A continuity/diode test plus DC volts is sufficient for the first checks. An inline USB current meter is useful later, but it cannot replace probes for the internal 3.3 V rail.

Use a closed, reputable USB supply or a computer USB port; all work here is low voltage. Do not open a mains adapter. Handle boards by their edges with power disconnected. Use ventilation and avoid touching the iron or melted solder.

## 4. Check the factory assembly before fitting LEDs

1. Compare the boards and component labels with the current assembly drawings/BOM. Inspect for damaged parts, solder bridges and blocked LED holes. If a hole is solder-filled, clear it with suitable tools or get help; do not push a lead through it.
2. With everything unpowered, verify the harness **by numbered pin**, not wire colour or the apparent plug direction:

   | Pin at both ends | Net |
   | --- | --- |
   | 1 | VBUS / 5 V |
   | 2 | USB D− |
   | 3 | USB D+ |
   | 4 | Ground |
   | 5 | CC1 |
   | 6 | CC2 |

   Confirm pin 1 connects to pin 1, and so on, with no unwanted adjacent connection. Keep the data pair together and the harness short. A visually similar reversed cable can connect power to a signal pin.
3. Check for an obvious sustained short between VBUS and ground, then 3.3 V and ground. A brief continuity beep while capacitors charge is not conclusive; an unexplained persistent near-zero reading needs investigation.
4. Connect the verified carrier/harness to the main board. Power briefly with no LEDs installed. Measure **VBUS near 5 V** and the regulated rail **near 3.3 V** using ground as the black-probe reference. Avoid bridging adjacent pads with a probe.
5. Confirm common driver **SDB is low** during reset/bootloader entry. If rails are wrong, a component rapidly heats, or current is unexpectedly high, disconnect and investigate before fitting LEDs.

At this stage the drivers may report open LEDs, which is expected. Absence of light is also expected. No component should be made to “work” by bypassing the current-setting resistors or protection.

## 5. Load and verify firmware

Follow the [firmware programming guide](firmware/README.md). Use a USB **data** cable to a computer. The prototype's native CDC interface is not the flashing bootloader; programming uses the STM32 factory USB DFU bootloader.

- A blank device normally enters factory boot mode. Use STM32CubeProgrammer to identify the G0B1 part and read its options before writing the provided image.
- For this part, **BOOT0 is PA14/SWCLK, pin 25**, sharing the SWD clock signal. After the first flash, physical BOOT entry requires the documented boot-selection options. Do not copy a PB8 boot recipe from another STM32 family.
- Apply/read back the boot options described in the firmware guide, then test BOOT + RESET and confirm USB DFU reconnects. Test SWD recovery as well before closing the enclosure.
- With no LEDs, the MCU should still enumerate as the application when attached to a computer. The display stays off during reset, charge detection and firmware loading.

## 6. Fit one LED module, then the other six

With the long printed spacer rails, tack and cool first, withdraw both rails, then complete the remaining joints. For the first-module pilot, the other six modules may sit unsoldered in the tray to support alignment; leave them in the tray when lifting out the PCB with DS1 attached, and remove all loose modules before powering the test. Once DS1 passes, return it to the jig and fit the remaining modules.


1. Disconnect USB. Match the tested module orientation to **DS1** and the verified pin-1 mark.
2. Use the tray to keep the LED face flat. Maintain the intended **3 mm body-to-PCB standoff** with spacers; do not press the epoxy body down onto the PCB. This also provides the manufacturer's requested separation between the soldering point and body.
3. Tack two opposite leads, inspect alignment and standoff, then solder the remaining ten. The supplier's manual-soldering notes specify a **295 ±5 °C tip, at most 3 seconds per joint**, and at least 3 mm from the epoxy body; check that these limits apply to the confirmed variant. Let a module cool before rework. Keep the iron away from the plastic and nearby factory-fitted components. Do not use reflow/hot air with the printed tray in place.
4. Inspect all twelve joints. Remove any bridge before power-up. Clip lead ends to the documented rear clearance, roughly 0.8–1 mm beyond the PCB where practical; do not leave sharp ends against the carrier or case.
5. With the supplied application, send `w` for the walking-pixel test described below. Every DS1 dot must light in the correct position without lighting a neighbour. Confirm measured current remains reasonable.
6. Unplug, fit DS2, inspect and test again. Continue one module at a time. This localises errors and avoids having to remove seven soldered displays to diagnose one reversed module.

The supplied application includes real USB serial diagnostics. Connect it to a computer with a data cable, open its serial port at 115200 baud and send one lowercase character:

| Command | Hardware test |
| --- | --- |
| `w` | Walking pixel, 100 ms per dot; down one column then across the display |
| `a` | All 245 dots on |
| `c` | Checkerboard |
| `p` | Return to artwork from its initial lead-in |
| `r` | Restart the current mode |

These select pixels without bypassing source qualification, the GCC limit or shutdown. The browser emulator cannot replace applying the patterns to the physical board. Diagnostic mode is not saved over a power cycle. Run all-on tests from a configured computer connection; test standalone charger qualification separately with normal artwork. Do not keep the board powered while swapping source types unless the firmware has first been extended to invalidate and reclassify the source.

## 7. Run the electrical and USB tests before enclosing it

Record the source, cable, test pattern, input voltage/current, mode and result for each test.

| Test | What to check |
| --- | --- |
| Walking pixel (`w`) | Correct orientation and mapping; all 245 pixels independent |
| Checkerboard and adjacent pixels | No swapped columns, duplicates, unintended dots or persistent ghosting |
| All-on, dim fallback | About 42.7 mA nominal LED load, plus MCU/driver overhead; measure total below the default-source allowance |
| All-on, fully authorised source | About 341.6 mA nominal LED load, plus overhead; confirm actual supply current and stable rails |
| Type-C orientation | Both plug orientations work; qualify the source rather than assuming any C cable grants high current |
| A-to-C computer | Dim before configuration; full current only after the 500 mA configuration is granted |
| BC1.2 DCP/CDP adapter | Only a completed positive charging-port result grants full current; an error/timeout must not do so |
| Host suspend / resume | Display immediately blanks, total suspend current is measured, and wake succeeds; also suspend during an I2C update |
| BOOT / RESET / DFU | Reliable recovery after an application has already been flashed |

The current figures are calculations, not acceptance measurements. Test with a known Type-C source and more than one ordinary A-to-C adapter. A source the firmware cannot qualify may remain dim or suspended; do not defeat its power policy to make it brighter.

For the all-on thermal run, record driver/MCU/case temperatures at roughly 5, 15 and 30 minutes, preferably with a thermometer. Inspect the actual driver temperature and the chosen printed plastic's limits; touch alone is not a thermal qualification. Repeat in the enclosure because its airflow differs. Confirm long playback, stable brightness and timing against the reference.

## 8. Finish the enclosure and the remaining replicas

Print a fit sample first. Check the bottom-right port relief with the actual cable overmould; a socket looking aligned in CAD does not prove the plug can seat fully. Check the USB stakes, clipped LED leads, main-board components, 3.5 mm board-to-board gap, harness bend and removable back. There must be no pressure on component bodies or exposed solder joints.

Make the case and carrier supports take insertion and cable loads. Keep the LED faces unobscured. Do not use the LED leads as mounting springs. Only after the pilot passes fit, power, thermal, USB and recovery tests should the other two sets of LEDs be soldered onto their boards. Retain the results and any assembly corrections for all three units.
