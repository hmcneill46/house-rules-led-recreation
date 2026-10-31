# UK retail parts and supplies — B2 / F12.875 mm

Checked 31 October 2026. All summary amounts below include a UK-mainland delivery allowance and VAT. No order or payment was submitted. **Add the separate JLCPCB quote for the custom main boards and their factory assembly** to these totals.

| Complete displays | Retail parts, power and consumables | If none of the listed assembly tools are owned |
|---|---:|---:|
| 2 | £91.45 | £125.25 |
| 3 | £111.04 | £144.84 |
| 5 | £180.21 | £214.01 |

These are purchase totals, with whole tubes, metre lengths and packs counted. The five-display total includes **14 additional LED modules**, because the owner has 21. The owner's printer, multimeter and grey Hyper PLA have no new purchase cost in this quote. Printer electricity and payment-provider/foreign-currency fees are not retailer goods; any applicable JLC payment fee belongs in the parent quote.

## What is included

| Purchase | 2 displays | 3 displays | 5 displays |
|---|---:|---:|---:|
| [Exact headerless XIAO RP2040 Plus, SKU 100059977](https://www.unmannedtechshop.co.uk/products/seeed-studio-xiao-rp2040-plus), £4.49 each | 2 | 3 | 5 |
| [Adafruit 4090 downstream USB-C breakout](https://thepihut.com/products/adafruit-usb-c-breakout-board-downstream-connection-ada4090), £2.90 each | 2 | 3 | 5 |
| [Official Raspberry Pi 15 W UK PSU](https://thepihut.com/products/raspberry-pi-psu-uk), white SC0443, £7.70 each | 2 | 3 | 5 |
| [50 cm USB-C to USB-C data cable](https://thepihut.com/products/usb-c-to-usb-c-cable-1m), £2.50 | 1 shared | 1 shared | 1 shared |
| [28 AWG stranded PTFE wire](https://thesaberarmory.com/products/28awg-ptfe-bs-spec-hook-up-wire-1-metre-lengths), £1.80/m with VAT | 1 m red + 1 m black + 2 m blue | 1 m red + 1 m black + 3 m blue | 1 m red + 1 m black + 5 m blue |
| [M2 ISO 7380-1 button screws](https://boltbase.com/products/m2-self-colour-10-9-high-tensile-socket-button-head-screws-iso-7380-1), £0.90 each before any successful bulk offer | 4 × 6 mm, 2 × 8 mm | 6 × 6 mm, 3 × 8 mm | 10 × 6 mm, 5 × 8 mm |
| [Antex lead-free solder, 0.8 mm, 4 m](https://thepihut.com/products/antex-lead-free-solder), £4.40 | 1 tube | 1 tube | 1 tube |
| [Future 315 no-clean flux pen](https://thepihut.com/products/flux-pen-future-315-low-residue-no-clean), £7.80 | 1 pen | 1 pen | 1 pen |
| [Chip Quik EGS10W-20G electronics-grade silicone](https://uk.farnell.com/chip-quik/egs10w-20g/silicone-adhesive-electronics/dp/4715839), £6.05 with VAT | 1 tube | 1 tube | 1 tube |
| [100 × 2.5 mm cable ties, pack of 100](https://uk.farnell.com/pro-power/0301cv-100w/cable-tie-100mm-pa66-pk100-black/dp/1366999), £1.64 conservative allowance with VAT | 1 pack | 1 pack | 1 pack |
| [Extra raw LED modules](https://www.switchelectronics.co.uk/products/red-5-x-7-dot-matrix-led-display-17-8x12-7mm), £1.80 each with VAT | 0 | 0 | 14 |

The PSU is a **5.1 V, 3 A UK wall supply with its own captive 1.5 m USB-C lead**. It does not require a separate power cable per display. One PSU per completed unit lets every unit run independently; the data cable is shared for programming. The current hardware uses 5 V USB power without requesting a higher PD voltage. On receipt, check the actual plug fits the printed opening and confirm the expected USB current detection during bring-up.

The wire is genuinely stranded (7/0.120 mm), with a specified maximum outside diameter of **0.71 mm**. It fits the existing cable-space contract and keeps 28 AWG for power and ground. Common low-cost 28 AWG silicone wire with 1.2 mm outside diameter was rejected. Allow about 14 × 70 mm MCU wires plus 6 × 45 mm USB wires per display before trimming; the purchased colour lengths cover these and leave a modest spare allowance. Keep the short D+/D− pair together and twisted as the assembly guide specifies.

The screws need heads within the existing **4.0 mm diameter / 1.5 mm height envelope**. The specified M2 button screws use a 1.3 mm hex key. Generic M2 DIN 7985 pan heads can be 1.6 mm high and were not substituted. The in-stock Pi Hut 180 mm cable ties are 4.6 mm wide and would not fit the 2.7 mm tie passage, so the 2.5 mm Farnell ties are used instead.

The adhesive is a small, flexible electronics-grade bead for the main PCB, as described in the assembly guide. The MCU has its printed retention cap. Avoid substituting an ordinary acetic-cure bathroom silicone or potting the entire assembly. The quoted tube and solder/flux are shared batch purchases; actual usage depends on practice and waste.

## Delivered retailer baskets

| Retailer | 2 displays | 3 displays | 5 displays | Evidence and delivery |
|---|---:|---:|---:|---|
| Unmanned Tech | £12.57 | £17.06 | £26.04 | Fresh anonymous quantity carts; £3.59 Standard shipping; goods explicitly tax included |
| The Pi Hut | £39.70 | £50.30 | £71.50 | Fresh combined carts: USB boards, PSUs, shared data cable, solder and flux; £3.80 Royal Mail tracked shipping |
| The Saber Armory | £11.40 | £13.20 | £16.80 | Fresh wire carts; goods VAT verified in an anonymous UK checkout; £3.50 shipping budgeted as £4.20 with VAT |
| Bolt Base | £9.30 | £12.00 | £17.40 | Exact screw quantity carts, £3.90 Tracked 48 shipping; no discount actually applied |
| Farnell | £18.48 | £18.48 | £18.48 | Adhesive + tie pack; primary catalogue and [£8.99 ex-VAT delivery policy](https://uk.farnell.com/help/delivery-information) |
| Switch Electronics | — | — | £29.99 | 14 LEDs; goods VAT verified in anonymous UK checkout; £3.99 shipping budgeted as £4.79 with VAT |
| **Total excluding custom PCB** | **£91.45** | **£111.04** | **£180.21** | |

**Price certainty:** UMT, Pi Hut and screw totals use exact live cart quantities and the merchant's shipping-rate endpoint. Saber and Switch goods VAT were verified: £6 wire becomes £7.20 and £21 LEDs becomes £25.20 before shipping. The shipping VAT on those two baskets is a conservative 20% allowance; final address checkout was not completed. Farnell is a catalogue-and-delivery budget rather than a locked checkout quote: its individual tie page showed £1.37 ex VAT while a newer category showed £0.683. The higher figure was retained, so a confirmed lower tie price could save approximately £0.82. The adhesive page showed 15 tubes in stock and the tie page 258 packs. Direct unauthenticated HTTP access to Farnell was blocked, so stock/price there comes from the primary pages returned by web browsing.

Screw quantity promotions were investigated, but the actual carts returned **zero discount** even with the merchant's published native offer metadata. None is deducted. The Switch voucher found required spending over £100, so buying extra goods to unlock it was not sensible. No newsletter signup or promotional subscription was created.

## Assembly tools, only if needed

Do not buy these again if equivalent tools can be borrowed or are already owned.

| Tool | Price including VAT | Delivery treatment |
|---|---:|---|
| [YIHUA 928D-I 65 W digital iron, fitted UK mains plug](https://kunkune.co.uk/shop/soldering-iron-kits/yihua-928d-i-soldering-iron-65w-uk-plug/) | £16.90 | £2.90 Standard, current published rate |
| [Iron stand](https://thepihut.com/products/soldering-iron-bench-stand) | £4.00 | Add to existing Pi Hut basket |
| [20–30 AWG wire strippers](https://thepihut.com/products/wire-strippers) | £6.00 | Add to existing Pi Hut basket |
| [Precision diagonal cutters](https://thepihut.com/products/precision-diagonal-cutters) | £3.50 | Add to existing Pi Hut basket |
| [1.3 mm hex key](https://boltbase.com/products/1-3mm-metric-short-arm-hex-keys-din-911) | £0.50 | Add to existing Bolt Base basket |
| **Additional tool budget** | **£33.80 delivered** | One shared set for any batch |

The iron's current live structured product data says **InStock**, £16.90 and VAT included. A cheaper £14.90 kit and the £32.50 926LED-IV station appeared in cached searches but were out of stock in their live product data, so they were excluded. The selected iron includes temperature regulation in the handle and a UK plug; it does not need another USB-PD power supply. Existing eye protection, a heat-safe work surface and ventilation should be used for soldering. The existing alignment jig and removable 3 mm spacer rails can use the already-owned filament; no purchased spacer kit is included. A suitable fine-tip driver/pliers may already be in the owner's printer tools; no additional mechanical tool kit is presumed necessary.

## Files and limitations

- `retail-quote-summary.json`: item links, whole purchase quantities, gross/net calculations and batch totals.
- `live-complete-pihut-shipping.json`: exact combined Pi Hut baskets.
- `live-module-shipping.json`, `live-wire-shipping.json`, `live-screw-shipping.json`: separate live quantity/rate evidence.
- `live-screw-published-bulk-discount.json`: the unsuccessful actual-cart discount check.
- `optional-tool-iron-live.json`: live iron availability/price evidence.
- `live-pihut-with-optional-tools-shipping.json`: confirms adding the stand, stripper and cutters keeps Pi Hut shipping at £3.80 for all three batch sizes.
- `tax-evidence.json`: concise tax evidence without account/address/session data.
- `live-products-2026-10-31.json`: wider product research, including rejected/out-of-stock alternatives.

Factory assembly covers the small components on the custom main board. The owner still fits the seven LED modules, solders the 20-wire loom and assembles the case: approximately **84 LED joints + 40 wire joints per display**, then inspection, electrical checks and firmware loading. Purchased stock modules and the actual USB plug still need the receipt checks in the existing assembly guide. This retail research does not change the design, order any goods, or certify the prototype before hardware testing.
