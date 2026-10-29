# LED matrix functional model

Open `matrix-emulator.html` in a browser. It is a single offline file with no external packages, assets or network calls. It plays the existing artwork, or displays a walking pixel, checkerboard or all-on diagnostic. Point to a dot to inspect its module terminals, driver, scan switch, sink and PWM register. The scan selector shows the five individual anode phases.

This is a **functional model, not an analogue circuit or hardware emulator**. It does not execute MCU machine code. It establishes whether the proposed terminal connections and software register mapping can represent the intended 245 pixels without aliases. Physical footprint orientation, actual current accuracy, voltage headroom, ghosting, brightness, temperature, USB compliance and fabrication quality remain hardware checks.

## Independent paths

`matrix_model.py` defines the Wenrun module's internal diodes independently from the project's connection CSV:

- Five column anodes: module pins 1, 3, 10, 7, 8.
- Seven row cathodes: module pins 12, 11, 2, 9, 4, 5, 6.
- Each physical diode is a path between one anode and one cathode.

The CSV supplies which driver terminal is wired to each module pin. The model traverses the physical diode paths to reconstruct the visible screen from driver registers. The encoder's logical mapping is implemented separately. Consequently, swapping rows causes a detectable displayed-pixel mismatch, swapping source/sink polarity is rejected, and accidentally joining paired modules' cathodes produces a detectable address alias. A model that drew the intended framebuffer directly would miss these mistakes.

The four chips serve 2 + 2 + 2 + 1 modules with five high-side scans. It also checks the driver's package pin numbers and the generated pixel-map CSV against these derived paths.

## Power and startup

The relevant IS31FL3729 registers are modelled: reset, PWM, per-CS scaling, global current, scan count, software shutdown, hardware SDB and 32 kHz PWM selection. SDB rising requires a 10 microsecond I2C quiet window before and after, as specified by the manufacturer. The prepared state leaves both shutdown controls active and all PWM values zero.

Peak current is computed from `342/R_ISET × GCC/64 × scaling/256`. With 47 kohm and scaling 255, nominal peak is about **7.25 mA**. Average current includes `PWM/256`, five scan slots and the 30/(30+0.8+0.27) slot utilisation. All 245 dots at maximum PWM use about **342 mA average LED current**. The idealised simultaneous active-slot upper bound is about **355 mA**, before driver/MCU overhead. These are calculations, not measurements or maximum-tolerance component guarantees. The host test includes 1% low resistor tolerance; driver current-regulation error is not modelled.

The optional generic `PowerPolicy` demonstrates strict blanking until an allowance is authorised, or PWM capping under a reduced average-current budget. The separate `firmware_power_gcc` and `apply_firmware_power` functions match the actual prototype policy: shutdown during initial preparation; then a **GCC8 dim fallback** for unqualified default-current power, and **GCC64** for configured USB 500 mA, positively advertised Type-C current, or a completed positive BC1.2 CDP/DCP result. A timeout, error, incomplete or SDP classification does not grant charger current. Host suspend blanks even when a charger allowance was previously established.

The dim fallback reduces instantaneous dot current to about 0.91 mA and all-on average LED load to about 42.7 mA. Add the provisional 30 mA controller/driver reserve and the nominal result remains below 100 mA. A configured 500 mA allowance accommodates the full nominal all-on load with that reserve. These allowances require real input-current measurements. PWM capping limits average load but does not reduce instantaneous dot current; GCC and the hardware ISET resistor do.

The browser's supply selector is **an injected test condition**. It does not detect USB CC advertisements or enumerate a real USB device. Actual firmware must establish the available current, respect configuration/suspend states and perform any charger/Type-C detection required by the final circuit. LED shutdown alone does not establish compliant total USB suspend current: the MCU, regulator and detection circuit's low-power behaviour also need verification.

The electrical source is the manufacturer-authored IS31FL3729 Rev. D datasheet saved under `hardware/reference/`; the Wenrun diode topology is from its module datasheet. The browser's artwork scheduler uses a continuous wall-clock approximation; host tests and exported metadata retain the project's original transition and terminal-frame contract. A browser animation is not proof of exact firmware scheduler timing.

## Run checks / rebuild

From the repository root, with Python 3.9 or newer and no added packages:

```sh
python3 -m unittest discover -s hardware/tests -p test_matrix_model.py -v
python3 hardware/simulation/build_viewer.py
```

Tests cover every single physical pixel, checkerboard/all-on patterns, five-phase partitioning, CSV address consistency, wrong-polarity wiring, row swaps, aliased pair cathodes, unused outputs, startup/reset, SDB timing, conservative current setting, authorised power limits, the firmware's dim fallback, BC1.2 completion/error qualification and LED shutdown. They cannot validate an incorrectly identified physical bottom-view pin-1 corner.
