# Printed pin-fit test plate

This is a **test tool**, not a manufacturing board or a fit guarantee. The complete array has not yet been physically fitted.

Print `pin-fit-plate.stl` flat at **100% scale**. Its outline is **88.4 × 17.3**, thickness **1.0**, with all **84 hole centres** matching the PCB design. The default STL holes are **1.0 nominal diameter**, whereas the real PCB specification is **0.9 finished diameter**. Printed holes can come out smaller or uneven and do not establish PCB hole tolerances. The editable `pin-fit-plate.scad` has `print_hole_diameter` for a second test if the printer needs compensation.

Print the separate `pin-fit-scale-50mm.stl` coupon at the same slicer settings. It is **50.00 × 10.00 × 1.00**. Measure its length and width with calipers, and check the pin plate's 88.4 × 17.3 outline. Correct accidental slicer scaling before judging the LED fit.

Gently insert **all seven modules at the same time**, oriented consistently and with their long edges touching as intended. Their pins should enter without forcing the bodies sideways or bending pins to compensate for an incorrect repeat. Record whether the bodies can touch while every lead remains straight. A fit in the looser printed holes is useful evidence about module repeat and body interference; it does not prove the tighter 0.9 PCB holes. A tight print may reflect the printer rather than the LEDs.

The breadboard observation supports 2.54 lead pitch only. The board's 12.70 module repeat and 7.62 strip spacing follow the manufacturer's nominal drawing and still need this complete array check. The earlier approximate 12.9-per-body /90-total caliper readings make the check necessary before ordering.

The pin pattern is symmetric under a 180-degree rotation. This jig cannot establish electrical pin 1, LED polarity or row/column orientation. Use `pin-fit-template.svg` and the low-current physical pixel test for those checks. Do not connect power through the plastic tool.

The STL was generated directly as a triangulated solid, with closed-manifold checks and all 84 centres audited against the native PCB. No OpenSCAD executable is needed to print the supplied file. The source generator is `hardware/tools/build_pin_fit_plate.py`; its mesh report is `hardware/reports/pin-fit-plate-verification.json`. Generation and topology checks are not evidence of a physical fit.
