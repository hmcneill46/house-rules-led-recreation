# Cost-down and alternative vendors — 29 October 2026

## Conclusion

**£228 / £262 are not proven best-possible prices.** They were approximate GBP references for the two JLCPCB combined DHL DDP checkout estimates, before final coupons and factory review extras. The earlier JLCONE investigation already found a cheaper pilot shipping combination: **$269.48 including VAT**, approximately **£202 at the quotation's reference conversion**, before coupons and review extras. Five of each remained **$349.63** with combined DDP. The available $30 coupon has not been applied to a final reviewed order.

No competing vendor has yet returned a comparable firm quotation covering both exact boards, all factory components, the USB shell anchors, UK delivery and VAT. The public information does **not** establish JLCPCB as universally cheapest. It does establish specific, substantial costs in this design that can be reduced by a carefully checked revision.

This is a bounded primary-source comparison. No competitor account was created, manufacturing files uploaded, human RFQ sent, terms accepted or order submitted. Public pages were read; the current child browser inventory had no available browser, so an interactive competitor calculator was not completed. Advertised starter prices are not treated as quotations for these boards.

## Exact design being compared

- Main: 88.4 × 17.3 mm, six layers, 1.6 mm, 1 oz outer / 0.5 oz inner, ENIG, 192 ordinary through vias with 0.2 mm drill / 0.4 mm pad; all filled and copper capped; 84 LED mounting holes open. Factory places 37 components on the bottom.
- Carrier: 16.0 × 16.8 mm, four layers, 1.0 mm, ten 0.2/0.4 mm vias, seven factory placements on top, including the checked USB4105-GF-A-120 socket and all four shell anchors. Lead-free HASL was used for the comparable JLC quotes.
- Finished outlines and the USB location must remain compatible with the enclosure. Temporary manufacturing rails are acceptable only if removed before delivery.

## Vendor comparison

| Vendor | Fit for the existing files | What the current public evidence establishes | Comparable delivered assembled price |
|---|---|---|---|
| **PCBWay** | Credible candidate for the exact main: advanced capabilities include 0.15 mm mechanical drilling and a 3 mil via annular ring. Its quote form offers resin filling/capping and via-in-pad. | It supports turnkey and mixed assembly, but the public assembly amount excludes bare PCBs and components; advanced fabrication and depaneling can require review. It recommends paneling boards with a side below 50 mm, which applies here. Request exact one- and three-assembled quantities if proceeding to a real comparison. | **Not obtained.** A simple assembly or bare-board headline cannot be compared with JLC's populated, VAT-paid checkout. |
| **AISLER** | Not a drop-in match to the frozen design. Its published six-plus-layer process requires at least a **0.25 mm via drill**, so the current 0.20 mm vias fail that process rule. Its listed four-layer products use 0.8 or 1.6 mm thickness, rather than this carrier's 1.0 mm. | Six- and eight-layer ENIG products exist. Assembly can start at one populated board and supports mixed SMT/through-hole work. Exact pricing is produced after uploading the project and assigning components. VIPPO compatibility would need confirmation in addition to the drill/stackup changes. | **Not obtained; geometry/process revision required first.** Its public small bare-board prices do not price the existing design. |
| **Seeed Fusion** | Worth a real quote if its advanced process accepts the exact VIPPO specification. Its standard guide lists 0.2 mm drilling and 4/4 mil routing, but specifically requires at least 6 mil inner-layer tracks for four-layer boards; the current carrier has finer routing. | Standard PCB minimum is five, assembly minimum one; turnkey SMT, THT and mixed assembly are available. The standard order page sends unsupported fabrication requirements to Advanced PCB/manual quotation and requires login before assembly-file upload. | **Not obtained.** Clarify the inner-layer routing, filled/capped vias, socket anchors and actual UK tax-paid shipping before comparing. |

