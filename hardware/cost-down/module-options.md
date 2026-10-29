# Stock MCU and USB modules for a lower-cost revision

**Implementation update:** these modules are now used by the routed [B2 design](../revisions/B2/README.md). B2 retains six layers with ordinary 0.30 mm vias, adds a BQ24392 BC1.2 detector, and has a completed printed cradle/cover design. Its current wiring, source policy, cost and remaining physical checks supersede the early feasibility sketches below. This page preserves the module research that informed that choice.

Research checked 29 October 2026. This is a recommendation for a new cost-down revision, not a substitution into the frozen A1 manufacturing files. The existing LED mounting outline, seven-module arrangement and LED pin positions can be retained. No existing CAD, BOM or manufacturing output was changed by this research.

**Recommended: Seeed XIAO RP2040 Plus plus Adafruit 4090 USB-C breakout, with the LED drivers on one simpler custom mounting PCB.** The MCU and USB parts cost £7.39 per display at the checked UK retailers, or £22.17 for three, including VAT and excluding delivery. This replaces the custom USB assembly and bare MCU circuitry. It does not eliminate LED drivers or imply that a passive mounting board alone can drive the LEDs.

## MCU shortlist

| Module | Manufacturer envelope / resources | Price and UK availability checked | Fit and practical decision |
| --- | --- | --- | --- |
| **Seeed XIAO RP2040 Plus**, SKU100059977 |21 ×17.8 mm nominal;2 MB flash,264 KB SRAM;26 digital GPIO;3.3 V I/O;USB-C,BOOT/RESET;dedicated D+/D− solder pads |**£4.49 incl VAT**, available for purchase at [Unmanned Tech](https://www.unmannedtechshop.co.uk/products/seeed-studio-xiao-rp2040-plus);manufacturer lists$4.90 |Best candidate. Fit its21 mm axis along the88.4 mm display width, with its own USB socket facing internally sideways. Wire the external bottom USB to its data pads. Headerless version avoids unnecessary stack height. |
| Seeed XIAO RP2040, SKU102010428 |Same nominal21 ×17.8 mm family envelope;2 MB flash,264 KB SRAM;11 digital GPIO;3.3 V I/O;native USB |**£3.90 incl VAT**, [Pi Hut](https://thepihut.com/products/seeed-xiao-rp2040), shown available |Enough computing power and I/O. The standard board does not expose the Plus USB data pads, so saving59p creates a worse external USB connection: internal plug/pigtail or fine-pitch rework. Not preferred. |
| Seeed XIAO ESP32C3, SKU113991054 |21 ×17.8 mm manufacturer envelope;4 MB flash,400 KB SRAM;11 GPIO;3.3 V I/O;USB Serial/JTAG;external antenna |**£5.10 incl VAT**, [Pi Hut](https://thepihut.com/collections/seeed/products/seeed-xiao-esp32c3), shown available |Fits sideways in the same way, but costs more and adds radio/antenna/power-management work without a project benefit. Its USB implementation and flashing/power hooks differ; do not treat it as the same native USB device controller as RP2040. |
| Waveshare RP2040-Zero |18 ×23.5 mm manufacturer dimension drawing;2 MB flash,264 KB SRAM;USB-C;29 GPIO with some only on solder pads |Manufacturer [lists$3.99 without headers](https://www.waveshare.com/rp2040-zero.htm);no equally clear low-cost UK-stock listing was verified |Its18 mm short dimension exceeds the17.8 mm nominal LED height by0.2 mm. With USB directly facing bottom,23.5 mm must fit the height and fails decisively. Not the best choice under the strict PCB-silhouette rule. |

Manufacturer sources: [Seeed RP2040 family guide](https://wiki.seeedstudio.com/XIAO-RP2040/), [Seeed ESP32C3 guide](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/), [Waveshare RP2040-Zero guide and dimension drawing](https://www.waveshare.com/wiki/RP2040-Zero). Some retailer pages still quote20 ×17.5 mm for the older XIAO; use the current manufacturer21 ×17.8 mm envelope for layout, then measure the exact purchased revision. Prices/availability are snapshots, not reservations.

## The useful difference on XIAO RP2040 Plus

The [manufacturer native KiCad project](https://files.seeedstudio.com/wiki/XIAO-RP2040/res/XIAO_RP2040-Plus_V1.0_SCH%26PCB.zip) and [schematic](https://files.seeedstudio.com/wiki/XIAO-RP2040/res/XIAO_RP2040-Plus_SCH.pdf) were inspected directly. PCB thickness is0.804 mm. Its edge bounding box is20.9804 ×17.8054 mm, including the Edge.Cuts line width, consistent with the nominal21 ×17.8 form factor.

- **TP4 = USB_D+**, **TP12 = USB_D−**: both are1.143 mm round backside solder pads. These can be wired by hand without touching the socket’s0.3 mm contact pads.
- The standard **pad14 is VBUS**, pad13 GND; ordinary GPIO pads remain on2.54 mm header spacing. Additional Plus GPIO pads are finer1.27 mm castellations, but the basic project does not need them.
- The USB connector footprint identifies a3.25 mm high body. The native source places all actual SMD parts on F.Cu; its B.Cu footprints are test pads and a logo. Use an insulating printed cradle and reserve underside space for the soldered USB wires; do not rest pads or wire joints on the LED lead stubs.

Power the MCU from the VBUS/5 V pad and GND. Branch LED-driver5 V from the protected incoming supply; do not run the display load through the MCU’s3.3 V regulator. BAT pads and battery-management features are unused. Once the external USB port is wired, its internal USB-C socket must remain unused: two USB sources/hosts must never be connected simultaneously.

Programming stays convenient: hold BOOT while connecting external USB (or BOOT plus RESET), then copy a correctly built RP2040 UF2 to the RPI-RP2 drive. BOOT/RESET remain accessible under the removable back. The existing STM32 binary is not compatible; the portable animation player and sequence data can be retained while rebuilding the USB, I/O and driver hooks for RP2040. [Raspberry Pi’s bootrom/UF2 specification](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf).

## Stock USB-C breakout

**Adafruit4090**, [manufacturer page](https://www.adafruit.com/product/4090), is **20.4 ×14.2 ×5.0 mm overall**. [Pi Hut’s exact ADA4090 listing](https://thepihut.com/products/adafruit-usb-c-breakout-board-downstream-connection-ada4090) was **£2.90 incl VAT,8 units shown available**; its public product data also marked it available. The [manufacturer Eagle CAD](https://github.com/adafruit/Adafruit-USB-C-Downstream-Breakout) confirms:

| Header pin | Function |
| --- | --- |
|1 |GND |
|2 |VBUS |
|3 |D− |
|4 |CC1, through its own5.1k resistor R2 to GND |
|5 |D+ |
|6/7 |SBU1/SBU2, unused |
|8 |CC2, through its own5.1k resistor R1 to GND |

The PCB outline in those source files is20.32 ×13.97 mm; the conservative product envelope above includes the connector. Both CC pins are separately accessible, so the cost-down board can retain two ADC divider inputs for conservative current-advertisement sensing. The stock port already has the two required Rd resistors: do not add a second pair in parallel or wire its CC pins to the unused internal MCU socket’s CC pins.

CC pull-downs establish the sink role and5 V connection; **they do not grant1.5 A**. The source advertises the allowed current. Some retailer/manufacturer marketing phrases this loosely; the design must use source advertisement and USB configuration appropriately. RP2040 has no equivalent of the original STM32 BC1.2 detector. Keep LEDs dim with total input below the unconfigured USB limit until a suitable Type-C current advertisement or successful500 mA USB configuration is established; retain a dim fallback on unqualified chargers. Suspend and inrush must be rechecked. A recommended known5 V supply can simplify everyday use while USB programming remains available.

Alternatives checked:

| Breakout | Dimensions / electrical facts | Why not the first choice |
| --- | --- | --- |
| [Pololu3411 usb07b](https://www.pololu.com/product/3411) |20.3 ×12.7 mm PCB,about13.7 mm including connector;D+/D−,CC1/CC2,separate5.11k Rd |Good engineering option. [RobotShop UK](https://uk.robotshop.com/products/pololu-usb-20-type-c-connector-breakout-board-usb07b) £3.65 incl tax and restocking;Pimoroni’s public product feed £3.00/unavailable. No better immediate UK source established. |
| [Pi Hut106575 horizontal](https://thepihut.com/products/usb-c-breakout-horizontal) |22.5 ×19.5 mm from its supplied dimension drawing;£2.60;all required signals |19.5 mm height exceeds the LED silhouette and current cavity. Rejected for a flat installation despite its low price. |
| [Adafruit5180 simple socket](https://www.adafruit.com/product/5180) |14.5 ×9.2 ×3.2 mm;four USB pins only;no Rd resistors |Cheap and small, but omits proper Type-C sink resistors and accessible CC pins. It sacrifices C-to-C operation/current sensing and is not the proposed design. |
| [Adafruit5993 vertical](https://www.adafruit.com/product/5993) |30.5 ×15.2 ×11.1 mm |Unnecessary height/space for this case; horizontal4090 is simpler. |

## Case fit: what is and is not established

The LED/main mounting PCB remains at the existing position: front z9.3, rear z10.9. Current inside rear surface is z22.8, leaving11.9 mm behind the main board. This is ample for headerless modules in a new printed cradle, with a component/lead gap; ordinary tall Dupont sockets would waste that space.

A workable preliminary plan is:

- Place the XIAO long axis along x, in a free region such as x40–61, with its17.8 mm width aligned to the nominal LED silhouette y−0.25–17.55. This is an envelope candidate with no tolerance spare; the exact module and all seven actual LED bodies must be measured before freezing the cradle. Main LED pin positions do not move.
- Reserve roughly z13.7–20.2 for the MCU/cradle envelope, including rear-side components and its USB body; this leaves about2.6 mm to the existing rear cover. The source USB body height and PCB thickness support feasibility, but the complete module’s maximum component height was not independently measured. This is a feasibility allowance, not a collision-certified final assembly.
- Fit the4090 breakout behind the right end with its long side along x and connector pointing down. Its20.4 mm width means its centre must be at or left of aboutx78.2 if the PCB right edge is kept atx88.4. The old port centre wasx82.85. Thus the readily stocked breakout requires about a**4.65 mm left shift of the bottom port**, which remains near the right end. Keeping the old centre exactly would put a centred20.4 mm breakout past the LED silhouette.
- Its5 mm overall thickness fits the same rear space: even an envelope starting z14.4 ends z19.4, below z22.8. The existing16 mm carrier cradle and port well must be redrawn for the stock20.4 mm board. The old main JST occupies part of that wider board’s projected area and must be removed/relocated in the new layout. This is not a physical drop-in to the frozen A1 assembly.

If the exact old port centre must be preserved, find and verify a narrower fully featured USB breakout or retain a small custom connector PCB. Turning the4090 edge-on around the USB mating axis could keep the old x centre, but its20.4 mm width then becomes depth: a case around34 mm rather than24 mm would be needed. That is a clear depth sacrifice, so it is not preferred. A stock MCU’s USB directly facing down also cannot simply be made to fit by deepening the case: its21/23.5 mm length still exceeds the allowed front-view height unless the board and port are angled.

## Cost and next design decision

For three displays:3 ×£4.49 MCU +3 ×£2.90 USB breakout =**£22.17 incl VAT**, plus UK shop delivery, wire and the custom LED/driver PCB. No total finished-unit price is claimed until that PCB has been routed and quoted. Prefer ordinary hand-solderable wire pads, short twisted USB D+/D− wires, and a printed cradle that carries port insertion loads. Include input protection and CC dividers in the cost-down board as required; the stock breakout is a connector and Rd resistors, not the whole original protection circuit.

The main savings must come from a single lower-layer-count LED/driver assembly and eliminating the second custom-PCBA setup. Moving only the MCU does not itself make the four QFN driver fanouts or the existing six-layer routing disappear. The [parallel driver-architecture review](architecture-options.md) recommends four TLC59282 SSOP constant-current sink drivers and five high-side switches on a new two-layer main PCB; its conclusions and unresolved routing/brightness verification are recorded separately. Stock driver breakouts do not provide a tidy fit in this enclosure. The original seven raw displays still need properly limited multiplexed drive; they cannot be connected straight to a development board’s GPIO.

## Research inputs and scope

Local design inputs read: `hardware/README.md`, `hardware/kicad/circuit-spec.json`, `hardware/mechanical/enclosure.scad` and `hardware/mechanical/enclosure-notes.md`. Vendor files downloaded to the adjacent research reference folder are unmodified source evidence, not new manufacturing outputs. Seeed’s native project carries its original author/title and CC BY-SA4.0 attribution. Adafruit design source is by Limor Fried/Ladyada; retain its repository licence/attribution if redistributing source files. No supplier was contacted and no order or cart was modified.


B2 implementation note: the finished prototype placement and source-derived fit checks supersede the early placement sketch above. See [B2 mechanical assembly](../revisions/B2/mechanical/README.md), [module contract](../revisions/B2/stock-module-contract.json), [USB suspend audit](../revisions/B2/reports/usb-suspend-module-audit.md) and [UK shipping-rate estimate](module-shipping-quote.json).
