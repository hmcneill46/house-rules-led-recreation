# Ender-3 V3 KE fit print

Use `HouseRules_Fit_KE04_PLA.gcode` with the **Creality Ender-3 V3 KE, 0.4 mm nozzle**, loaded with **Creality Hyper PLA grey, 1.75 mm**. Copy the file to the printer's USB drive and select it on the printer. No print has been started remotely.

This prints the two objects from the existing Orca scene: the 88.4 × 17.3 × 1 mm LED pin-fit plate and the 50 × 10 × 1 mm scale coupon. It does not print the enclosure. OrcaSlicer 2.4.2 estimates **17 minutes 20 seconds**, **0.82 m / 2.44 g** of PLA; actual heating and bed levelling add time.

## Settings saved in the project

| Setting | Value |
| --- | --- |
| Nozzle | 220°C first layer, 215°C thereafter |
| Bed | 60°C first layer, 55°C thereafter |
| Layer height | 0.20 mm, including first layer; five layers |
| Walls | Three |
| Solid shells | Five top and five bottom layers; the 1 mm parts are solid |
| First-layer speed | 20 mm/s |
| Outer / inner walls | 40 / 80 mm/s |
| Small hole perimeters | 50% speed, 2 mm threshold |
| Solid infill / top surface | 100 / 40 mm/s |
| Cooling | Off on layer one, 100% from layer two |
| Supports / raft / brim | None |
| Scale / XY hole compensation | 100% / 0 mm |
| Elephant-foot correction | 0.05 mm on first layer |

The native KE Klipper machine start/end sequences were preserved, including homing, bed levelling, the stock X=-2 mm purge line and final parking. Model geometry and positions were preserved from the original scene. Flow ratio remains the native preset's 0.98; it has not been calibrated to this individual spool.

**This is a PLA file. CR-PETG requires a separate slice with PETG settings.**

## Fit check after printing

1. Let both pieces cool before removing them. Measure the scale coupon: its designed length is 50.00 mm. Record the measured result before drawing conclusions about the pin fit.
2. Try one LED module in the plate, then seven together. Support the plate and insert the leads gently; stop if they need bending or force. Record whether all seven bodies can touch and whether every pin aligns.
3. The printed holes are nominally 1.0 mm; the PCB holes are 0.9 mm finished diameter. Printer accuracy and hole shape affect the result, so this fixture checks the arrangement and body spacing; it does not certify the PCB's hole diameter or the modules' electrical pinout.

See `../mechanical/pin-fit-plate-notes.md` for the fixture geometry and remaining measurement checks.

## Files and verification

- `HouseRules_Fit_KE04_PLA.3mf`: editable configured Orca project.
- `pin-fit-KE-original.3mf`: preserved original scene.
- `fit-print-settings.json`: exact setting overrides and preserved-entry hashes.
- `gcode-verification.json`: exported file hash, temperatures, layer heights and motion bounds.
- `orca-fit-preview.png`: actual Orca preview and successful export notice.

The exported G-code was inspected in Orca's preview and checked for five layers, both objects, expected temperatures, bed fit, and absence of supports/brim. The file has not been physically printed yet. Its SHA-256 is `6ec4a20aab41bfcfbbc914d3c4cbd04b31e1d967b3efbce91491afa91dd6227b`.
