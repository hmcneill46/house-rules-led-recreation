# Independent hardware and manufacturing review

Reviewed 29 October 2026 against the saved native KiCad boards and `circuit-spec.json`. The initial review was read-only; later explicitly authorised connection and tail-cleanup work is recorded separately. The final audit below did not modify frozen design files. No design was uploaded and no order was placed.

**Conclusion:** the present six-layer main / four-layer carrier arrangement is coherent for a controlled prototype. The native board inventory matches the circuit specification, including values, exact MPN/LCSC codes, pad nets, mounting sides and centres. Manufacturing process choices, assembler rotation review and the owned LED fit/polarity tests remain pre-order requirements; this report does not approve production.

## Actionable findings

### P1 — native via classification: corrected before this review closed

An intermediate main board contained 114 vias marked as blind/buried despite spanning F.Cu–B.Cu. That would imply the wrong fabrication interpretation even though the intended geometry is an ordinary plated through via. The root design pass normalised the via flags. The final independent native API check found **192 main vias, all `VIATYPE_THROUGH`, F.Cu–B.Cu and explicitly filled/capped**, and **10 carrier vias, all through**. No blind, buried, laser-drilled or HDI process is intended.

The manufacturing exporter refuses any non-through or non-F/B via rather than silently changing it. Run final DRC after any further routing/via edits, then export the exact reviewed board revision.

### P2 — specify the main thermal via process explicitly

All 192 main vias, including QFN signal lands and driver/MCU exposed-pad regions, are explicitly marked filled and copper capped in the final native file. Select **resin-filled and copper-capped via-in-pad processing**, also called VIPPO/POFV, with a flat solderable surface. Tenting an ordinary open via is not equivalent inside an exposed pad; solder can wick into it during reflow. Ensure CAM fills the intended vias and leaves the owner's LED mounting holes open.

