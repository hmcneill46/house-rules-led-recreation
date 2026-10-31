# TLC59283 revision — mechanical checks and selected purchase plan

The driver/resistor substitution preserves the physical design. Fresh native KiCad comparison found identical positions, orientations, footprint IDs, pad sizes/shapes/drills/layers/nets, board outline and thickness across all **82 footprints and 355 pads**. The board remains **89.45 × 17.30 × 1.6 mm**, with **12.875 mm module pitch**. The case, stock-module positions and bottom-right USB port remain unchanged.

**The full case-print check is still pending.** The owner confirmed the 12.875 mm pitch fitting coupon, but explicitly has not completed the full case print/fit. Confidence that it will fit is not treated as completed physical evidence. Existing confirmed-F print files remain applicable; no reslicing is required for this electrical identity/value change.

## Fresh checks

- Native new-PCB mounting/contact audit: **PASS**, no stop/pad conflicts and no cap-screw height conflicts. Only the already-qualified low-profile R9 footprint lies within the screw-head XY envelope.
- Manufacturer-source stock-module contact audit: **PASS**, all four XIAO corner contact rectangles clear of source copper/component bounds.
- OpenSCAD rebuild in a temporary copy: all five meshes closed, consistently wound and positive-volume. The normal electronics/support, seated shell/cover and eleven-step MCU insertion intersections are empty. The intended snap-closing transition still has positive interference; snap force/lifetime remain physical checks.
- Freshly rebuilt meshes reproduce the existing triangle geometry at 100% scale. Twenty-one tracked geometry/print inputs remain byte-identical to the pre-substitution revision.
- Three-job Ender-3 V3 KE / Hyper PLA print-pack validator: **PASS against the new PCB audit**, including all 84 dummy-hole centres, native printer start/end commands, temperatures, motion bounds and exact embedded G-code.
- Seven-object combined-plate validator: **PASS against its archived confirmed-F board**, retaining its historical fixed-hash assertion. Exact new/old native geometry equality independently binds that unchanged print to the new board. All seven source meshes remain unscaled; shell-only supports/brim and executable toolpaths pass.

The represented component-to-wire allowances remain 0.8 mm beneath the MCU and 0.5 mm beneath the USB board. Actual solder, purchased module revisions, wire dressing, screw heads, printer shrinkage and cable moulding still need inspection/dry fit. These checks do not connect to a printer or power a board.

## Selected purchases: three finished displays, two spare populated mains

| Purchase now | Quantity | Delivered budget |
| --- | --- | ---: |
| Main PCB, all 55 small components factory assembled | Five; finish three and retain two populated mains | £103.16 |
| Headerless XIAO RP2040 Plus | Three | £17.06 |
| Headerless Adafruit 4090 USB-C breakout | Three | £12.50 |
| 28 AWG thin PTFE wire | 1 m red, 1 m black, **5 m blue** | £16.80 |
| Specified M2 button screws and key | **10 × 6 mm, 5 × 8 mm**, one 1.3 mm key | £17.90 |
| Electronics-safe silicone and cable ties | One tube and one pack | £9.83 |
| **Total now** | Existing 21 LEDs used; no additional LEDs now | **£177.25** |

The extra screws and two extra blue metres are included now for the optional two later displays. After finishing three, retain four M2×6 and two M2×8 screws, along with the unused wire/key/ties and usable silicone. Planned five-unit starting cuts use approximately 0.925 m red, 0.575 m black and 4.75 m blue before trimming; bought lengths are allowances rather than a pre-cut harness guarantee.

At the recorded prices, the optional later purchases are two controllers (£12.57 delivered), two USB breakouts (£9.60 delivered) and **14 further LED modules (£29.99 delivered)**, totalling **£52.16**. No further main-PCB order is needed. The staged five-display total is **£229.41**, £7.39 above buying everything for five together, because controller/USB delivery is repeated.

These are budgets using recorded 31 October quotes, shipping/tax/depanel allowances and exchange rate. Prices, stock and final review can change; opened silicone may need replacing after storage. Owned filament, tools, supplies, USB power and data cables cost £0 new spending. Prototype remake/rework costs are not included. **Nothing was ordered, paid for or sent to a printer.**

Detailed machine-readable evidence: [mechanical verification](mechanical-purchase.json), [selected purchasing plan](selected-purchase-plan.json). The [retail source record](../../quotes/updated-F-2026-10-31/retail/README.md) and [factory quote record](../../quotes/alternatives-2026-10-31/jlc-59283-7p15k-cost-only/complete55-quotes.json) retain original price evidence.
