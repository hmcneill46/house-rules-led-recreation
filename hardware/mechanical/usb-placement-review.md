# USB carrier placement and mating-space check

29 October 2026. Adopt the coordinates in `usb-placement-proposal.json` if consistent with the final electrical specification. This proposal leaves copper routing to the main PCB author.

## Recommended placement

Carrier remains **16.0 x 16.8 mm**, one assembly side. Relative to the main PCB, place its origin at **(72.15,0.25)**. Both board outlines remain within the LED silhouette.

| Part | x | y | Rotation | Comment |
| --- | ---: | ---: | ---: | --- |
| USB J1 | 10.7 | 13.7 | 0 | Socket toward the bottom; shifted right to clear the JST courtyard |
| Harness J2 | 3.1 | 5.0 | 270 | True left entry on F.Cu |
| Rd R1 | 1.4 | 12.0 | 90 | Left flank |
| Rd R2 | 4.5 | 12.0 | 90 | Left flank |
| Input C1 | 14.6 | 2.0 | 90 | Change to 0402, 100 nF, at least 25 V X7R |
| ESD U1 | 8.0 | 7.6 | 270 | Preserve the final electrical pin assignments |
| VBUS TVS D1 | 14.6 | 6.3 | 90 | Right flank |

This arrangement was built as a fresh scratch KiCad PCB with the actual stock footprints and the previously documented USB ground-pad corner rounding. Native KiCad DRC found **zero placement violations**, using 0.15 mm copper clearance, 0.25 mm copper-to-edge clearance and 0.2 mm hole clearance. Stock component courtyards were not edited. The 34 unconnected items are expected because the scratch trial contains no tracks.

Scratch PCB and complete DRC output are referenced in the JSON. The completed carrier must be routed and checked again; this trial is not a fabrication file.

## Why the former orientation was unsuitable

The JST manufacturer's SH assembly drawing gives a **6.25 mm mated depth**, approximately 2 mm beyond the 4.25 mm header body. The earlier top-entry-facing arrangement at (8,3.1), rotation 180 degrees, left too little room for the mating plug and cable bend before the top case wall.

Rotation 270 degrees on F.Cu points the side-entry connector left. The mated harness now exits into the long open space behind the main PCB, rather than into the short top wall. The approximate global wire exit is x=70.675, with ample horizontal space to the left for a gentle loop. Rotation 90 degrees would point right on this assembly side.

A 30-50 mm factory-crimped cable can be folded into the reserved internal channel. Verify the actual housing and wire diameter before finishing the case; do not crush the conductors or rely on a sharp right-angle fold.

## USB face position

The USB stock footprint marks the PCB edge at local y=+3.1, but its body/mating face is at y=+3.675. With the chosen centre y=13.7 and carrier offset y=0.25, the mating face is therefore **global y=17.625**. The daughterboard bottom edge is **y=17.05**. These are different surfaces.

The socket centre is global x=82.85, farther right than the initial concept. A normal thick enclosure wall would recess it. Provide a relieved port well and sufficient space for the cable overmould rather than moving the PCB beyond the LED outline.

References: [JST SH manufacturer drawing](https://www.jst.com/wp-content/uploads/2021/01/eSH.pdf), page 1 assembly profile; installed KiCad 10 stock JST SH and USB4105 footprints. Mating direction was checked with actual `pcbnew` footprint transforms.