JLC currently lists this via-in-pad process as standard/free on six or more layers. Confirm that selection in the real quote rather than assuming it from a local soldermask setting. [JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering), [JLC via-in-pad guide](https://jlcpcb.com/help/article/via-in-pad-pofv-guide).

### P2 — lock suitable copper/stack choices at quotation

Use the vendor's standard **six-layer 1.6 mm FR-4** stack for the main and **four-layer 1.0 mm FR-4** stack for the carrier, with **1 oz outer copper**. Confirm the actual inner copper and dielectric thicknesses. The KiCad boards identify layer count and total thickness but do not contain a validated dielectric/impedance stack.

The final main routing has a 0.10 mm minimum track and 0.15 mm minimum +5V/VBUS track, so ordering heavier 2 oz copper against the same geometry is inappropriate without redesign. The 0.4 mm via pad / 0.2 mm drill geometry is within published multilayer capability; JLC notes that 0.2 mm drill vias with pad diameter below 0.45 mm can incur a fee. Do not enlarge the tightly routed pads blindly to avoid it. Prefer a flat finish suitable for the QFNs, such as ENIG, subject to the assembler's recommendation and quote. [JLC fabrication capabilities](https://jlcpcb.com/capabilities/pcb-).

### P2 — fine silkscreen needs diagram support

Several legends are only 0.6–0.8 mm high with 0.10–0.12 mm strokes. This is below JLC's published 1 mm text / 0.15 mm stroke readability guidance. Do not rely on these small labels being readable on the delivered boards. Supply the assembly/programming diagram showing BOOT, RESET, SWD, USB harness pin1 and LED pin1; enlarge essential legends if clearance permits. [JLC legend capability](https://jlcpcb.com/capabilities/pcb-).

### P2 — assembler handling and any added tooling must preserve the final board

The long main strip and small carrier need an assembler-approved rail/panel/support plan. JLC's quote page describes automatic tooling holes near corners; the main's LED mounting pads are near its corners, so finished-board tooling changes require a specific clearance review. Prefer tooling on removable rails where practical. Do not permit unreviewed holes, mouse-bite tabs or dimensions that compromise the LED silhouette or case fit. Confirm the final depanelised dimensions and tolerances. [JLC quote/tooling notes](https://cart.jlcpcb.com/quote/?fromDemo=yes), [JLC board dimensions](https://jlcpcb.com/help/article/pcb-dimensions).

### P2 — factory placement rotations require a manufacturer preview

Main SMT components are on the **bottom**; carrier SMT components are on the **top**. A native KiCad rotation is not proof of a particular assembler's feeder/pin1 interpretation. Review all QFN, regulator, ESD, TVS, USB and JST orientations against pin1/cathode/mechanical drawings in the actual placement preview. The exporter preserves KiCad coordinates and rotations and does not add guessed JLC offsets or mirror bottom X.

The main connector has since changed to vertical JST BM06B-SRSS-TB(LF)(SN), C160392, after physical review found the original horizontal mate collided with LED leads. Final native DRC/parity and inventory checks passed after that connector/routing change. The six-wire harness is a separate purchased/assembled item and must use plain SHR-06V-S mating housings at both ends, matching the reviewed envelope; the wider SHR-06V-S-B is excluded. Verify pin1-to-pin1 continuity; a visually matching premade harness can reverse wiring. Keep the USB data pair together and confirm connector/cable bend clearance in the printed case.

## Final snapshot inspected

| Property | Main | USB carrier |
| --- | --- | --- |
| Outline centreline | 88.4 × 17.3 mm | 16.0 × 16.8 mm |
| Copper layers / total thickness | 6 / 1.6 mm | 4 / 1.0 mm |
| Footprints | 50 | 7 |
| Factory component placements | 37, bottom | 7, top |
| Owner/PCB-only exclusions | DS1–DS7; TP1–TP6 | None |
| Exact factory MPN/LCSC fields | Present; match specification | Present; match specification |
| Plane arrangement | In1 GND; In4 +5 V | In1 GND |
| Current via classification | 192 ordinary F–B through vias, filled/capped Type VII | 10 ordinary F–B through vias |

The dedicated main planes avoid long narrow supply and ground routes across the strip. The main USB data paths run predominantly on F.Cu over In1 GND, with native track centreline totals of 39.8134 mm F.Cu + 2.6032 mm B.Cu for USB_DM and 38.8562 mm F.Cu + 2.1411 mm B.Cu for USB_DP. These include pad escape branches and exclude the internal harness. This is preferable to routing the whole link across an unspecified power-reference layer. Carrier totals are USB_DM 10.4221 mm F.Cu + 4.1692 mm B.Cu and USB_DP 11.8530 mm F.Cu. These are routed copper totals, not verified channel delays. Neither the board traces nor the unshielded internal harness constitute a verified 90-ohm controlled-impedance channel; real USB enumeration/data/suspend tests remain required.

The 47k/47k CC sensing network, separate 5.1k Rd resistors, 47k LED ISET values, 5 V-only supply, 3.3 V MCU rail and same-port ROM DFU arrangement agree with the power review. See [firmware-power-review.md](/Users/harrymcneill/Projects/house-rules-led-recreation/hardware/reports/firmware-power-review.md) for current calculations and USB startup fixes.

## Export tooling prepared

`hardware/tools/export_manufacturing.py` was prepared and its Python syntax/read-only native inventory checks were exercised by this review. Fabrication package execution is recorded separately in its output manifest. It:

- Cross-checks the actual board/spec inventory, physical outline and centres, values, MPN/LCSC and connected pad nets.
- Requires the intended six-/four-layer thicknesses and ordinary through vias, then runs native DRC/parity with an in-memory zone refill, without saving the PCB.
- Stops on DRC/parity/unconnected errors and on missing factory component identities.
- Exports Gerber X2 copper/mask/silk/outline, separate PTH/NPTH Excellon files and maps, paste layers, exact BOM and native/generic CPL for both boards.
- Excludes owner-fit DS modules and component-free TP pads from the factory BOM/CPL while retaining their physical copper/holes in fabrication files.
- Uses the same saved auxiliary origin for fabrication, drilling and placement. Bottom X is not negated. Package-specific angle corrections are left to assembler review.
- Builds a new review-only output directory, refuses overwrite, records input/output hashes and aborts if design sources change during export.

Some vendors require different BOM/CPL headings, layer names, panel format or angle conventions. The common JLC-shaped CPL is a review candidate, not an approval of its orientation interpretation. The package README includes process selections and explicit pre-order/user-review holds. No cart stock, shipment price or live assembly quotation has been reserved.


## Later local QFN routing allowance and native rule validation

A later routing pass added eight locked inner-land 0.4/0.2 mm through vias. The main board's absolute clearance floor is now 0.10 mm, while Default and Power netclasses remain 0.15 mm. The only lower-clearance custom condition is VIA-to-PAD pairs whose objects intersect the same U1-U4 QFN courtyard. Via-to-via, via-to-track, pad-to-pad, drill and 0.10 mm annular-ring constraints were retained. This matches the scoped fabrication decision, not a global 0.10 mm routing policy. [JLC 1 oz multilayer fabrication capabilities](https://jlcpcb.com/capabilities/Capabilities).

Native positive DRC after the inner-land batch reported zero clearance errors. An isolated copy retaining the same global/default settings but removing the local exception reported exactly eight 0.15 mm clearance violations at the new nominal 0.10 mm via-pad gaps. This negative control proves that the local exception is required and active, with the ordinary 0.15 mm rule retained elsewhere. Both snapshots had 17 unfinished connections and 64 dangling warnings before the next routing pass, so they are routing-stage evidence rather than final release reports.

The original unitless `(min 0.15)` in the power-width rule silently prevented custom rules from loading in the installed CLI. It has been corrected to explicit `(min 0.15mm)` in the main rule file and project generator. The generator now reproduces the scoped rule/floor and was exercised only in an isolated temporary directory; saved board geometry was not regenerated. `main-innerland-rule-verification.json` records the positive/negative counts. [KiCad 10 custom rule syntax](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#_custom_design_rules).


## Final protective addition

The main now contains R14, the same 2.2 kohm/C4190 part already used for I2C pull-ups, between the BOOT button and PA14/SWCLK. Its verified placement is B.Cu at (14.3,0.9) mm from the auxiliary origin. The initially considered (15.9,0.9) position was rejected for switch courtyard/pad overlap. This changes the main count to **50 footprints / 37 factory components**. The source, native fields and regenerated schematic agree; both boards' ERC passed and main/USB netlists verified 279/40 connected pins. The final native DRC after this addition and guarded removal/trim of unused route tails reports zero violations, zero unconnected items and zero schematic parity issues. All component-pad connectivity was preserved during cleanup.

## Frozen final verification

The final main source SHA256 is `8b9df50fe0897db76a186902024ef12a80ff8da990d0e1d2d342f8fa2f86a830`; the carrier is `fb01d3a1369278d2435762de07fb7607957e51fce6277dc55044a102059ed40f`. Both final native all-severity DRC/parity checks pass with zero warnings or errors. The final main contains 2539 track segments, 192 filled/capped ordinary through vias, and 84 open 0.9 mm LED PTH holes. A fresh isolated negative control, retaining valid rule units and local libraries but omitting only the QFN via-pad exception, produces exactly nine nominal 0.10 mm clearance errors against the ordinary 0.15 mm rule; no other violations occur. Hash checks prove the control did not alter actual design sources. The carrier's corrected explicit-unit power rule also passes native DRC.

See [final-electrical-verification.md](/Users/harrymcneill/Projects/house-rules-led-recreation/hardware/reports/final-electrical-verification.md) and its JSON evidence for measured USB lengths, R14 net details, native counts and hashes. These file checks do not replace LED footprint/pinout testing, assembly-preview approval, case/harness fit or prototype power/USB measurements.
