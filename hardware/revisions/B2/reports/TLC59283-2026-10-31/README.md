# B2-F — TLC59283 and 7.15 kΩ engineering update

31 October 2026. The owner selected three finished displays, two populated spare
main boards, and the extra screws/wire for those spares. U1–U4 now specify
**TLC59283RGER/C485815**; R1–R4 specify **7.15 kΩ ±1%,
0603WAF7151T5E/C25980**. The updated schematic, PCB, electrical source,
firmware contract, model and manufacturing BOM agree on these exact parts.

**All represented checks passed. No order or payment was submitted.** This is
an engineering prototype review package, not approval of unbuilt hardware.
The owner explicitly has **not yet completed the full case print/fit check**.
The successful 12.875 mm pitch coupon remains the evidence for module spacing.

## Geometry and behaviour

The PCB remains89.45 ×17.30 ×1.6mm, with12.875mm module pitch. All copper,
pad geometry, drills, component positions, exposed-pad thermal vias and the
case/USB-port geometry are preserved. Only eight part identities and associated
non-geometric metadata changed. Reversing those exact strings restores every
byte of the frozen F board; a separate native geometry comparison also passes.

Nominal LED current is `1.208 ×43.8 /7.15 =7.40006mA`,0.335% below the previous
TLC59282/6.8k setting. The400Hz frame,500µs phases,30µs blank and470µs full
light time remain. USB programming, controller, wiring and artwork are unchanged.
The rebuilt UF2/BIN payloads are unchanged; contract/build metadata and ELF debug
information are refreshed against the new source.

## Verification

| Check | Result |
| --- | --- |
| Native KiCad ERC and exported schematic netlist | Zero violations;82 references/327 connected pins match |
| Native DRC, unconnected items and schematic parity | Zero in every result array, including warnings/exclusions |
| Independent part/pin/source review | Exactly eight intended identities; all pin graphs preserved |
| Board/process audit |55 factory SMT parts;84 open LED holes;276 filled/capped0.30mm vias;12 driver thermal vias |
| Actual Gerbers, paste and Excellon |15 plotted/drill files preserve commands apart from timestamps; six copper layers |
| BOM/CPL and hashes |55 exact factory references; native CPL byte-identical; all manifest outputs verified |
| Firmware host and physical pin model |245 walking pixels,60,000 artwork frames,301,235 phase reconstructions,14 injected faults |
| Actual HardwareIO backend |1,000 SPI/latch transactions; invalid-state/SPI-failure paths checked |
| Spec/schematic generator reproduction | Byte-identical regenerated spec, schematic and symbols; correct bundled U9 model retained |
| Both firmware builds/linked USB/UF2 audits |PASS; generated contract rejects stale drivers/resistors |
| Mechanical/source-module checks |Fresh OpenSCAD mesh/collision checks and native contact/head-height audit pass |
| KE/Hyper PLA separate and combined print files |Validators pass; unchanged files remain applicable |

The five native KiCad10.0.7 default ignored checks remain explicitly documented;
no custom DRC/ ERC exclusions or relaxed rules were introduced.

The [machine-readable summary](verification-summary.json) binds current source
hashes to these results. Detailed records: [identity update](identity-update.json),
[independent electrical review](independent-electrical.md), [actual manufacturing
verification](manufacturing-verification.json), [software results](software/software-verification-summary.json),
and [mechanical/print checks](mechanical-purchase.md).

## Current files and purchase plan

Use the [TLC59283 manufacturing review package](../../manufacturing/B2_F_TLC59283_7p15k_review_2026-10-31/README.md),
its [Gerber/drill ZIP](../../manufacturing/B2_F_TLC59283_7p15k_review_2026-10-31/house-rules-main-B2-fabrication-REVIEW.zip),
[exact BOM](../../manufacturing/B2_F_TLC59283_7p15k_review_2026-10-31/assembly/bom.csv)
and [native placement CSV](../../manufacturing/B2_F_TLC59283_7p15k_review_2026-10-31/assembly/cpl-manufacturer-review.csv).
The older `B2_F_12p875_review_2026-10-31` package retains TLC59282/6.8k and is
historical. Do not mix its BOM with the new files. The previous quote/cart was a
manual part-matching cost study; it was not converted into an order by this work.

The [selected purchasing plan](selected-purchase-plan.json) budgets **£177.25 now**:
five assembled main PCBs, three XIAO RP2040 Plus modules, three Adafruit4090
USB-C boards,1m red/1m black/**5m blue** thin28AWG PTFE wire,
**10×M2×6mm and5×M2×8mm** specified button screws, one1.3mm key, silicone and
ties. Use the21 owned LEDs and owned tools/filament/power supplies/data cables.
Two optional later displays budget **£52.16**, including14 new LED modules;
the staged total is£229.41 at recorded prices. Prices, delivery/tax/depanel
allowances and card exchange can change; no stock is reserved and no remake
allowance is included.

## Open checks

The full printed case needs a dry fit with the real modules, wires, specified
screws and actual USB plug. Factory CAM must approve the final outline, removable
external rails, filled/capped vias and84 open LED holes; the feeder/pin1/rotation
preview must use the exact new parts. These remain pending before an order.

TLC59283 adds source-only precharge while BLANK is HIGH. Static review found no
powered steady-state incompatibility, but VCC=0 reverse current and relative rail
ramps are not specified well enough to qualify in software. Keep both switched
rails, QOD, zero-latch/blank/low-control shutdown and current USB policy. The first
powered unit needs rail/gate/cathode/anode waveforms, ghosting and brightness
uniformity, input/inrush/suspend current, external USB programming/recovery and
enclosed temperature checks. No analogue chip emulator or physical test is
claimed. A failed measurement could require a further circuit revision.

Historical source/report snapshots are under `before/` and `software/before/`,
with the earlier manufacturing packages and Git commit01789e4 also preserved.
