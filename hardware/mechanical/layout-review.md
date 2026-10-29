# Mechanical layout review

29 October 2026. Current geometry and remaining physical checks. Units are millimetres. This supersedes the earlier small-carrier and horizontal-main-header proposals.

## Fit evidence and main PCB

The owner's caliper readings were approximately 12.9 × 18 for one module and approximately 90 × 18 for seven. The breadboard check supports **2.54 lead pitch only**. Its five-hole groups prevented a touching full-array check. The board uses the Wenrun drawing's nominal **12.70 module pitch and 7.62 strip spacing**, pending simultaneous fitting of all seven actual modules to the 1:1 template and printed pin plate. The difference between approximate body readings and nominal drawing makes that check necessary.

Main PCB: **88.4 × 17.3 × 1.6**, six copper layers. Nominal LED envelope: x=-0.25..88.65, y=-0.25..17.55. Module centres are (6.10,8.65), (18.80,8.65), (31.50,8.65), (44.20,8.65), (56.90,8.65), (69.60,8.65), (82.30,8.65).

Each module has strips at centre x ±3.81 and six rows at centre y +[-6.35,-3.81,-1.27,1.27,3.81,6.35]. PCB holes are **0.9 finished diameter** with **1.4 copper pads**, giving 0.25 nominal annular ring. A nominal 0.5 lead has approximately ±0.2 radial positional room. Do not force modules to make an incorrect body repeat fit.

`pin-fit-plate.stl` uses the same 84 centres and outline with **1.0 nominal PRINT holes** for printer clearance. Its success does not prove the tighter PCB holes or fabrication tolerances. See `pin-fit-plate-notes.md` and `pin-fit-template.svg`.

## LED pin orientation

The [Wenrun drawing](https://cdn.shopify.com/s/files/1/0695/1347/8453/files/LMD07057AUE.pdf) identifies pin 1 as upper-left in the front view. Front order is left 1,2,3,4,5,6 downward and right 12,11,10,9,8,7 downward. The rear view is mirrored: pin 1 appears upper-right. Every footprint has a square pin 1 pad and front silk mark visible before fitting.

The uploaded rear photo must be rotated 180 degrees from its readable `12 WLG` / `057A/B` text orientation to match the installed rear diagram. Use pin numbers and the low-current upper-left-dot test, not readable case text. A physical pin 1 anode / pin 12 cathode test and checks of other rows/columns remain pending.

## Current USB and harness arrangement

Carrier: **16.0 × 16.8 × 1.0**, parallel behind the main, origin **(72.15,0.25)**, underside **3.5 behind the main rear surface**. Both board outlines stay within the nominal LED silhouette.

Carrier USB4105 is at local **(10.7,13.7)**. Body 8.94 wide × 7.35 deep × 3.31 high. Its mating face is +3.675 from origin, while the recommended PCB edge is +3.1. Installed socket centre x=**82.85**, mating face y=**17.625**.

Carrier J2 is side-entry **SM06B-SRSS-TB(LF)(SN), C160405**, local(3.1,5.0), source 270/F.Cu, entry left. Conservative mated envelope: 6.25 deep × 8.0 wide × 2.95 high, ending at global x 70.675 on its wire-exit side.

Main J1 is **vertical BM06B-SRSS-TB(LF)(SN), C160392**, stock `Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical`, at **(69.0,12.2), source 270/B.Cu**. Body x 67.1..70.0, y 8.2..16.2 clears LED leads and carrier plug. Approximately 6.3 mated height reaches assembly z 17.2, leaving 5.6 rear wire-bend room. The horizontal main header is obsolete: its mating plug covered LED stubs even though the bare header fitted.

Use plain **SHR-06V-S housings without -B protrusions** at both ends and a **30–50 mm factory-crimped six-wire cable**. Wire by pin number 1→1 through 6→6; keep USB D−/D+ in positions 2/3 adjacent. Colours are unverified. Carrier wires leave left; main wires leave rearward and bend left. Confirm actual plug and wire fit before the final case.

References: [JST SH drawing](https://www.jst.com/wp-content/uploads/2021/01/eSH.pdf), [GCT USB4105 drawing](https://gct.co/files/drawings/usb4105.pdf). Native checks are under `hardware/reports`.

## Enclosure and service

Concept: **93.6 × 22.6 × 24.0**, open 90.4 × 18.4 front, 3.0 LED standoff, main front ledges and body shoulders. The removable back carries the reinforced carrier bracket. Integral shell stops react lateral and withdrawal loads without using LED leads as structure. Socket recess is **1.825**, with an enclosed 14 ×6.5 well and 2.42 shell roof.

See `enclosure-notes.md`, `enclosure.scad` and `assembly-stack.svg` for assembly and load paths. The full array, cable bend, solder fillets, printed retention and insertion loads require prototype checks. No complete array or printed enclosure is represented as physically verified.
