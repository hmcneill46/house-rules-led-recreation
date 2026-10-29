# B2 physical-connection emulator

Run from the repository root:

```sh
python3 hardware/revisions/B2/simulation/test_model.py
```

Requires Python3 and a C++11 compiler (`c++`, provided by Apple's Command Line Tools). The small bridge compiles in a temporary directory; no downloaded Python packages or hardware are needed. The result is saved in [verification.json](verification.json).

The bridge executes the **actual B2 firmware** `encodePhase()` and `serialBytes()` functions. Python then shifts those64 wire bits through four simulated16-bit devices in the order established by the actual SIN/SOUT nets. It follows physical TLC59282RGER output terminals2..17, PMOS gate/source/drain connections, and the raw matrices' independent diode pin diagram to reconstruct the visible pixels. It deliberately does not import the firmware's logical row/gate map or assume `module//2` is how the electrical wiring works. Cosmetic pin labels do not control its decoding.

The tests cover all245 individual dots, all-on and checkerboard patterns, and60,000 artwork frames covering all39 commands and two complete traversals. An independent Python artwork player checks the emitted frames against the immutable column data, and the B2 artwork files are compared byte-for-byte with A1. Each phase is also checked individually, so a wrong selected column cannot be concealed by combining the five phases.

The physical IREF resistors are now 6.8 kΩ Basic C23212 parts. The model reads their values from the connection source and reports 7.42493 mA nominal per lit diode, 363.82 mA for 49 simultaneous diode paths, 341.99 mA LED average at full duty, or 18.19 mA at the 25 µs DIM setting. These figures exclude controller/driver overhead and component variation; they are nominal calculations rather than measured USB input currents.

Intentional faults confirm that the model catches reversed LED polarity, shared cathodes, reversed PMOS source/drain, multiple enabled columns, missing gate selection, enabled unused sinks, an unpowered driver with its LED supply still present, swapped physical TLC output connections, and reversed serial chip order. BLANK and both rails off produce darkness even with all-one shift data.

The USB front-end check independently follows the ten physical BQ24392 terminals. It verifies separate connector and MCU data pairs, GOOD_BAT on the always-on 3.3 V rail, the 10 kΩ charging-status pull-up, and worst-case detector-divider logic levels. Three additional injected faults swap the USB sides, move GOOD_BAT to the switched rail, or make the divider unable to meet the MCU's input-high threshold. This checks wiring and static voltage levels; it does not simulate charger detection or USB transactions.

This is a **functional connectivity model**, not an analog circuit or thermal simulator. It cannot certify physical module orientation, MOSFET gate settling, ghosting, USB enumeration/inrush/suspend current, brightness matching or temperature. It reads the schematic connection source; final routed-PCB net parity and DRC are separate checks. Those limitations are retained in the machine-readable report.

Physical reference constants are transcribed from [TI TLC59282](https://www.ti.com/lit/ds/symlink/tlc59282.pdf), [TI BQ24392](https://www.ti.com/lit/ds/symlink/bq24392.pdf), [AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf) and [Wenrun LMD07057AUE](https://cdn.shopify.com/s/files/1/0695/1347/8453/files/LMD07057AUE.pdf).

The owner separately verified all12 terminal roles/order and upright orientation on one `LMD07057AUE-101B-02` by diode test on29 October2026; the correct front view has the part-number label on the left. The other20 modules are not yet verified. This physical evidence is recorded in [the owner test report](../reports/owner-led-diode-test-2026-10-29.json); it is separate from the emulator and does not certify powered-board behavior.
