# Native JLCONE B2 cost study —29 October2026

These are **unrouted, original49-SMT-component baseline** quotes, before the later BC1.2 additions/capacitor optimization. No PCB order, unpaid order, component purchase or payment was submitted. The saved draft labels explicitly say UNROUTED COST STUDY. Completed routed boards must be re-quoted.

Five6-layer bare PCBs with two bottom-side Economic assemblies cost **$102.27 in goods**: fabrication$49.93 and assembly$52.34. Both manual review options and factory depaneling are included. The49 component placements match16 BOM groups; owner LEDs and wire pads are excluded. Same-settings four-layer quote obtained by the root agent was$78.27, exactly$24 less in goods.

The6-layer fabrication breakdown is$32 base,$16.80 ENIG,$0.08 ENIG-area charge and$1.05 production-file review. Epoxy-filled and capped0.3mm vias add$0. There is no small-via fee. Earlier native figures around$33 used the platform's new **OSP default**, so are invalid for this ENIG comparison and are deliberately superseded. OSP also disabled Economic assembly; explicitly selecting ENIG restored Economic availability. An exploratory TG155 selection was restored to TG135 before saving. Switching from Standard to Economic reset the assembly face, which was corrected and verified as Bottom Side before BOM/CPL processing.

| Native6-layer checkout, before coupon | Goods | Payable shipping | JLC-collected UK VAT/tax | Total USD |
|---|---:|---:|---:|---:|
|Global Standard Direct Line,8–12 business days |102.27 |1.50 promotional rate (was5.90) |20.76 |**124.53** |
|DHL Express,2–4 business days |102.27 |18.00 promotional rate (was24.41) |24.06 |**144.33** |

The actual cart estimate accepts the claimed **$30 high-layer coupon** with$18 freight:102.27+18−30=$90.27. That cart subtotal excludes the checkout's VAT. The checkout expressly defers coupon application until the payment section after Submit Order, so no final discounted/VAT-recalculated payable quote was obtained. Do not deduct30 from the totals above and call the result a final price. The coupon requires freight above$5; whether the$1.50 direct-line promotion qualifies based on its original$5.90 fee remains unconfirmed. Only one promotional coupon applies per batch. No repeat-use or stacking claim is made.

Proof images contain only the summary card and were visually checked:

- [Cart showing coupon−30](native-6L-cart-coupon30.png).
- [Direct-line shipping and VAT](native-6L-directline-vat-before-coupon.png).
- [DHL shipping and VAT](native-6L-dhl-vat-before-coupon.png).

All exact amounts and caveats are in [native-6L-quote.json](native-6L-quote.json). Separate stock XIAO RP2040 Plus and Adafruit4090 purchases currently add about**£14.78 delivered for one set**, or£22.17 for two sets, based on official shop consumer shipping estimates; final checkout remains authoritative. See [retail shipping evidence](../../../../cost-down/module-shipping-quote.json).

For the process comparison, current JLC [via guidance](https://jlcpcb.com/help/article/pcb-via-covering) and [free POFV announcement](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv) support free resin filling/capping on6+ layers. Four-layer UI offered free **Plugged** rather than Tented; plugged-via guidance requires≥0.35mm clearance from adjacent soldermask openings, which can conflict with dense fanout. The four-layer price is a valid cost study, not proof that its process is suitable for the final routing. Six-layer filled/capped thermal vias can therefore have engineering value independent of a coupon.

Current [rigid-PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/) permit0.10mm tracks and spacing (multilayer nominal0.09mm). The [extra-charge schedule](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra) adds20% for4–8 layers using3.0–3.5mil traces/spacing. A0.1124mm neck is4.43mil and a0.10mm minimum is3.94mil, above that stated fee band. Also check the separate physical-hole clearances: PTH hole-to-track0.28mm, inner-layer PTH hole-to-copper0.30mm, via-hole-to-track0.20mm. These differ from pad-edge clearance rules.

Final tooling notes must preserve the88.4×17.3mm outline and all84 LED holes. If factory tooling needs rails, use removable external rails and the included depaneling service; do not add permanent internal holes or grow the finished board. Filled/capped-via instructions must distinguish0.3mm vias from the0.9mm LED solder holes.
