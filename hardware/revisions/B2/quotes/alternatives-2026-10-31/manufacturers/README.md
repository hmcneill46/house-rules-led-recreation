# Unchanged-board manufacturer comparison — 31 October 2026

**PCBWay and NextPCB Standard Turnkey are the strongest two alternatives to obtain a real quotation from. Neither is verified cheaper than JLCPCB for this exact board.** Their generic assembly promotions are not landed prices for the finished 55-component board. The initial research was followed by anonymous calculator checks. The public manufacturing package was uploaded to NextPCB for pricing only; its exact BOM matched 18/18. No account was created and no order/payment submitted. Owner-authorised contact attempts are recorded separately below.

The reference is the confirmed-F B2 board: 89.45 × 17.30 × 1.6 mm, six layers, ENIG, green, 55 bottom SMT parts in 18 BOM groups, including four TLC59282RGER QFNs. It also requires 276 ordinary 0.30 mm vias resin filled and copper capped, while 84 × 0.90 mm LED PTH remain open. Removable external rails must be removed before delivery.

| Manufacturer/service | Unchanged-design feasibility | Quote/pricing evidence | Priority |
| --- | --- | --- | --- |
| **PCBWay turnkey** | Six layers, ENIG and resin fill/cap are offered. Sources from DigiKey/Mouser/etc. Small via annuli need explicit CAM acceptance. | Public calculator gives tooling/stencil/labor only; components and special-process surcharges require review. Homepage advertises assembly **from $29 for 1–20 pieces**, not the full product. Exact RGER stock/price and UK landed total unverified. | **Quote first** |
| **NextPCB Standard Turnkey** | Advanced capability explicitly supports via-in-pad fill/cap. Standard sourcing accepts global distributors. Standard assembly starts at one board. Tight vias need CAM review. | Public 2026 offer advertises automatic up-to-$200 SMT discount for 1–10 turnkey boards with a $50 minimum; exact eligible charges/total require the quote. | **Quote alongside PCBWay** |
| **PCBGOGO turnkey** | ≥1 assembled board, FR4, QFN assembly and resin-filled vias are offered; full copper cap and tight-ring geometry need confirmation. | Instant assembly estimate explicitly excludes PCB fabrication and components; accurate quotation requires files/review. | Reserve third option |
| **Seeed Fusion Advanced** | Advanced service supports POFV and six layers; published via annulus of 4 mil exceeds this board's 0.075 mm tight vias. Cannot assume unchanged acceptance. | One assembled board possible from five fabricated; external MPN sourcing and pricing review supported. Standard cheap PCB service does not include POFV. | Lower priority for unchanged design |
| **Elecrow turnkey/premium** | MOQ one assembled board; QFN and global sourcing including Mouser/DigiKey supported. Exact filled/capped process, six-layer rules and tight vias need project-manager acceptance. | Public assembly estimator is reference only; final itemised quote is issued by a project manager. $1 service listing is a placeholder, not complete assembly price. | Reserve option |

## Actual anonymous calculator comparison

The [live calculator record](live-calculator-results.json) contains these **estimates, not final landed quotations**:

| Calculator, correct 4/4 mil routing option | 5 fabricated / 2 assembled | 5 fabricated / 5 assembled | Still missing or unapproved |
| --- | ---: | ---: | --- |
| PCBWay | **$602.40** | **$602.40** | All components, VAT, manual process/CAM review; UI inner copper is 1 oz while actual requirement is 0.5 oz |
| NextPCB Standard | **$179.23** | **$214.51** | UK shipping/VAT, final CAM acceptance of 0.075 mm annulus, external rails/depanel and rotation review |

PCBWay displays $573.40 fabrication + $29 promoted assembly, with $27.37 UK FedEx-FICP delivery cancelled by an equal displayed shipping discount. This is already substantially higher than the JLC budget before PCBWay adds parts or VAT. Four-mil routing was explicitly selected and verified; an initial overconservative three-mil selection gave the same price. Its global full-via fill/cap option is selected, while the notes require the LED holes to remain open. No file-specific manufacture approval is implied. A requested manual quote could differ, so the calculator is not a guaranteed minimum charge.

NextPCB matched all 18 exact BOM groups, including TLC59282RGER, after accepting the review Gerber, native CPL ZIP and a column-only conversion of the exact BOM. Its fabrication estimate is $96.33. For two, BOM is $32.90 and promoted SMT is $50 (a displayed $131.22 reduction from $181.22). For five, BOM is $53.19 and SMT is $64.99 (a $200 reduction from $264.99). The driver has a listed 7–18 working-day sourcing lead, with zero overage shown for 8/20 installed chips. Production estimate is 14–27 working days. The UI rounds the quoted length to 89.5 mm; the exact Gerber and review note retain 89.45 mm.

NextPCB’s Add to Cart button opens a login dialog, so shipping could not be priced without an account. No account or unpaid order was created. These goods estimates are higher than the JLC comparison even before adding UK delivery/VAT; they do not establish a cheaper unchanged-board route.

[PCBWay two-board evidence](evidence/pcbway-two-4mil-INCOMPLETE-estimate.jpg), [five-board evidence](evidence/pcbway-five-4mil-INCOMPLETE-estimate.jpg), [NextPCB two-board evidence](evidence/nextpcb-two-matched-estimate.jpg), [five-board evidence](evidence/nextpcb-five-matched-estimate.jpg). Screenshots contain no owner contact or delivery information.

