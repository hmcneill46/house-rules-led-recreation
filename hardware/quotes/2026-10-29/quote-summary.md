# JLCPCB quotation record — 29 October 2026

Status: **automated, review-only estimates, not a firm production quotation**. No order has been submitted and no payment has been made. Prices below were read from the logged-in JLCPCB website; JLCONE shipping/coupon comparisons are recorded separately in `../jlcpcb/jlcone-comparison.md`.

The current cart contains two jobs: five fabricated and five factory-assembled main boards, and five fabricated and five factory-assembled USB carrier boards. Nothing in the frozen `hardware/manufacturing/A1_review` package was changed.

## Requested quantities and practical minimums

JLCPCB's quoted minimum is five bare boards per design. With five bare boards, Economic assembly offered only **two or five assembled boards**. It did not offer one or three. Standard assembly accepted three, with larger temporary assembly panels and rail removal.

| Intended purchase | Actual economical quantity quoted |
|---|---|
| One finished display | Two assembled main boards and two assembled carriers, plus three unassembled boards of each design |
| Three finished displays | Five assembled main boards and five assembled carriers |

The owner's seven LED modules per display are excluded from factory assembly. The factory parts are 37 placements on each main board and seven on each carrier.

## Manufacturing configuration

| Item | Main | USB carrier |
|---|---|---|
| Finished size | 88.4 × 17.3 mm | 16.0 × 16.8 mm |
| Layers / thickness | Six / 1.6 mm | Four / 1.0 mm |
| Copper | 1 oz outer, 0.5 oz inner | 1 oz outer, 0.5 oz inner |
| Finish / colour | ENIG 1 µin / green | Lead-free HASL / green |
| Via process | Epoxy filled and copper capped, all 192 small vias; 84 LED PTH stay open | Plugged, ordinary through vias |
| Smallest via drill / pad | 0.2 / 0.4 mm | 0.2 / 0.4 mm |
| Assembly | Bottom, Economic | Top, Economic |

The 0.2 mm via option automatically required Tg155 and four-wire Kelvin testing. These charges were retained. No drill enlargement or geometry change was used to reduce the price. Optional deburring was removed. Ordinary bare-board flying-probe testing remained selected.

The quotation notes require removable tooling/rails when needed, no tooling holes within the finished outline, and removal of rails before delivery. JLCPCB must still confirm the assembly tooling arrangement and final dimensions during CAM review.

## Assembly part availability and the connector variant

The original carrier socket, **USB4105-GF-A / C3020560**, had zero assembly stock. Its pre-order estimate was 12 pieces minimum, £6.66, with the actual price quoted only after payment. That unpurchased inspection-only parts-cart entry was removed.

The quote instead uses **USB4105-GF-A-120 / C5184243**, which showed 2,090 pieces in stock. Engineering checked the manufacturer's family drawing: it retains the XY footprint, body and pin map and specifies 1.20 ±0.15 mm shell stakes. The 1.0 mm carrier and enclosure clear it. The alternate BOM and provenance are in `input/usb-bom-jlc-120-quote-only.csv` and `input/usb-120-quote-only-provenance.json`.

This is a **quote-only alternative**, not a released manufacturing BOM change. The final order package must explicitly adopt the checked variant before ordering. The shorter -060 variant was not selected.

The factory note expressly requires soldering **all four plated-through-hole shell anchors as well as the SMT contacts**. The automated quote has SMT and special-component fees but does not separately confirm the shell-anchor soldering process or labour. JLCPCB labels the assembly remark **“Quote after review”** and excludes its eventual price from the displayed total. This remains a material limitation of every carrier total below, including Standard assembly.

## Board and assembly subtotals

These are JLCPCB's GBP reference prices, before shipping, VAT and coupons. Actual checkout/payment currency is USD.

| Job | Bare PCB batch | Assembly / components | Displayed total | Additional exclusions |
|---|---:|---:|---:|---|
| Main, five bare / two assembled, Economic | £64.17 | £43.79 | **£107.96** | CAM/tooling review |
| Carrier, five bare / two assembled, Economic, -120 socket | £37.06 | £21.06 | **£58.12** | Shell-anchor review |
| Main, five bare / five assembled, Economic | £64.17 | £66.95 | **£131.12** | CAM/tooling review |
| Carrier, five bare / five assembled, Economic, -120 socket | £37.06 | £25.82 | **£62.88** | £2.48 depaneling listed separately; shell-anchor review |
| Main, five bare / three assembled, Standard | £65.49 | £67.89 | **£133.38** | Includes £1.99 rail removal; CAM review |
| Carrier, five bare / three assembled, Standard, -120 socket | £37.90 | £38.37 | **£76.27** | £1.99 depaneling listed separately; shell-anchor review |

Standard automatically quoted 88.4 × 71.3 mm temporary assembly dimensions for the main and 70.0 × 70.8 mm for the carrier. These are not a change to the finished board outline. Standard three-of-each costs more than Economic five-of-each even before shipping.

