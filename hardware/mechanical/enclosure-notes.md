# Enclosure and assembly concept

29 October 2026. This concept follows the frozen 88.4 × 17.3 main PCB and 16.0 × 16.8 USB carrier placement. It supersedes the earlier 14 × 15 carrier suggestion in `layout-review.md`. It is an editable mechanical study, pending a printed fit sample and actual connector/cable check.

`enclosure.scad` contains the parametric shell, removable back, carrier cradle and illustrative electronics. Select `view = "shell"` or `view = "lid"` for individual parts; the lid view turns its outside face onto the print bed. `assembled`, `exploded` and `section` help inspect the stack. `assembly-stack.svg` is the dimensioned packaging drawing. The supplied `enclosure-PROTOTYPE-shell.stl` and `enclosure-PROTOTYPE-back.stl` are trial-print parts. Their CAD solids and mesh topology have been checked, but sliding fit, retention and actual cable/PCB fit have not been tested.

## Dimensions and stack

The case is **93.6 wide × 22.6 high × 24.0 deep**, with a **90.4 × 18.4 open front**. The PCB outlines remain behind the nominal 88.9 × 17.8 LED envelope. The case is larger than the LEDs so it can have walls and support the boards. No front lip covers the light-emitting face. An extra 1.0 of cavity height above the LEDs provides room for sturdy carrier supports; the front opening and bottom USB wall keep their original positions.

Main PCB x/y coordinates are used throughout: x increases right, y increases toward the bottom. The LED front face is z=0 and z increases toward the rear.

| Stack item | Front z | Rear z | Thickness or gap |
| --- | ---: | ---: | ---: |
| LED plastic body | 0.00 | 6.30 | 6.30 |
| Lead standoff | 6.30 | 9.30 | 3.00 |
| Main PCB | 9.30 | 10.90 | 1.60 |
| Main rear to carrier underside | 10.90 | 14.40 | 3.50 |
| USB carrier PCB | 14.40 | 15.40 | 1.00 |
| USB receptacle | 15.40 | 18.71 | 3.31 |
| USB to back clearance | 18.71 | 22.80 | 4.09 |
| Removable back | 22.80 | 24.00 | 1.20 |

The main connector is a **vertical JST BM06B-SRSS-TB**, at main (69.0,12.2), with the plain SHR-06V-S cable housing. Its approximately 6.3 mated height reaches z=17.2 and leaves 5.6 to the inside back for wires to bend left. Its conservative body envelope x=67.1..70.0, y=8.2..16.2 sits to the left of the carrier. The carrier's plug ends at x=70.675, leaving 0.675 between plastic envelopes. A horizontal main header was rejected because its mating plug would cover adjacent LED lead stubs even though the bare header fits.

The 3.5 board-to-board gap clears the remaining main-board SMD parts and trimmed lead/solder envelopes. Inspect the carrier underside, USB stakes and solder fillets rather than treating the PCB surfaces as the only solid objects.

## Bottom USB port

The carrier origin is **(72.15, 0.25)** relative to the main PCB. Its USB connector centre is local **(10.7, 13.7)**, giving global x=**82.85**. The mating face is y=**17.625**: the stock footprint's PCB-edge annotation is +3.1 from the connector origin, while its metal front face is +3.675. Confusing those two planes changes the recess by 0.575.

The normal outside bottom wall is y=19.45, so the metal face is recessed **1.825**. The model relieves an enclosed **14.0 wide ×6.5 high port well** all the way to the receptacle. The 24.0 depth leaves 2.42 of shell roof before the rear split, plus the 1.2 back plate, so the well has a substantial closed roof. The case therefore presents a shallow recessed bottom port at the far right. It does not claim the receptacle is flush with the outside wall. Flush outer alignment would require a different wall shape or carrier position and must be checked against the actual cable overmould.

Check the selected USB-C cable before printing the final case. The 14 × 6.5 relief is an initial plug envelope, not a guarantee that every USB-C overmould fits. The increased depth removes the earlier thin-bridge concern and makes an open rear notch unnecessary. Inspect the local stiffness and plug fit on a print.

## Supports and assembly sequence

The shell has insulating ledges under the component-free main PCB front edges. Small shoulders meet the rear plastic rims of the LED bodies outside the lead rows. They establish the intended LED standoff without loading the solder pins. The main assembly can enter from the open rear of the shell.

The carrier bracket is on the **removable back**. The main LED/main-board assembly enters the shell first, so fixed raised rails do not obstruct it. The carrier then slides **from the right** into two top edge channels and a broad lower-left side channel on the back. Front ledges support its underside and rear ledges leave 0.15 nominal clearance above the bare PCB perimeter. Inserting from the right keeps the tall USB body clear of the lower-left support.

The two upper support columns are **1.43 thick × 3.0 wide**, the lower-left pillar is **1.2 × 2.0**, the front and rear ledges are **1.2 thick**, and the back's locating lip is **1.2 thick**. The thicker lip is continuous because it now starts at z=20.4, above the USB shell at z=18.71. The taller columns have broad gussets in the new rear air space. These are ordinary substantial printed rails rather than thin snap clips. The lower-left side pillar also locates the board in x; a **2.4 × 2.0 × 2.6 integral block in the right shell wall** captures the opposite edge after the lid is inserted. Its 0.8 projection remains outside the main board's insertion path. Nominal carrier side clearance is 0.15 to the left and 0.45 to the right, which fits within the wider USB port relief.

No PCB mounting holes or metal fasteners through either board are needed. The back has a friction-fit locating lip and pry recess; test its grip, the sliding channels and USB insertion loads with the actual printer and material. The boards should slide into their supports without being bent or clamped against components. The 0.15 rear-stop gap is clearance, not a command to preload the PCB.

