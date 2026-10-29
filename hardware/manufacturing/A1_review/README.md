# Review-only manufacturing export — HOUSE RULES A1

These files were generated locally from the saved KiCad boards. No design was
uploaded and no order was placed. This package is an engineering prototype for
review; generating it does not authorise production or establish hardware tests.

Before buying/uploading: complete the owned LED pin/orientation and mechanical fit
tests, review current native DRC/ERC/parity reports, confirm the case and USB
harness, inspect Gerbers/drill in an independent viewer, and review the assembler's
component matches, pin-1 orientation, feeder rotations, stock and final quote.
The user must review the concrete final package/quote before an order is placed.
The internal cable must use plain JST SHR-06V-S mating housings at both ends;
the wider SHR-06V-S-B version is outside the reviewed mechanical envelope.

## Board and process choices to confirm with the fabricator

- Main: six copper layers, 88.4 x 17.3 mm nominal, 1.6 mm FR-4. In1.Cu is GND;
  In4.Cu is +5 V. F.Cu, In2.Cu, In3.Cu and B.Cu carry signal/fanout copper.
- USB carrier: four copper layers, 16.0 x 16.8 mm nominal, 1.0 mm FR-4. In1.Cu is GND.
- Use the fabricator's standard stack at these thicknesses, and 1 oz outer copper;
  confirm the inner-copper weight and actual dielectric stack. No controlled
  impedance has been specified or verified. Do not order 2 oz copper against the
  present fine-track layout.
- Main exposed-pad thermal vias require resin-filled, copper-capped via-in-pad
  processing (VIPPO/POFV), with a flat solderable surface; tenting alone is not
  equivalent inside an exposed pad. The same filled/capped treatment is needed for
  QFN signal-land vias and any other SMD-pad vias. Specify the main board's 0.2 mm drill
  vias for filling/capping, and have CAM confirm that all owned LED mounting holes
  remain open. JLC currently lists this via-in-pad
  process as standard/free for six or more layers; confirm it on the actual quote.
- All intended vias are ordinary F.Cu-B.Cu plated through vias. No blind, buried,
  laser or HDI vias are requested. Minimum via geometry is 0.4 mm pad / 0.2 mm drill.
  JLC notes that 0.2 mm drills below a 0.45 mm via pad may incur an extra fee.
  The tightly routed board must not be enlarged blindly to avoid that fee.
- Factory assembly must solder the USB socket's through-hole metal shell anchors as
  well as its SMT electrical contacts. The shell anchor holes remain open and are
  excluded from via-filling instructions, as are every owned LED mounting hole.
- Prefer a flat surface finish suitable for the 0.4 mm-pitch QFNs (e.g. ENIG), subject
  to the assembler's recommendation and quote. Fine silkscreen is below JLC's
  published 1 mm/0.15 mm readability guidance; use the assembly/programming diagram
  for BOOT, RESET, SWD and polarity identification.
- These narrow boards may require assembly rails/panel tooling chosen by the
  assembler. Do not change the final depanelised board outline or enlarge it beyond
  the LED silhouette. Confirm depanelisation tolerances and support before approval.
  Do not permit automatic tooling holes inside either finished board without a
  clearance review; the main LED mounting pads are close to its corners. Prefer
  tooling on removable rails where practical.

Sources checked 29 October 2026:
[JLC capabilities](https://jlcpcb.com/capabilities/pcb-),
[JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering),
[JLC via-in-pad process](https://jlcpcb.com/help/article/via-in-pad-pofv-guide),
[JLC board dimensions](https://jlcpcb.com/help/article/pcb-dimensions).
Public availability and pricing can change; no stock is reserved.

## Files and coordinate conventions

Each board has a fabrication folder containing Gerber X2 copper, soldermask,
silkscreen, outline, separate PTH/NPTH Excellon drill files and a drill map.
Native DRC and drill reports are in the board's reports folder.
The fabrication ZIP contains those files only. Paste Gerbers and factory BOM/CPL
are in the assembly folder. Gerber and drill exports use the same saved auxiliary
origin. No mirroring or Y inversion is added by this Python tool.

BOM columns are MPN, LCSC, Qty, Designators, Value, Package. Values and component
identities come from the actual PCB, cross-checked against circuit-spec.json.
DS1-DS7 and all TP pads are excluded from factory BOM/CPL; their mounting holes and
copper remain in fabrication Gerbers. Excluded parts/pads are listed separately.

positions-native-factory.csv preserves KiCad's own millimetre position/rotation
convention and top/bottom side labels. Both sides share the unmirrored placement
coordinate system, with the saved auxiliary origin and KiCad's exported Y axis.
The auxiliary origin is near the board's upper-left corner, so negative exported
Y coordinates are expected. Bottom X is NOT negated. The generic CPL candidate
uses the same values; no package-specific rotation corrections are applied.
placement-review.csv adds the native PCB centre/angle and exact component identity
for visual comparison. In particular, the main-board SMT parts are on BOTTOM and
the carrier SMT parts are on TOP. KiCad angles are not a guarantee of JLC or another
assembler's feeder orientation. Inspect every asymmetric part and pin-1 marker in
the manufacturer's placement preview, and obtain its approval before production.

The CPL has common JLC-shaped headings, but another vendor may require its own BOM,
CPL, layer naming, panel or rotation format. Do not silently transform bottom
coordinates/angles or accept automatic part substitutions. The manifest records
input and output hashes and DRC result counts so the exact package can be reviewed.
