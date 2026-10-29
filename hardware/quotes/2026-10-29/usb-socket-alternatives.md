# USB4105 socket alternatives — engineering review

29 October 2026. Quote-stage engineering review of the frozen 16.0 × 16.8 mm, 1.0 mm USB carrier. No BOM, PCB, Gerber, placement or manufacturing ZIP was modified for this review.

**USB4105-GF-A-120 / C5184243 is mechanically and electrically suitable for quotation on the existing PCB and case.** Its longer shell stakes clear the current enclosure and main board. Factory acceptance of the shell-anchor soldering process remains necessary. **USB4105-GF-A-060 / C3025063 is not approved as an automatic substitute** on this 1.0 mm board.

## Manufacturer evidence

GCT’s USB4105 drawing B3 (24 February 2023), sheet 1, gives one family PCB layout and pin map. The suffix controls shell stake length S: blank 0.95 mm, -060 0.60 mm, -120 1.20 mm, each ±0.15 mm. GF means gold-flash contacts; A means tape and reel. These suffixes do not change body size, locating pegs, contact tails, mounting-hole XY positions or mating-face location. The shared body envelope is 8.94 × 7.35 × 3.31 mm. [GCT-authored family drawing, hosted by Mouser](https://www.mouser.com/catalog/specsheets/Global_Connector_Technology_usb4105.pdf).

The manufacturer specification rates the family above the project’s 5 V requirements and describes lead-free reflow. This substitution does not introduce USB PD or alter the existing CC, VBUS, ground or USB2 wiring. [GCT USB4105 specification](https://gct.co/files/specs/usb4105-spec.pdf).

The direct GCT drawing/product endpoints returned access errors during this review; the GCT-authored distributor-hosted drawing above supplied the ordering and dimension evidence. A text extraction was checked; no redistributed manufacturer drawing is included in this report.

## Stake engagement in this carrier

The following is a project calculation, using S minus board thickness and a conservative assumed ±10% PCB thickness range (0.90–1.10 mm). Confirm the actual board tolerance in the supplier’s final order/DFM review. A negative projection means the stake ends within its plated hole.

| Exact MPN | JLC/LCSC code | S, mm | Nominal underside projection, mm | Tolerance range, mm | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| USB4105-GF-A | C3020560 | 0.95 ±0.15 | −0.05 | −0.30 to +0.20 | Original geometry; unavailable in the live assembly inventory reported to the project |
| USB4105-GF-A-120 | C5184243 | 1.20 ±0.15 | +0.20 | −0.05 to +0.45 | Suitable for unchanged-board quotation, with anchor soldering DFM review |
| USB4105-GF-A-060 | C3025063 | 0.60 ±0.15 | −0.40 | −0.65 to −0.15 | Reject as the default 1.0 mm-board substitute |

The -120 part improves anchor engagement by 0.25 mm versus the original, but it does not guarantee visible stake protrusion at every tolerance extreme. The assembly instruction must explicitly include **all four plated shell anchors**, not only the fine-pitch SMT contacts. The factory should accept the resulting anchor wetting/barrel fill, using its supported paste-in-hole or secondary soldering process. The connector’s USB insertion forces must reach the PCB through sound shell joints and then the printed cradle. Fine-pitch contact joints alone are not the mechanical attachment.

## Physical clearance checked against the current design

The retained KiCad family footprint has shell-anchor centres at local J1 offsets (±4.32, −3.105) and (±4.32, +1.075). With J1 at carrier (10.7, 13.7) and the carrier at main (72.15, 0.25), their main-coordinate centres are x=78.53/87.17 and y=10.845/15.025. The existing oval plated slots are 0.6 ×1.7 and 0.6 ×1.4 mm, matching the manufacturer family layout. The selected family has the same 16 contact mapping; abbreviated distributor “pin count” attributes do not override that drawing.

From `mechanical/enclosure.scad`, the main rear is z=10.90 mm, carrier underside z=14.40 mm and top z=15.40 mm. A worst-case 0.45 mm stake projection ends at z=13.95 mm, leaving 3.05 mm to the bare main rear. The model’s specified 1.0 mm trimmed LED leads end at z=11.90 mm, so even the anchor near a DS7 lead has 2.05 mm nominal geometric separation before any additional solder-envelope allowance. Actual clipped lead length and solder fillets still need inspection during assembly.

The top carrier tabs occupy y≤1.0 mm at x=74.5/86.6, the lower-left support occupies x=70.8–73.0 and y=14–16, and the right fence starts x=88.6. These features are outside the four stake regions. The tall main JST body lies left of the carrier, ending x=70.0. No larger housing or moved mating face is introduced by -120. The current case is 24.0 mm deep: socket rear z=18.71, inside back z=22.80, leaving 4.09 mm above the unchanged USB body. The 3D preview may continue to show the standard 0.95 mm stake; its body and mating geometry remain representative, while this tolerance calculation covers the longer -120 stakes.

This is a footprint and envelope review; factory solder-joint DFM and a physical cable/retention check remain separate. No carrier or enclosure geometry change is required for the -120 substitution.

## Supplier and inventory evidence

- [JLCPCB USB4105-GF-A-120 / C5184243](https://jlcpcb.com/partdetail/GCT-USB4105_GF_A120/C5184243) identifies the exact candidate and supports assembly. The quotation agent separately observed **2,090 in live assembly stock** on 29 October 2026; this report did not independently control or change that cart. Recheck/reserve inventory when proceeding to an actual order.
- [JLCPCB USB4105-GF-A-060 / C3025063](https://jlcpcb.com/partdetail/GCT-USB4105_GF_A060/C3025063) identifies the short-stake option; its stock does not cure the engagement concern above.
- LCSC reseller/search stock was not treated as JLCPCB assembly stock. Availability is time-sensitive and a quote does not reserve components.

The GF/15 contact-plating variants belong to the same family ordering grid, but no alternate exact JLC code and live assembly availability were established for a 15 µin version. There is no reason to broaden the substitution now that the -120 variant is a suitable candidate.

## Documentation correction made during this review

The enclosure SCAD and notes already specified 24.0 mm depth and 4.09 mm USB-to-back clearance, but `mechanical/assembly-stack.svg` still depicted the previous 21.0 mm case and 1.09 mm clearance. The SVG side elevation was extended coherently at its retained 28 pixels/mm scale, with its rear wall and depth dimensions moved, 24.0/4.09 labels corrected, and the port well drawn as a 6.5 mm z-span with the current closed roof. The side elevation was shifted left to retain space for its legend. The stale “rear edge open” and “no final enclosure STL” captions were also updated. The corrected SVG was rendered to `hardware/render/assembly-stack.png` and visually checked. No SCAD, STL or mechanical geometry was changed.