Primary sources: [PCBWay advanced capabilities](https://www.pcbway.com/advanced-pcb-capabilities.html), [PCBWay quote form and price exclusions](https://www.pcbway.com/orderonline.aspx), [PCBWay assembly form](https://www.pcbway.com/quotesmt.aspx); [AISLER portfolio](https://community.aisler.net/t/pcb-portfolio/101), [AISLER six-layer design rules](https://community.aisler.net/t/6l-layer-35-m-enig-design-rules/5467), [AISLER assembly](https://aisler.net/en-US/products/assembly); [Seeed service guide](https://wiki.seeedstudio.com/Service_for_Fusion_PCB/), [Seeed order page](https://www.seeedstudio.com/fusion_pcb.html).

PCBWay is the most useful next comparison for the **unchanged** design because the required fabrication process is explicitly represented. This is a shortlist judgment, not evidence that its final price will be lower. AISLER's low advertised PCB pricing is not applicable to the existing via geometry. Seeed needs process clarification.

## What actually makes the present JLC design expensive

The local signed-in quotation records in `../quotes/2026-10-29/` give the following five-of-each batch costs, before shipping and tax:

| Cost | Main | Carrier | Combined |
|---|---:|---:|---:|
| Bare PCB batches | £64.17 | £37.06 | **£101.23** |
| Of which small-via charge | £12.54 | £12.42 | £24.96 |
| Of which forced Kelvin test | £12.47 | £12.41 | £24.88 |
| Of which Tg155 charge | £2.51 | £2.48 | £4.99 |
| Components | £38.81 | £8.10 | **£46.91** |
| Extended-component setup | £18.53 | £9.27 | **£27.80** |
| Assembly setup plus stencil | £7.34 | £7.34 | **£14.68** |

The three fine-via-related bare-board lines total **£54.83 per combined order batch**, not per finished display. The actual main-board filled/capped via line was **£0.00** under the quoted six-layer offer. Reducing to four layers while retaining via-in-pad could lose that benefit and add a filling charge; a lower layer count alone is not a demonstrated saving.

For the five main boards, the STM32 MCU accounts for about £19.59 and the twenty LED-driver ICs about £14.44: approximately 88% of their £38.81 component subtotal. Merely changing tiny resistor prices cannot produce a large saving. Replacing these ICs could affect firmware, footprint, drive current or availability and therefore needs a separate engineering case.

Two separately assembled board designs also incur two setups, two stencils and two sets of extended-part fees. Combining manufacturing only becomes useful if stackups, thickness, assembly sides, depaneling and physical fit still work; this cannot be assumed for the current six-layer 1.6 mm main and four-layer 1.0 mm carrier.

## Read-only carrier via-size audit

JLC's published quote guidance identifies the current 0.20 mm drill / 0.40 mm pad as a chargeable small-via combination; a multilayer 0.20 mm drill can avoid that surcharge with at least a 0.45 mm pad. That makes larger carrier pads a promising candidate. The exact quote selection and any consequential Kelvin/Tg155 charges must be rechecked after the revision; no cheaper drill option should be selected for files that still contain 0.20 mm holes. [JLC quote specification help](https://cart.jlcpcb.com/quote/?fromDemo=yes).

Read-only KiCad copper-shape calculations tested enlarging **all ten** carrier via pads from 0.40 to 0.45 mm, leaving the drill at 0.20 mm. Both pads' growth was included when checking via pairs. Three other-net via pairs would then violate the project's 0.15 mm clearance:

| Pair, coordinates in mm | Proposed copper clearance | Required |
|---|---:|---:|
| GND (58.0, 58.6) ↔ VBUS (58.2, 59.15) | 0.135235 mm | 0.150 mm |
| GND (58.0, 58.6) ↔ CC1 (57.4094, 58.6351) | 0.141641 mm | 0.150 mm |
| CC1 (59.45, 61.493) ↔ USB_DM (59.95, 61.2) | 0.129525 mm | 0.150 mm |

Thus a blanket diameter edit is **not ready for manufacture**. The required extra centre spacing is only about 0.008–0.021 mm for those pairs, suggesting local rerouting may be feasible, but some nearby tracks have little spare clearance. A proper revision must refill planes, run native DRC, check hole/solder-mask rules, regenerate fabrication files and obtain a fresh quote. No clearance rule should be relaxed to claim the saving.

This is a preliminary geometry audit, not a full DRC pass. Detailed results and the unchanged source hash are in `usb-via-045-readonly-analysis.json`. No PCB or manufacturing file was written or modified during it.

**Most defensible cost-down order:** keep the present quotation as a historical baseline; redesign the carrier around ordinary low-cost via rules; investigate the main's routing/package constraints and remove the need for expensive fine-via processing where practical; then compare the revised complete, assembled, UK-tax-paid jobs at JLCPCB and PCBWay. Only fresh quotations establish the final saving.