## The portability issue to resolve first

There are 109 escape vias with a nominal 0.30 mm drill and 0.45 mm pad, giving a **0.075 mm annulus**. PCBWay's published advanced minimum is **3 mil = 0.0762 mm**; its ordinary process is less permissive. NextPCB's published standard 1 oz minimum is **3.5 mil ≈ 0.09 mm**. Seeed Advanced lists **4 mil**. This does not establish rejection: a factory might accept metric rounding or a different process after CAM review. It does establish that this JLC-qualified Gerber set cannot automatically be sold as compatible with every competitor's standard service.

An unchanged-design RFQ must state those exact dimensions and request written acceptance without silently enlarging pads, reducing holes, changing clearances or leaving vias unfilled. The CAD is not being changed merely to obtain a lower advertised estimate.

NextPCB's **Rev 0** promotion is unsuitable for this unchanged job: its published minimum board is 50 × 50 mm, five or ten assembled, HQ Online inventory only, and special processes outside its scope. The current board is 17.30 mm wide and needs fill/cap plus review. Standard Turnkey is the appropriate path. The service overview has inconsistent generic FAQ turnaround/quantity text; the specific Rev 0 article and current quote should govern.

## Comparing a real offer fairly

For two assembled boards plus three bare spares, the existing JLC route is modeled at **£103.67 landed for custom boards/assembly/driver sourcing** before unverified coupons. For five assembled mains it is modeled at **£128.48**. These are provisional reference budgets, not final payable JLC prices. Retail controllers, USB breakouts, wire and screws remain the same whichever factory supplies the custom board; they must not be counted again or omitted to make a competitor look cheaper.

Ask each factory for exact RGER procurement including attrition/MOQ; fabrication; stencil/tooling; all 55 placements; QFN/hidden-pad inspection; filled/capped vias; external panel rails; depanel; shipping to UK mainland; VAT/duties and courier clearance fees; and lead time/quote validity. Accept no unsanctioned driver substitution. One populated board may be possible at some competitors, but comparisons requested here use two and five assembled to match the existing budgets.

PCBWay's current terms exclude customs/VAT/brokerage by default unless checkout or a written tax-inclusive service specifies otherwise. NextPCB price/terms pages likewise exclude shipping/tariffs and require checking VAT. A shipping-inclusive calculator total alone is therefore not a UK landed price. No universal courier fee or tax-inclusive shipping amount was invented in this research.

## Primary sources

- PCBWay: [assembly calculator and special processes](https://www.pcbway.com/quotesmt.aspx), [sourcing](https://www.pcbway.com/pcb_prototype/Electronic_Components.html), [FAQ](https://www.pcbway.com/assembly-faq.html), [advanced rules](https://www.pcbway.com/advanced-pcb-capabilities.html), [current terms](https://m.pcbway.com/terms-service.html), [shipping](https://www.pcbway.com/helpcenter/delivery/International_Order___Shipping_Information.html), [from-$29 promotion](https://www.pcbway.com/).
- NextPCB: [standard turnkey and sourcing](https://www.nextpcb.com/pcb-assembly-services), [advanced fill/cap](https://www.nextpcb.com/advanced-pcb-manufacturing-capabilities), [standard rings](https://www.nextpcb.com/pcb-capabilities), [2026 offer](https://www.nextpcb.com/blog/nextpcb-discount), [Rev 0 limits](https://www.nextpcb.com/blog/what-is-nextpcb-rev0-pcba-service), [prices](https://www.nextpcb.com/prices), [terms](https://www.nextpcb.com/terms-of-service).
- PCBGOGO: [quote limitations](https://www.pcbgogo.com/pcba-quote.html), [assembly capabilities and MOQ](https://www.pcbgogo.com/capabilities/pcba-capabilities.html).
- Seeed: [current service guide/MOQ](https://wiki.seeedstudio.com/Service_for_Fusion_PCB/), [advanced vs standard/POFV](https://support.seeed.cc/portal/en/kb/articles/what-is-the-difference-between-fusion-standard-pcb-and-fusion-advanced-pcb), [advanced rules](https://support.seeed.cc/portal/en/kb/articles/fusion-advanced-pcb-specification).
- Elecrow: [assembly sourcing/MOQ/quote breakdown](https://www.elecrow.com/maker/assembly/index).

The two full RFQ drafts in this folder remain the review copies. The owner subsequently authorised enquiries: PCBWay is prepared awaiting CAPTCHA handoff; NextPCB’s contact form returned a submission failure, so neither supplier has confirmed receipt yet. See [enquiry status](enquiry-status.json). They contain no owner's address, phone, email or precise postcode. A final factory quote would need the delivery details privately and must be reviewed before ordering.
# Final contact decision

After the calculator results, the owner limited sending supplier emails to cases with a realistic chance of being price competitive with JLC. Neither current competitor estimate meets that condition, so the prepared Mail drafts remain **unsent**. PCBWay's form stopped at CAPTCHA; NextPCB's earlier authorised contact attempt failed/reset, with no confirmed receipt. The public calculator work and unchanged-board CAM questions below are retained for comparison.
