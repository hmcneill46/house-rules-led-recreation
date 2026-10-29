# Physical House Rules — prototype A1

A complete editable electronics design for seven owner-supplied Wenrun LMD07057AUE-101B displays, arranged as a **35 × 7, 245-dot** screen. Designed 29 October 2026. This is a **prototype awaiting physical validation**, with fabrication and assembly files for review. No boards have been ordered or tested. Start with [the illustrated summary](design-summary.html).

## What was designed

| Item | Design |
| --- | --- |
| Display arrangement | Seven upright modules, 12.70 mm centre spacing; user reports seven-module printed-fixture fit passed |
| Main PCB | 88.4 × 17.3 × 1.6 mm, six copper layers |
| USB carrier | 16.0 × 16.8 × 1.0 mm, four copper layers, behind right end |
| Drivers | Four IS31FL3729-QFLS4-TR, addressing 2 + 2 + 2 + 1 modules |
| Controller | STM32G0B1KBU6, 128 KB flash, native USB and factory DFU |
| Factory assembly | 37 main-board SMD placements on B; seven carrier placements on F |
| Owner assembly | Seven LED modules: 84 through-hole joints per unit; plug-in six-wire harness |
| Power | USB 5 V only; both A-to-C and C-to-C cables |
| Enclosure concept | 93.6 × 22.6 × 24 mm, printable shell and removable rear carrier cradle |

The PCB is inset 0.25 mm from the **nominal** 88.9 × 17.8 mm seven-module envelope. On 29 October 2026 the owner reported that the printed pin-fit plate worked and all seven LED modules fitted very nicely. The plate shares the main PCB's 88.4 × 17.3 mm outline and 84 pin centres. Its 1.0 mm thickness and nominal 1.0 mm holes differ from the main PCB's 1.6 mm thickness and 0.9 mm finished holes. This confirms the reported group's mechanical arrangement, while electrical orientation, actual PCB hole tolerances and the other two groups remain separate checks. See [the recorded user fit result](reports/user-fit-confirmation-2026-10-29.json).

The USB carrier solves a physical conflict: the selected USB socket will not fit directly between the LED solder leads. It remains within the display's projected outline and connects through a short keyed JST-SH six-way harness, with a vertical header on the main board to clear the LED lead stubs. The bottom-right socket sits approximately **1.825 mm recessed** behind the concept case's outer wall, with a 14 × 6.5 mm plug well. A cable plug protrudes. The case is an editable fit concept; verify the chosen plug and actual assembly before printing a final shell.

## Where to look

- [Main KiCad project](kicad/house-rules-main.kicad_pro), [main PCB](kicad/house-rules-main.kicad_pcb), [schematic](kicad/house-rules-main.kicad_sch).
- [USB KiCad project](kicad/house-rules-usb.kicad_pro), [carrier PCB](kicad/house-rules-usb.kicad_pcb), [schematic](kicad/house-rules-usb.kicad_sch).
- [Native CAD renders](render/), including front with LEDs, bare front, component rear and carrier views.
- Manufacturing review output: `manufacturing/A1_review/`, generated after final CAD checks. It contains separate Gerber/drill archives, exact-part BOM and placement files for each board. The illustrated summary links it once exported; it is a review package, not an instruction to order immediately.
- [Offline pin-level simulator](simulation/matrix-emulator.html), [model scope](simulation/README.md).
- [Compiled firmware and programming guide](firmware/README.md), [BIN](firmware/compiled/HouseRules.ino.bin), [ELF](firmware/compiled/HouseRules.ino.elf).
- [1:1 pin-fit template](mechanical/pin-fit-template.svg), [soldering alignment tray](mechanical/README.md), [case and assembly stack](mechanical/enclosure-notes.md).
- [Assembly and test instructions](assembly-and-test.md), [verification reports](reports/).

## Electronics and brightness

