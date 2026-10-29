# B2 case and fit-test prints — Ender-3 V3 KE / Hyper PLA grey

Ready-to-copy G-code for a **stock Creality Ender-3 V3 KE with a 0.4 mm nozzle**, using **Creality Hyper PLA grey, 1.75 mm**. These are PLA files. Copy the selected `.gcode` to the printer's USB drive and start it at the printer. No printer was connected to or started remotely.

[Download the three-file print pack](B2_KE04_HyperPLA_PrintPack.zip), unzip it and read `PRINT_FIRST.txt`, or use the individual files below.

Print **one set** in this order. Let each print cool before removal. The times are OrcaSlicer estimates; real heating, levelling and machine behavior add time.

| File | What it prints | Estimate | PLA |
|---|---|---:|---:|
| [01 — Fit tests](gcode/01_B2_FitTests_KE04_HyperPLA.gcode) | MCU channel sample, two-piece closure sample, 1.6 mm dummy main PCB, 50 mm scale coupon | 38m 22s | 4.80 g |
| [02 — Shell](gcode/02_B2_Shell_KE04_HyperPLA.gcode) | Front shell; removable internal supports and a 3 mm outside brim | 52m 39s | 12.24 g |
| [03 — Back and cap](gcode/03_B2_BackAndCap_KE04_HyperPLA.gcode) | Rear cover and small removable MCU retaining cap | 30m 49s | 4.77 g |

Total slicer estimate: **2h 1m 50s / 21.81 g**, including fit tests, supports and brim. Shell plus back/cap alone: **1h 23m 28s / 17.01 g**. Each job is printed by layer, not sequentially by object. You do not need to slice the files again.

## Settings and support removal

The machine start/end sequences are preserved from the owner's earlier successful KE fit-print project, including its stock X=-2 mm purge line, homing, 5×5 bed mesh and final parking. Both the original project and G-code remain unchanged.

| Setting | Value |
|---|---|
| Nozzle | 220°C first layer; 215°C thereafter |
| Bed | 60°C first layer; 55°C thereafter |
| Layer height | 0.20 mm model layers, first layer 0.20 mm |
| Walls / top / bottom | 3 / 5 / 5 |
| Infill | 25% gyroid where a cavity remains; thin features are mostly solid |
| First layer / outer / inner walls | 20 / 35 / 60 mm/s |
| Bridges | 25 mm/s |
| Cooling | Off for layer one; 100% from layer two, with small-layer slowdown |
| Scale / XY hole compensation | 100% / 0 mm |
| First-layer elephant-foot correction | 0.05 mm |
| Shell supports | Normal, snug, build-plate-only; 0.20 mm top contact gap, two interface layers |
| Shell brim | Outside only, 3 mm, 0.15 mm separation |
| Other jobs | No supports, brim or raft |

The shell has flat PCB ledges with 2.55/1.55 mm cantilevers at Z8.1, so its G-code includes supports underneath them. After cooling, remove the outside brim, then gently remove the support strips through the large front/rear openings. Clear the ledge undersides and USB opening without levering against a thin ledge. Do not mistake the permanent PCB ledges for removable support. Compare with the unsliced mesh in the editable project if unsure. The USB roof also has a short bridge printed slowly with full cooling.

The back, cap and coupons keep supports **out of the narrow MCU channels**. Their small ledges use the slow bridge/overhang settings. Inspect those ledges and clear loose strands before trial fitting; test results may require a later tolerance adjustment. Shell support layers may use intermediate Z heights because Orca's independent support layer height is enabled; the model setting is still 0.20 mm.

## What to check before buying PCBs

1. Measure the scale coupon: designed length **50.00 mm**. Measure the dummy PCB thickness (**1.60 mm**) and outline (**88.40 × 17.30 mm**). Record actual readings; do not scale the whole case to fix a tight fit.
2. Check the loose XIAO PCB in the MCU-channel coupon. Test the two closure pieces together gently. The short coupon establishes local bead/pocket fit; the full case has different stiffness.
3. Remove all shell supports and dry-fit the dummy main PCB on its case ledges. The dummy uses the final board's **exact 84 LED hole centres**. Its **1.0 mm FDM holes** differ from the real PCB's **0.90 mm finished holes**. It has no copper or component bodies, so it does not reproduce solder/parts/wire clearance or certify PCB hole tolerances.
4. With everything **unpowered**, try the actual headerless XIAO, USB breakout, intended USB plug and retaining cap in the back. Follow the [mechanical assembly guide](../mechanical/README.md). Use two M2×6 USB screws and one M2×8 cap screw, heads at most 4.0 mm wide / 1.5 mm high; turn gently into the printed pilots. Do not fit the loose pin headers.
5. Check the USB plug seats fully through the bottom-right well. Test the empty shell/cover first, then the unpowered module fit: the back should seat, stay retained, and release with a plastic pick at the top notch. Support the back during removal. Do not force it shut against untrimmed LED leads or a misplaced board.
6. If trial fitting LEDs, use the confirmed upright orientation and preserve the 3 mm body-to-board gap. Do not bend leads to compensate for a mismatch. Their final rear projections are trimmed after soldering to the real PCB; the plastic dummy does not replace that assembly.

Stop after the coupons if they are clearly too tight, loose or inaccurate. Send the caliper readings and describe which fit failed; the relevant local tolerance can then be adjusted. A PLA print that looks good is still a mechanical prototype, not an enclosed electronics temperature test.

## Exact stock modules

Buy **one of each per display**, without fitted headers:

- [Seeed Studio XIAO RP2040 **Plus**, SKU100059977 — Unmanned Tech](https://www.unmannedtechshop.co.uk/products/seeed-studio-xiao-rp2040-plus): £4.49 including VAT when checked 29 October 2026. The Plus version exposes the USB data solder pads used by B2. Headers may be supplied loose; leave them unfitted.
- [Adafruit **4090** USB-C downstream breakout / ADA4090 — The Pi Hut](https://thepihut.com/products/adafruit-usb-c-breakout-board-downstream-connection-ada4090): £2.90 including VAT when checked 29 October 2026. Use this exact breakout for the case and CC/data wiring.

Parts subtotal **£7.39 per display**, before shop postage. The earlier one-set UK delivered estimate is **£14.78**; checkout determines current shipping/stock. No parts have been purchased by the agent. See [the recorded module delivery estimates](../../../cost-down/module-shipping-quote.json).

## Source and verification

- `projects/`: prepared editable projects; `sliced-projects/`: native Orca projects with the exact exported G-code embedded.
- `profiles/`: full settings snapshots; `preparation.json`: unchanged source-mesh hashes, dimensions, placement and identity scale/rotation.
- `independent-gcode-audit.json`: independent review of actual G-code, settings, temperatures, geometry placement, motion bounds and embedded-file equality.
- `previews/`: actual Orca preview screenshots, including a cut through the shell's support strips.
- `models/`: print-only dummy PCB SCAD/STL. The five original B2 case/coupon STLs are unchanged in `../mechanical/`.

`prepare_prints.py` generates the prepared projects from the existing owner KE/Hyper PLA profile and unchanged source STLs. Slicing uses installed OrcaSlicer **2.4.2**, `--slice 0 --arrange 0 --orient 0`, with a separate temporary data directory. The exact commands and exported hashes are recorded in `slice-provenance.json`. Sliced projects and copied standalone files are checked for byte-identical G-code. No PCB, schematic or firmware change is part of this print preparation.
