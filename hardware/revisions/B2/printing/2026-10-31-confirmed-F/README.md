# Confirmed-F case and fit prints — 31 October 2026

This pack matches the owner-selected **12.875 mm** module pitch: **F / +0.175 mm per join**. The seven-module PCB is **89.450 × 17.300 mm**; the case outside is **94.650 × 22.600 × 24.000 mm**. The older 12.700 mm jobs in the parent folder remain historical reference files.

Use a **stock Ender-3 V3 KE, 0.4 mm nozzle, Creality Hyper PLA grey 1.75 mm**. These files are for PLA. No printer has been connected or started remotely. Copy a G-code file to the printer's USB drive and start it manually.

[Download the three-file print pack with instructions and verification](B2_F_12p875_KE04_HyperPLA_PrintPack.zip). Total slicer estimate: **2h 3m 8s / 22.03 g** including fit tests, shell supports and brim. Shell plus back/cap alone: **1h 24m 20s / 17.18 g**. Heating and levelling can add time.

Print one set in order, letting each job cool before removal:

| G-code | Contents | Estimate | PLA |
|---|---|---:|---:|
| [01 — Fit tests](gcode/01_B2_F_FitTests_KE04_HyperPLA.gcode) | Exact updated 84-hole, 1.6 mm dummy PCB; MCU channel sample; two-piece closure sample; 50 mm calibration coupon | 38m 48s | 4.85 g |
| [02 — Shell](gcode/02_B2_F_Shell_KE04_HyperPLA.gcode) | Widened front shell, removable supports beneath the PCB ledges, 3 mm outside brim | 53m 8s | 12.36 g |
| [03 — Back and cap](gcode/03_B2_F_BackAndCap_KE04_HyperPLA.gcode) | Widened rear cover and unchanged small MCU retaining cap | 31m 12s | 4.82 g |

The MCU, USB breakout, screw-post coordinates and port location remain fixed relative to the left end. The case width and complete LED-mounting geometry change; one internal upper main-PCB stop also moves 0.8 mm to keep the shifted J12 wire pad clear. The front opening is 91.450 × 18.400 mm. The pin pattern inside each of the seven modules is unchanged.

## Settings

The owner-proven native KE homing, 5×5 bed mesh, X=-2 mm purge line and final parking sequence are retained. Model/first-layer height is 0.20 mm, scale is 100%, and XY hole/contour compensation is zero. Nozzle temperature is 220°C on the first layer then 215°C; bed is 60°C then 55°C. Cooling is off on layer one and reaches 100% from layer two, with small-layer slowdown.

Three walls, five top/bottom layers and 25% gyroid infill use the earlier case profile. First layer is 20 mm/s, outer walls 35 mm/s, inner walls 60 mm/s and bridges 25 mm/s. The shell uses snug build-plate supports with 0.20 mm top contact gap and two interface layers. The other jobs have no supports or brim, preserving the narrow MCU channels. See the prepared and sliced Orca projects for the full settings.

## Check the physical assembly

Measure the 50 mm coupon and the dummy PCB: **89.450 × 17.300 × 1.600 mm**. Check it lies flat before fitting LEDs; its hole centres exactly match the updated PCB audit. Print holes are 1.0 mm, while the real PCB holes are 0.90 mm finished, so this does not certify the factory hole fit.

After cooling the shell, remove its outside brim and the temporary support strips through the front/rear openings. Clear the undersides of the permanent PCB ledges and the USB well without levering against them. Dry-fit the dummy on the ledges, then check the empty cover seats and reopens at its top notch. Confirm the four detents retain the cover under cable insertion/removal and survive several opening cycles. Do not scale the entire case to adjust a local tight fit.

Use the exact headerless XIAO RP2040 Plus and Adafruit 4090, the intended USB cable, two M2×6 USB screws and one M2×8 cap screw. Screw heads must be at most 4 mm wide and 1.5 mm high. Check the stock modules in the coupons and cover without power. Follow the [mechanical guide](../../mechanical/README.md) for module orientation, the 3 mm LED standoff, trimmed lead/solder/wire allowances, assembly and strain relief. Do not force the case shut against untrimmed leads or misplaced boards.

## Source and checks

`preparation.json` records current source hashes and all object placements. `profiles/` contains full machine/material/process snapshots. `projects/` and `sliced-projects/` contain editable Orca projects; the sliced files embed the same bytes as the standalone G-code. `slice-provenance.json` records the successful installed OrcaSlicer 2.4.2 commands and hashes.

`verify_print_pack.py` independently reads the actual dummy mesh's 84 hole loops, compares the sliced meshes with source triangles at 100% scale and zero rotation, and parses executable G-code for heating, cooling, native start/end, support/brim use, every object's first layer and movement bounds. Its results are in `verification.json`. These software checks do not replace the new case's physical trial fit or validate real solder, wiring, purchased module revisions or snap force/lifetime.