These are raw LED matrices, with no controller or current limiting inside. The [Wenrun datasheet](https://cdn.shopify.com/s/files/1/0695/1347/8453/files/LMD07057AUE.pdf) specifies column anodes 1, 3, 10, 7, 8 (left to right) and row cathodes 12, 11, 2, 9, 4, 5, 6 (top to bottom). The custom footprint numbers the front-view left strip 1–6 downward and the right strip 12–7 downward. A physical single-pixel check is still required: the photos identify a -101B-Q2 suffix whose meaning is not established. Never connect a module directly across 5 V.

Each driver selects five shared anode columns and supplies independent current sinks to each module's seven rows. The paired modules share anodes only; their cathodes remain independent. Addresses are 0x34–0x37. Four 47 kohm, 1% ISET resistors limit nominal full-scale dot current to approximately **7.25 mA peak**, below the LED's 20 mA continuous absolute maximum. The 80 mA pulse rating is conditional on duty ≤1/10 and is **not applicable** to the selected five-phase scan. No separate resistor is needed for every dot because the drivers regulate current.

The calculated all-on LED load is approximately **342 mA average**, before MCU and driver overhead. The default dim mode uses approximately 43 mA average LED current. These are nominal calculations, not measured input current or guaranteed brightness. Compare brightness and timing with the reference and measure full-on temperature/current before considering any increase. Driver register details and source references are in [the functional model](simulation/README.md); local manufacturer PDFs are in [reference/](reference/).

The six-layer main board reserves In1 for GND and In4 for +5 V; F/In2/In3/B carry signals. The USB data pair follows the front copper's upper margin, with the adjacent GND layer providing its reference. Default copper clearance is 0.15 mm. A documented 0.10 mm via-to-pad rule applies only inside each LED driver courtyard, enabling filled/capped QFN fanout; via-to-track and via-to-via spacing retain the default. All vias are intended as ordinary full-stack through vias, with minimum 0.4 mm copper / 0.2 mm drill. There is no blind-via or HDI requirement. The design does not claim controlled 90-ohm impedance or USB certification; the short harness and entire USB path require hardware tests.

## USB and programming

Separate 5.1 kohm CC resistors make the board a 5 V USB-C sink in either plug orientation. No high-voltage Power Delivery negotiation is needed. The input has a resettable fuse, a 5 V TVS and data/CC ESD protection. Independent 47k/47k dividers let the MCU conservatively detect Type-C current advertisements without violating CC termination or ADC input-impedance limits.

Firmware starts with drivers disabled, performs source qualification, and uses full brightness only after a configured 500 mA USB connection, a positively identified BC1.2 charging port, or a conservative sufficient Type-C current indication. Unknown/default-current sources run dim; host suspend blanks and enters a low-power path. Inrush, total input/suspend current, BC1.2 detection and wake still require bench measurements. A fuse does not grant permission to draw current.

Use a **USB data cable** and STM32CubeProgrammer to load the factory USB DFU bootloader. A virgin blank MCU normally enters ROM automatically. After first programming, set and verify the documented G0B1 boot option bytes so holding BOOT while resetting re-enters DFU. Five SWD recovery pads remain accessible with the rear cover removed. BOOT shares PA14/SWCLK on this exact part. Follow [the exact programming steps](firmware/README.md); the running USB serial interface is not itself a flashing bootloader.

## Software checks and their limits

Native KiCad ERC, schematic-netlist comparison and PCB DRC/parity reports are saved in `reports/`. Check their current timestamps and counts; the illustrated summary reads the reports rather than assuming success. ERC/DRC establish represented connectivity and geometric rules, not physical LED identification, analogue behaviour or manufacturing yield.

The offline model reconstructs the display by traversing independently defined LED diode terminals and the actual module-to-driver connections. All 245 walking pixels and the artwork's 22,248 distinct windows were checked. Twenty-six host tests pass, including deliberate row/polarity/shared-cathode faults; see the timestamped [software verification record](reports/software-verification.json). A separately compiled C++ playback test compares **60,000 frames and two complete traversals** with the original recreation. The compiled ARM image occupies 66,108 bytes flash and 4,560 bytes static RAM. Its USB descriptor and critical startup/power hooks were inspected in the ELF. These checks do not execute the MCU or establish physical USB compliance.

## Manufacture and minimise repeat costs

Quote **three main boards and three carriers**, with the small components assembled and the 21 existing modules retained locally. Also compare a minimum pilot assembly quantity before committing all three. Fit and prove one unit before soldering the remaining 14 displays; a single assembly batch may avoid paying two sets of setup and UK shipping again. Use the full-size paper template and soldering jig first to reduce mechanical risk.

First supplier to quote is [JLCPCB Economic PCBA](https://jlcpcb.com/capabilities/pcb-assembly-capabilities): its published capabilities support these board dimensions, single-side assembly, 0.4 mm QFN pitch, 0402 parts and 2/4/6-layer boards. Main assembly is on B; carrier assembly is on F. The main BOOT switch has a 2.2 kohm series resistor so it can safely share PA14 with the SWD clock. Request green FR-4, 1 oz copper, standard six-layer 1.6 mm main stack and four-layer 1.0 mm carrier stack. Have the factory review QFN stencil/thermal vias and choose filled/capped treatment for exposed-pad vias; do not assume mask tenting will seal them. Confirm 0.2 mm drill/0.4 mm via pricing and exact part stock before paying. The manufacturer must check placement rotations and polarity in its assembly viewer.

[PCBWay assembly](https://www.pcbway.com/pcb-assembly.html) is a useful competing total-delivered quote. Bare boards alone are poor value if the tiny QFNs then need a separate assembler. No live project quote has been obtained; an earlier rough £40–90 allowance predated the final two-board, six-layer design and must not be treated as a price. Compare fabrication, two assembly setups, component/feeder fees, short harnesses, shipping and UK VAT together. The package contains exact MPN/LCSC fields and a sourcing review; stock snapshots are not reservations. Nothing has been purchased or uploaded to a manufacturer.

Before order: verify seven-module fit and pin orientation, review the Gerbers and assembly rotations, obtain the actual quote, and agree the thermal-via/stencil process. After delivery: inspect and test the empty electronics, program via USB, fit one LED and run diagnostics, then finish the first unit and measure it. Only after that should the other units be populated. A PCB electrical test cannot prove the animation or LED polarity.

## Tools and reproducibility

KiCad 10.0.7, Freerouting 2.5.0 and pinned Arduino tooling were installed locally. KiCad provides the editable schematic/PCB, native rule checks, manufacturing exports and faithful 3D images. [atopile](https://github.com/atopile/atopile) and [tscircuit](https://tscircuit.com/) are viable code-first tools; native KiCad was selected here for the custom footprint, tight mechanical layout and review/export workflow. Python-generated circuit data retains a code-readable source alongside the native files. No matching PCB MCP plugin was found in the available directory; no unofficial server was required.

`tools/circuit_spec.py` is the electrical/placement specification. `build_schematics.py --verify` rebuilds schematics and verifies their nets. **`build_pcbs.py` recreates placement and discards routing**; do not run it over a final routed board casually. Recorded `.dsn`/`.ses` files are routing intermediates, and the final native `.kicad_pcb` files include manual finishing work. `finalize_pcbs.py --metadata-only` refreshes fields without importing an old session. Preserve the final native boards as the deliverables. See [tool versions](design/tooling.txt) and [third-party library notices](kicad/third-party/README.md).