The carrier's temporary £59.13 five-board OSP quote was superseded by the £62.88 lead-free HASL quote. Use the latter for comparisons.

## Combined DHL Express DDP checkout estimates

The saved UK destination was used. Delivery is quoted at 2–4 business days after production. These figures include the displayed import-tax collection and duty/tax disbursement charge, **but exclude the post-review carrier charges described above**. Discounts were not yet applied in the checkout.

| Actual assembled quantity, each design | Goods | Shipping | Customs duties & taxes | Disbursement | Displayed USD total |
|---|---:|---:|---:|---:|---:|
| Two main + two carriers | $221.56 | $25.36 | $49.39 | $8.27 | **$304.58** |
| Five main + five carriers | $258.80 | $25.66 | $56.90 | $8.27 | **$349.63** |

The displayed tax corresponds to approximately 20% of goods plus freight. Do not describe these as final factory-approved totals or deduct a coupon without verifying its actual checkout application. JLCONE offers a cheaper split-shipment pilot option; see the separate app comparison before choosing delivery.

The independently verified JLCONE alternative was two separate Global Standard Direct Line shipments for the pilot: main $174.63 including $1.50 promotional freight and $29.11 VAT; carrier $94.85 including $1.50 promotional freight and $15.81 VAT; combined **$269.48 before coupons and review extras**. For five of each, splitting main DDP $248.17 and carrier Direct Line $102.46 produced **$350.63**, slightly above combined DDP $349.63 before coupons. The applicability of the $1.50 promotion to repeated orders and the final coupon/tax calculation remain to be confirmed. These are actual quoted shipment combinations, not a request to alter customs declarations.

Screenshots `evidence/pilot-2-each-ddp-summary.jpg` and `evidence/five-each-ddp-summary.jpg` show all line items and the selected DDP service. The address and phone are outside those screenshots. Corresponding text evidence is alongside them.

## Coupons and review before payment

The website cart initially offered a $10-equivalent coupon preview. The JLCONE investigation subsequently obtained an account-specific $30 high-layer PCB coupon. Cart eligibility and a final discount applied to an order are different stages; see `../jlcpcb/jlcone-comparison.md` for the verified account details and split-shipment comparisons. No creator code was assumed valid and no discounts were stacked speculatively.

JLCPCB's [Review Before Payment service](https://jlcpcb.com/help/article/review-before-payment-service-for-pcba-orders), updated 23 September 2026, can review advanced options before payment. It requires selecting that service and submitting an unpaid order. The factory then updates the amount due and reserves components for up to seven days. This route can resolve the anchor/tooling charges without paying first. It has not been submitted as part of this quotation record.

## Checks and remaining release requirements

- Final saved main job: 14 BOM rows, 37 placements, all selected; exact MPN/LCSC matches retained after the quantity update. Machine-readable evidence is `evidence/main-final-five-bom-matches.json`.
- Carrier quote: six distinct BOM identities and seven placements, with the checked -120 socket as the sole substitution. All parts were available when quoted.
- Final saved carrier readback also passed: all six rows/seven placements selected. `evidence/final-bom-audit.json` records an exact comparison of every selected main/carrier MPN, LCSC code and footprint against the quote-input CSVs. The carrier's -120 BOM was the expected comparison source.
- The manufacturer's feeder-zero orientation and final placement/polarity still require final DFM review before production; preview dots alone are not a pin-one guarantee.
- Physical seven-module fit remains an existing project release requirement. Quoting does not constitute fit approval.
- Confirm all four USB shell anchors factory soldered, any resulting labour/stencil charges, rail removal and final finished outlines before accepting a firm price.
- No owner LED modules, connecting cable, power supply, case printing or import charges beyond the quoted service are added silently.

The cart is for review only. No Submit Order, payment or manufacturing release was performed.

## Browser handoff and quote references

`browser-handoff.json` preserves the authenticated account's current job links and the earlier checkout estimate links. The account must be signed in to use them. The primary restart point is the [JLCPCB cart](https://cart.jlcpcb.com/shopcart/cart).

| Scenario | Main cart / assembly reference | Carrier cart / assembly reference |
|---|---|---|
| Current five assembled each | Y4-13966379A / SMT026102963533-13966379A | Y5-13966379A / SMT026102963539-13966379A |
| Historical two assembled each | Y2-13966379A / SMT026102963396-13966379A | Y3-13966379A / SMT026102963462-13966379A |

The two-assembled cart jobs were edited into the current five-assembled jobs. The preserved two-assembled checkout URL is evidence of the earlier estimate, **not a verified current orderable basket**. Recreate or edit the two-assembled jobs and re-check them before submitting that alternative for review. Preserve the five-assembled alternative separately if requesting factory review of both. The final readback audit opened unsaved edit views only; it did not save another price/configuration change to the cart.
