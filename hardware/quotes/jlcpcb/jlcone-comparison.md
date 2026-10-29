# JLCONE desktop comparison — 29 October 2026

Status: installed successfully; user signed in; two- and five-assembled-each scenarios inspected without submitting an order. Final coupon/tax application remains beyond Submit Order.

- Installed `/Applications/JLCONE.app`, version 1.0.72, Intel x64.
- Official download page: <https://jlcone.com/download> (the bare domain returned an empty/404 response).
- Used the vendor DMG listed by Homebrew's official cask API: <https://rs.jlcone.com/static/APP/app_version/jlcone-1.0.72-x64.dmg>.
- DMG saved at `/Users/harrymcneill/Downloads/jlcone-1.0.72-x64.dmg`.
- SHA-256 matched the Homebrew manifest: `97d6d45c92d8669f81d128f3b3749c27e6d1dfc5896647e03d8825d8ecea51ae`.
- `codesign --verify --deep --strict` passed. `spctl --assess` accepted the app with `source=Notarized Developer ID`. No security warning bypass or security-setting changes were used.
- Initial Homebrew install failed because the existing `/usr/local/share/man/man8` directory was not writable. No ownership/permission repair was attempted; the vendor DMG was installed directly instead.
- Native app launched into JLCPCB Account sign-in. It did not inherit the website login. The user subsequently signed in; no credentials were read or entered by this task.
- No terms were accepted and no orders, payments or account registrations were submitted.

See `discount-research.md` for published promotions. Actual coupon savings, instant discount, shipping, VAT and final payable amount still require the logged-in app checkout and identical board specifications. A published promotion is not a confirmed cart saving. JLCPCB states that GBP display amounts are for reference and payment is in USD; preserve the actual USD amount when comparing payment totals, and treat a bank/card conversion as separate from the manufacturer's quote.

## Actual app: two assembled of each board

Both existing jobs appeared in the app account cart. Each job includes five fabricated PCBs, with two assembled. No fabrication or assembly options were changed by this comparison task.

| Item | USD |
| --- | ---: |
| Main fabrication | 85.60 |
| Main Economic assembly, two units | 58.42 |
| USB fabrication | 49.44 |
| USB Economic assembly, two units | 28.10 |
| Merchandise total | **221.56** |

The UK checkout offered ordinary CPT routes, Global Standard Direct Line, **DHL Express (DDP)**, and own-account freight. CPT expressly says destination duty, tax and carrier handling fees are additional. The observed prepaid option was:

| DHL Express DDP, two assembled each | USD |
| --- | ---: |
| Merchandise | 221.56 |
| Shipping | 25.36 |
| Customs duties and taxes | 49.39 |
| Duty and Tax Disbursement Fee | 8.27 |
| **Grand total before coupon and instant discount** | **304.58** |

The last page offered **Submit Order**, with “Apply coupons in the payment section” and JLCONE Exclusive Discount still `--`. We stopped before submitting. Consequently $304.58 is a real prepaid-tax checkout quote **before discounts**, not the final discounted payable total. Selecting “Review Before Payment” would still submit an order, so was not used.

## Actual account coupons found and claimed

The logged-in desktop coupon centre revealed a better offer than the search-indexed $20 candidate:

- **JLCONE High-Layer PCB $30**: expressly includes **six layers**; order over $5 excluding freight; shipping over $5; selected regions; expires **27 December 2026**. Claimed successfully, confirmed in the unused-coupon wallet.
- **JLCONE PCBA $20**: order over $100 excluding freight; expires **27 November 2026**. Claimed and visible in wallet; applicability is not established for the assembly subtotal alone.
- Account also has new-user $10 SMT, $6 PCB and $10 shipping coupons. Only one promotional coupon may be used in the batch.
- The advertised JLCONE $20 PCB banner actually requires an order over **$500**. It is unsuitable here. The $15 batch coupon requires over $1,000.

After refreshing the unchanged two-each cart, its live estimate expressly showed **Coupons −$30.00**, merchandise $221.56, shipping estimate $18.00, subtotal **$209.56**. This confirms the $30 coupon is eligible in the app cart estimate. That estimate does **not** contain prepaid import tax or the DDP fee and must not be represented as the delivered total. Taxes may change after the coupon is actually applied; do not simply subtract $30 from the DDP figure and call it a final quote. The random app discount remains unconfirmed.

Evidence with no delivery address visible:

- `jlcone-coupon-wallet-2026-10-29.png`
- `jlcone-coupon30-terms-2026-10-29.png`
- `jlcone-2-each-cart-coupon30-2026-10-29.png`

## UK VAT, import handling and coupon effects

Checked official sources on 29 October 2026. JLCPCB's [Customs, Duties and Taxes guide](https://jlcpcb.com/help/article/customs,-duties-and-taxes), updated 9 September 2026, says it collects personal-customer UK VAT for goods at or below £135; above that, local customs normally collects it. Its [shipping guide](https://jlcpcb.com/help/article/shipping-methods-and-delivery-time) warns that freight alone normally excludes import charges. The actual UK DDP checkout above is the relevant prepaid option for this cart; US- or EU-specific DDP articles do not establish UK coverage.

