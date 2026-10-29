# Check the owned LEDs with the ULTRICS UT0021YB

No resistor or external supply is needed for this test. The [manufacturer's user guide](https://ultrics.uk/wp-content/uploads/2021/12/main-file-Uk-v2_compressed.pdf), specification page 04 and operating page 06, specifies approximately **2.8 V / 1.5 mA** in diode mode. That is a low-current test suitable for the loose red matrix. This is not an instruction to use the meter's current ranges as a supply.

1. Remove one LED module from the breadboard and disconnect everything from it. Opposite breadboard contacts may be linked internally; this test must use the loose module.
2. Put the black lead in the **middle COM socket**, and the red lead in the **right VΩmA socket**. Leave the left 10A socket empty.
3. Select the **diode symbol next to the green 2k marking**, around seven o'clock on the dial. Use the diode position, not a current range. Release HOLD if it is active.
4. Keep the module upright, with the seven-dot dimension vertical. Choose one short edge as TOP and keep that edge identified when turning it over.
5. Looking at the **rear pins**, touch red to the topmost right pin and black to the topmost left pin. Avoid touching neighbouring pins. Look at the front while keeping the chosen TOP edge at the top; a dot should glow faintly. A mirror or viewing the face at an angle can help.
6. Record which front dot lights, or that none does, plus which edge carries the printed part number. Do not change the chosen TOP silently. A different dot can identify a rotated module; it does not automatically mean a faulty one.

The candidate numbering, **rear view with pins towards you**, is:

```text
              chosen TOP
       left                 right
black →12  o               o  1 ← red
       11  o               o  2
       10  o               o  3
        9  o               o  4
        8  o               o  5
        7  o               o  6
```

With the candidate's correct upright orientation, pin1 positive / pin12 negative lights the **upper-left front dot**. The first observation establishes whether that orientation matches the owned part. Do not assign manufacturing approval from the assumed numbers alone.

Once the orientation is established, eleven observations cover every terminal:

| Red probe | Black probe sequence | Expected front pattern |
| --- | --- | --- |
| Pin1 | 12,11,2,9,4,5,6 | First column, top to bottom |
| 1,3,10,7,8 | Pin12 | First row, left to right |

The shared first dot is counted only once. Check one complete module, then enough of each remaining module to catch a mixed variant; all35 dots can be checked if desired. Keep a record of the printed suffix and TOP orientation. The design assumes five positive anodes and seven negative cathodes. The [full-size front/rear template](../../mechanical/pin-fit-template.svg) uses the same numbered map.

The display reading may indicate the forward drop, while an open/over-range indication can appear as a leading `1`. Observe the dot as well; do not raise the voltage or change to a current range to force it to light. If the test does not produce a clear observation, check the meter battery, mode, probes and contact before drawing conclusions about polarity.

For later PCB rail checks, the same meter's 20 V DC range is suitable for nominal5 V/3.3 V. Its200 mA input is **not** suitable for the complete display's approximately430 mA planning load. The manual limits the10 A range to10 seconds and does not guarantee fuse protection there; do not leave it inline for a long temperature test. A later current-test procedure must use the appropriate series connection/range, never place a current-mode meter across the supply rails.

**Owner verification, 29 October 2026:** with the printed part number on the right in front view, the first pair lit the top-row second dot. Rotating the module 180° so the part number is on the **left** lit the top-left dot. The owner then confirmed **both complete probe sequences match**: all 12 terminal roles/order and the front orientation are verified for one owned `LMD07057AUE-101B-02`. No PCB pinout change is needed. Keep this module marked and orient the other modules consistently; the other 20 modules and PCB-powered tests are not yet verified. [Recorded evidence](reports/owner-led-diode-test-2026-10-29.json). The successful printed seven-module fit remains a separate mechanical observation.
