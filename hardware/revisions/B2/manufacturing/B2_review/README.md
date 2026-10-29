# House Rules B2 — MANUFACTURING REVIEW, NOT PRODUCTION APPROVAL

This package passed a fresh native KiCad10 DRC including warnings, exclusions,
unconnected items and schematic parity, after refilling/saving a staged copy.
The five ignored checks that KiCad10.0.7 uses by default are reported
explicitly; their pristine native evidence is included in reports/. UUID
exclusions, custom-rule ignores and other ignored-rule overrides are forbidden.
Its native audit checks82 references,55 factory parts,327 connected pins and the
unchanged84 LED holes against frozen A1. Separate owner-reported diode tests
verify the full12-terminal map and front orientation of ONE owned
LMD07057AUE-101B-02: part-number label on the left in the correct front view.
The other20 modules remain unverified. This does not establish powered-board
operation, actual soldered fit, USB current/compliance, brightness, thermal
performance or print fit. The owner evidence is included in reports/.
No upload, order or payment has been made by the exporter.

Board requirements: SIX copper layers,88.4 x17.3mm final outline,1.6mm FR4.
Layer order is F.Cu/In1.Cu/In2.Cu/In3.Cu/In4.Cu/B.Cu. In4 is GND-only. In2 is
primarily GND with one explicitly approved quiet CT_5V timing-capacitor bridge,
maximum12mm total; no other signal is allowed there. Its GND fill must remain
one connected outline. The final measured length is recorded in the audit.
In3 has signal copper including USB and GND fill; USB retains its unbroken
In4 ground reference. Confirm the actual standard dielectric
stack with the manufacturer. No controlled-impedance certification is claimed.

ALL0.30mm ordinary F-to-B plated through VIAS must be epoxy/resin FILLED and
COPPER CAPPED flat, including12 exposed-pad thermal vias (three per TLC driver)
and the selective0.45mm-pad escape vias. Most via pads are0.60mm; selected escape
pads are0.45mm, minimum annulus0.075mm. Tenting or solder plugging alone is not
equivalent to this fill/cap requirement. No blind/buried/laser vias are specified.

Actual Excellon PTH T1 =0.30mm VIA holes: FILL AND CAP ALL.
Actual Excellon PTH T2 =0.90mm LED mounting holes, exactly84: KEEP OPEN,
UNFILLED AND UNCAPPED. Never apply a blanket fill instruction to all PTH holes.
The actual drill counts and source/output hashes are in manifest.json and
reports/drill-statistics.json. There must be no other finished-board hole tools.
Both native geometry and actual Excellon holes are independently checked for
at least0.45mm via-to-LED-PTH hole-edge clearance and0.25mm via-to-via clearance,
including same-net pairs. These physical checks do not depend on copper DRC.

Narrow-board assembly may need REMOVABLE OUTSIDE RAILS and tooling chosen by the
assembler. Tooling/fiducial holes must be OUTSIDE the finished88.4x17.3mm outline,
on removable rails only. Do not add holes inside the main board or move/close the
84 LED holes. Rails must depanelise completely so the final PCB stays hidden
behind the LEDs. CAM must confirm fill/cap selection, open LED holes and final
outline tolerance before an order is approved.

Factory assembly:55 SMT components on BOTTOM ONLY. DS1..DS7 andJ1..J20 are
owner-fit modules/wire lands, excluded from every factory BOM/CPL. Their copper
and LED holes remain in Gerbers. Do not solder-fill the84 empty LED holes.
The owner supplies the XIAO RP2040 Plus and Adafruit4090 separately and wires
20 leads/40 wire-end joints; these stock modules/looms are not factory BOM parts.

ROTATION REVIEW IS REQUIRED. bom.csv uses common JLC-shaped headings; bom-review
adds exact quantities/identities. cpl-manufacturer-review.csv preserves KiCad's
native millimetre position export, same auxiliary origin as Gerbers/drill.
BOTTOM X IS NOT NEGATED. Native exported Y can be negative. No extra mirroring,
Y inversion or package-specific angle correction has been applied. Native angles
are NOT a guarantee of the manufacturer's tape/feeder/pin1 convention.
placement-review.csv adds native pad1 coordinates relative to the auxiliary
origin, using native board XY (distinct from exported CPL Y), BOTTOM side,
exact MPN/LCSC, native angle and uncorrected CPL rotation. Review
all asymmetric components in the assembler's placement preview, especially QFNs,
PMOS switches, load switches, ESD/BC chips and diode polarity. Obtain the factory's
concrete placement/process review before production. No silent substitutions.

fabrication/ contains six actual Gerber X2 copper layers, both masks/silks, outline,
metric Excellon PTH/NPTH, drill map and Gerber job metadata. Its ZIP contains
fabrication files only. assembly/ adds paste Gerbers and factory CSVs. reports/
contains native DRC, exact board audit and actual drill statistics. source/ retains
the exact refilled/saved board used for these outputs plus project/schematic/rules
and local footprint libraries. source/3d/ includes the bundled model assets.
Every model referenced by the actual staged PCB must resolve through
${KIPRJMOD}/3d/ inside this snapshot; installed/global model fallbacks, absolute
paths and escaping relative paths are rejected. reports/3d-model-portability.json
records each reference/hash and explicitly lists footprints lacking a 3D model.
Absent models are not a claim of absent physical components. The repository
also retains generators, mechanical design, firmware and earlier source history.
The source canonical PCB was not modified. manifest.json links all inputs and
outputs to SHA256 hashes; a later change requires a fresh audit/export/quote.
