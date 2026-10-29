# Temporary soldering alignment tray

`alignment-tray.stl` is a printable temporary jig for seven LED modules placed face-down together, with their pins upward. It has one open rectangular pocket and no dividers. It is not the finished enclosure or a PCB drilling template.

| Feature | Nominal dimension |
| --- | --- |
| Clear pocket | 90.6 × 18.6 mm |
| Floor | 1.2 mm |
| Walls | 1.6 mm thick |
| Wall height above floor | 3.0 mm |
| Overall | 93.8 × 21.8 × 4.2 mm |

These approximate fit dimensions allow clearance around the reported 90 × 18 mm LED group; they are not guaranteed to be snug. Check the actual seven modules and your printer's fit before use. Push the row gently against one long wall and one end wall for a common reference. Check that the LED faces are level before soldering. A thin paper liner can protect the faces if needed.

Print with the large flat floor on the bed and the pocket facing upward, at 100% scale, in millimetres. No supports are needed. The tray is intended for alignment during normal hand soldering; remove it before hot-air work or reflow.

`alignment-tray.scad` is the parametric OpenSCAD source. Change its pocket dimensions if your measured group needs a different fit, then render and export a new STL. No OpenSCAD installation was needed to generate the supplied STL.

The supplied STL is a closed, consistently oriented two-manifold mesh: 16 unique vertices, 28 triangles, no self-intersections, and a solid volume of 3532.848 mm³. The topology and signed volume were checked against the rectangular-pocket geometry.

## Pin-fit test and 3 mm standoff tools

Before ordering boards, print `pin-fit-plate.stl` and the separate `pin-fit-scale-50mm.stl` at 100% scale. The plate is 88.4 × 17.3 × 1.0 with all 84 PCB hole centres. Its **1.0 mm print holes do not prove the PCB's 0.9 mm finished-hole fit**. The separate scale coupon is 50 × 10 × 1. See [pin-fit instructions](pin-fit-plate-notes.md). Full seven-module fit is still pending; the breadboard check establishes 2.54 lead pitch only.

Print **two** copies of `led-standoff-spacer-3mm.stl`. Its working bar is 100 × 1 × 3 with a handle outside the array's left end. The supplied STL rests on its broad 3 mm side for printing; turn it on edge so the 3 mm dimension sets the assembly gap. Put the rail centres at PCB y=3.57 and 13.73. Tack two opposite pins per module, let the joints cool, withdraw both rails left, then finish the remaining joints. The front tray aligns faces and does not establish the gap by itself. Remove all temporary tools from the final unit.

The printed tools have closed, consistently oriented manifold meshes. Dimensions, all 84 centres and the spacer clearances are recorded in `hardware/reports/pin-fit-plate-verification.json` and `printed-tools-stl-roundtrip.json`. These are digital checks, not physical-fit results.

The [assembly guide](assembly-guide.svg) shows front pin numbers, exact pin-1 positions, the vertical main JST and numbered 1:1 harness. The [enclosure notes](enclosure-notes.md) describe the separate enclosure concept, USB force paths and case checks.