USB insertion drives the carrier's upper PCB edge into the two top columns, then through the back's locating lip to the shell. USB withdrawal drives its lower-left PCB edge into an integral **2.0 × 1.95 × 2.6 bottom shell block**, at x 73..75, y 17.5..19.45, z 14.4..17.0. It limits downward carrier travel to 0.45, leaving the top ledges engaged. Both this stop and the side fence begin beyond the main PCB outline, so they do not block insertion of the main assembly. The USB shell's through-hole stakes transfer connector force into the carrier. The case should take these loads; the harness and LED leads should not.

The main PCB rests on front edge ledges and is retained by the back's perimeter stops. LED plastic rear rims rest on separate shoulders. Check the actual body thickness and 3.0 standoff before closing so those supports meet their intended surfaces without forcing the soldered leads to bend. The enclosure is not a clamp for correcting a misaligned LED assembly.

Intended order:

1. Electrically test the main and USB boards, then one LED module before fitting the other six.
2. Use the front alignment tray plus **two removable 3 mm spacer rails**, `led-standoff-spacer-3mm.stl`. The working bar is 100 × 1 × 3. Put the rails between the LED backs and PCB front, with centres at board y 3.57 and 13.73, handles projecting outside the array's left end. Those positions lie between pin rows, leaving 0.52 nominal clearance to 0.5-diameter pins. Tack two opposite pins on every module and confirm all bodies sit uniformly. Let the joints cool, slide both rails left and remove them, then complete the remaining joints. The rails pass only 0.07 from the front pad rims, so removing them after tacking avoids keeping warm plastic beside front solder fillets. The front tray alone does not set the 3.0 gap. Trim the leads to the intended 1.0 rear projection and check the complete assembly without forcing it sideways.
3. Place the main LED assembly into the shell from the rear, with the LED faces toward the open front and the PCB resting on its front ledges.
4. Slide the tested USB carrier into the removable back's cradle, then connect the short JST harness to both boards.
5. Bend the main connector wires left, fold the harness into the reserved length to the left of both connectors, inspect that no wire is pinched, then close the back. Keep boot/reset/SWD contacts accessible by removing the back during development.

## Harness space

The carrier's JST entry faces left. Its mated JST SH envelope extends to global x=**70.675**; the conservative header-plus-plug envelope is approximately **6.25 deep × 8.0 wide × 2.95 high**. This includes the extra approximately 2 mm of mating housing beyond the bare board connector.

The main JST points toward the back and its wires bend left. Its lower y placement keeps the carrier's y=2.5..7.5 wire exits above the main connector's y=8.2 body edge. Use the plain **SHR-06V-S housing without -B protrusions** at both cable ends. The source reserves an illustrative wire-loop region at x=54..67, y=2..15, z=14..18.7 to the left of the main vertical connector and above the remaining SMD parts. The main header's 5.6 of rear wire-bend room needs checking with the actual wire gauge.

Use a **30–50 mm factory-crimped six-wire harness**, keeping USB D−/D+ adjacent and confirming pin-to-pin continuity at both ends. Do not infer cable wiring from colours. Route the loop gently; the reserved volume is not proof that a specific cable's minimum bend radius or overmould fits. The harness should be connected before closing and must not transfer lid-removal force into either small connector.

Ready-to-quote cable specification: **two genuine JST SHR-06V-S housings, 12 matching SSH-003T-P0.2-H contacts, six flexible 28AWG wires, 40 mm nominal contact-to-contact length (acceptable 30–50 mm after fit), pin 1→1 through 6→6**. Ask for a finished factory-crimped assembly, not loose housings. [LCSC's SHR-06V-S page](https://lcsc.com/product-detail/Housings-Wire-To-Board-Wire-To-Wire_JST-SHR-06V-S_C265411.html) lists a custom-cable service with MOQ 1; obtain its drawing/quote for this exact short harness. The product number C265411 itself is only the empty housing. An exact 30–50 mm stocked finished cable has not been verified, so do not buy a longer or differently wired cable assuming the case already accommodates it. Factory wire colours are unrestricted; the assembly diagram assigns nets only by pin number.

## Checks before final fabrication

The lead-grid fit, all seven actual bodies, exact module standoff and clipped lead height need checking with the supplied 1:1 template and assembly jig. Print a small fit coupon for the 0.22 lid clearance and carrier rail channel before a complete case. Check USB plug insertion/removal loads, the enclosed port well, the removable back's grip, carrier capture against the side fence and the wire loop with physical parts. Recheck perimeter rail locations against the final routed PCBs and solder fillets. The preview uses component envelopes and simplified LED dots, not a complete collision-certified solid model.

The stack arithmetic and board/connector placement were checked against the KiCad footprint geometry and [JST's SH assembly drawing](https://www.jst.com/wp-content/uploads/2021/01/eSH.pdf). The SVG was rendered and visually inspected. Official OpenSCAD 2021.01 was installed from openscad.org and used to compile both prototype parts and render the assembly. The exported STLs were checked for closed, consistently oriented meshes. The documented envelope collision checks exclude intentional support contact planes. These checks do not establish printability, exact solder-filleted hardware fit, cable bend radius or physical retention.


## Trial printing

Print both prototype files as oriented: shell with its front rim on the bed, back with its outside face on the bed and the supports growing upward. The open shell ledges and port roof create local bridges/overhangs; inspect the slicer preview and use removable supports if your printer needs them. Keep support scars away from the board-contact ledges. Use the same material and clearance coupon planned for the final case. Test the empty case/back fit first, then add unpowered electronics and the actual cable, checking that nothing is forced when closing. These are prototype STLs, not a claim that a completed physical assembly has been proved.