[HMRC's overseas-sales guidance](https://www.gov.uk/guidance/vat-and-overseas-goods-sold-directly-to-customers-in-the-uk) bases the £135 limit on the total consignment's intrinsic goods value, excluding separately stated transport, insurance and identifiable taxes. It applies to the parcel, not to each board. Above that threshold, normal import VAT/customs rules apply. For ordinary imports, [GOV.UK consumer guidance](https://www.gov.uk/goods-sent-from-abroad/tax-and-duty) says the courier can collect VAT, duty and delivery charges; the VAT base includes goods, postage, packaging, insurance and any duty. The [standard VAT rate](https://www.gov.uk/vat-rates) is 20%; duty depends on the product's classification and origin, so no independent zero-duty claim is made for assembled boards.

[HMRC's current transaction-value guidance](https://www.gov.uk/guidance/customs-valuation/method-1-transaction-value) recognises qualifying pre-import discounts, subject to the sale and invoice conditions. A coupon's allocation between goods, assembly or freight and the manufacturer's declared value can affect the tax calculation; the final JLC invoice/payment calculation is needed. Do not change the customs value manually or split/devalue declarations artificially.

A CPT price is therefore a manufacturer's payment plus later import charges, not a guaranteed delivered price. A DDP comparison should retain all four visible cost components and the final discount/tax calculation. No additional assumed courier fee should be added to the already quoted DDP disbursement fee without evidence.

## Separate shipments and five-each comparison

These are **observed pre-coupon, pre-instant-discount app quotes**, using the existing jobs individually or together. No orders were submitted. Each board type still has five fabricated boards. The quoting task maintains the USB depanel/anchor caveats; those review adjustments are not silently included in these figures.

| Assembled quantity | Shipment | Merchandise | Shipping | Tax | Disbursement | Total USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Two main | Global Standard Direct Line, UK-VAT | 144.02 | 1.50 | 29.11 | — | **174.63** |
| Two main | DHL Express, UK-VAT, initial checkout | 144.02 | 18.00 | 32.41 | — | **194.43** |
| Two USB | Global Standard Direct Line, UK-VAT | 77.54 | 1.50 | 15.81 | — | **94.85** |
| Five of each, together | DHL Express DDP | 258.80 | 25.66 | 56.90 | 8.27 | **349.63** |
| Five main | DHL Express DDP | 174.92 | 24.99 | 39.99 | 8.27 | **248.17** |
| Five USB | Global Standard Direct Line, UK-VAT | 83.88 | 1.50 | 17.08 | — | **102.46** |

The app displayed direct-line shipping reductions from $6.52 to $1.50 for two main, $5.43 to $1.50 for two USB, and $5.48 to $1.50 for five USB. Each individual quote showed that price; **the permitted number of promotional uses has not been established**. Do not guarantee two discounted shipments merely because both preview independently at $1.50. The visible route Details popup provided delivery performance, not the shipping promotion's use limits, and no primary-source term establishing repeated eligibility was found.

Before coupons, two separate direct-line previews total $269.48, compared with $304.58 together by DDP. Five separate previews total $350.63, compared with $349.63 together. These sums assume the previewed shipping rate remains available for each actual order; they are comparisons, not a confirmed two-order final payment.

For using the strongest coupon without relying on its unknown interaction with $1.50 freight, a practical candidate is **main by DHL (freight above $5), USB separately by direct line**. It permits testing the $30 main-board coupon and the independent new-user $10 SMT coupon for USB, with only one $1.50 shipment. For two-each, this route's observed total before coupons is $289.28; for five-each it is $350.63. It may beat a combined order after coupons, but final coupon allocation, tax recomputation and the unconfirmed automatic app discount must be read on the payment calculation. Each coupon is single use: the alternative two- and five-each scenarios cannot both consume the same $30 coupon.

The $30 coupon specifically requires freight above $5. The direct-line **paid** price is $1.50, although the original displayed main freight was $6.52. Therefore it is not established that the coupon remains eligible on that cheap route. The main-five checkout itself used CPT/DDP treatment rather than UK-VAT, despite the website's reference GBP merchandise display being below £135; use the actual checkout's tax treatment and final USD invoice, not a guessed currency conversion.

Privacy-safe summary evidence, cropped from native screenshots and visually checked:

- `jlcone-2-each-ddp-summary-2026-10-29.png`
- `jlcone-2-main-directline-summary-2026-10-29.png`
- `jlcone-2-usb-directline-summary-2026-10-29.png`
- `jlcone-5-each-ddp-summary-2026-10-29.png`
- `jlcone-5-main-ddp-summary-2026-10-29.png`
- `jlcone-5-usb-directline-summary-2026-10-29.png`

Some cart coupon rows can transiently retain a previous selection's amount while recalculating after switching jobs. Treat those live estimates as provisional and allow calculation to finish. The confirmed $30 claimed-wallet offer and its actual six-layer/freight conditions are stronger evidence than a transient cart number.
