# Main PCB physical and 3D review

29 October 2026. This is a provisional physical review while copper routing continues. The rendered source snapshot is recorded in `main-review-render-source.json`; final routing must receive a fresh native DRC and render.

## Pin geometry and orientation

Native KiCad inspection confirms the software design has all **84 LED lead positions** at the nominal 2.54 row pitch, 7.62 strip spacing and 12.70 module pitch, with 0.9 drills and 1.4 pads. This checks the CAD geometry, not the actual modules; the breadboard evidence supports 2.54 lead pitch only. Every module's front pin 1 is the upper-left square pad. Viewed from the rear, that same pad appears upper-right. Each front footprint also has a small pin-1 silk mark visible before fitting the display. The complete bare-front image shows the square pads and all seven marks.

All **277 connected pin assignments** match the current circuit specification. This includes the replacement vertical main J1 and its unchanged logical six-wire pin order. These checks do not establish copper connectivity while the board is being routed.

The main board is 88.4 × 17.3 × 1.6, within the nominal LED envelope x=-0.25..88.65 and y=-0.25..17.55. The nominal inset is 0.25 per edge. The owner's complete set of seven modules must still fit the 1:1 template simultaneously; the earlier approximately 90 mm caliper body reading is not a proof of the full pin lattice. The physical low-current pin 1 / pin 12 upper-left-dot check remains necessary.

## Models and standoff

All **43 physical component models** exist; the six remaining references are copper test pads and need no solid model. The original LED model's VRML Cylinder primitives disappeared in KiCad's native render. `build_pcbs.py:model_wrl()` now makes explicitly triangulated round dots and leads. Native rendering then shows all **245 dots** and the lead rows correctly.

The LED body occupies z=3.0..9.3 above the front PCB surface: **3.0 standoff + 6.3 body thickness**. The lead model spans z=-2.6..3.0, representing 1.0 of trimmed lead below the 1.6 PCB. The edge view visibly confirms the gap, body thickness, rear components and lead ends. This is a nominal mechanical envelope, not a detailed manufacturer solid or a model of solder fillets.

The rear view shows access to all 84 lead ends after factory SMT assembly. The MCU's facing copper lands are relatively close to the middle LED pads; use a fine iron tip and controlled solder amounts during the prototype rather than assuming a large soldering tip fits every joint. The model does not simulate solder spread or tool access.

## Main harness connector correction

The horizontal main JST was rejected after checking the mating plug, not just the bare header. Its mated envelope x=65.025..71.275 covered the adjacent x=65.79 LED lead row. The final main connector is **BM06B-SRSS-TB(LF)(SN), C160392**, with stock KiCad vertical footprint at **(69.0,12.2), source angle 270, B.Cu**. The carrier keeps its horizontal header.

The vertical header's body envelope is x=67.1..70.0 and y=8.2..16.2. Its copper envelope is x=66.9..71.1, giving at least 0.41 horizontal clearance to the adjacent LED pad edges. The plain SHR-06V-S mated housing reaches approximately 6.3 above the main rear surface, ending at assembly z=17.2 and leaving 5.6 to the prototype case back. Its body is left of the carrier and 0.675 from the carrier's mated plug envelope. Carrier wire exits y=2.5..7.5 pass above the main header's y=8.2 body edge; the main wires bend toward the free length on the left. Confirm that bend with the actual cable gauge and housing.

Source angle 90 at the same centre was reviewed and rejected: it moves the body right to x=68.0..70.9, overlapping the carrier's mating plug. Angle 270 is mechanically significant, so changing it merely to simplify data routing requires another physical review. Use **SHR-06V-S without the wider -B protrusions** for both harness ends.

## Repeating the views

`python3 hardware/tools/render_main_review.py` writes `main-review-top.png`, `main-review-bottom.png`, `main-review-bare-front.png` and `main-review-edge.png` under `hardware/render`. It uses a temporary snapshot and never saves the source PCB. The bare-front copy removes only LED model nodes, retaining all pads, footprints, silkscreen and copper. After routing, `--prefix main` produces the corresponding final filenames. A camera zoom of 2.4 frames the complete long board at the default 1800 × 600 requested size.

The rendered front/rear/edge views were inspected after the model and connector corrections. They show all seven modules aligned, the main PCB behind the LED silhouette, the vertical main header and rear programming controls. The mated harness and printed enclosure are represented separately in `assembly-stack.svg` and are not present in these standalone PCB renders.
