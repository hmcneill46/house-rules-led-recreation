# B2 Type-C ADC threshold review

29 October 2026. Prototype decision: retain the firmware's conservative **800–2200 mV raw-CC estimate** range, requiring exactly one qualifying CC input and100 ms stable detection. No additional CC IC, PCB change or firmware threshold change is approved by this review. USB configuration and positive BC1.2 classification remain independent routes to full brightness; host suspend overrides every grant.

## Primary voltage ranges

[ST AN5225 Rev 7, §4.2 Tables 6–7](https://www.st.com/resource/en/application_note/dm00536349.pdf) gives these sink-side ranges, including the cable-ground-drop allowance:

| Advertisement | Raw sink CC voltage |
|---|---:|
| Default USB current |250–610 mV|
| 1.5 A |700–1160 mV|
| 3 A |1310–2040 mV|

The nominal default/1.5 A decision boundary is660 mV. [TI TPS65987D, §6.8](https://www.ti.com/lit/ds/symlink/tps65987d.pdf) independently gives its1.5 A comparator threshold as610/660/700 mV minimum/typical/maximum. This does not establish the accuracy of an uncalibrated MCU ADC implementation.

Current-advertisement detection requires5.1 kΩ Rd within±10%. Our47 kΩ/47 kΩ divider also loads Rd: nominal `5.1k || 94k = 4.84kΩ`. With an assumed5%-low breakout Rd and1%-low divider resistors, the result is about4.61 kΩ, close to the4.59 kΩ lower limit. Verify the actual stock breakout and complete loading; do not count the same loading again by reducing the published CC voltage ranges a second time.

## Measurement budget

Firmware estimates raw CC as `ADC_code × 6600/4095`, assuming a3.3 V ADC reference and an exact half-voltage divider. The selected XIAO Plus uses RS3236-3.3YUTDN4, without the accuracy-grade A suffix. Its [manufacturer-authored RS3236 family datasheet](https://datasheet.lcsc.com/lcsc/2202251530_Jiangsu-RUNIC-Tech-RS3236-ADJ8YF5_C379351.pdf) specifies±2.5% fixed-output accuracy at25°C/0.1 mA; this alone is not a full-temperature reference bound.

For 1% divider resistors the ratio is0.495–0.505. Using±2.5% reference error gives the following conservative calculations, before ADC conversion error/noise:

| Included errors | Default maximum reported | 1.5 A minimum reported |
|---|---:|---:|
|Divider and reference only |631.9 mV |676.1 mV|
|Also a conservative±1 µA input-leakage allowance |680.6 mV |629.8 mV|

The leakage calculation uses about23.7 kΩ maximum divider Thevenin resistance: approximately47.5 mV error referred to raw CC. [RP2040 datasheet, Table 625 and §§4.9.2–4.9.4](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) supplies the 1 µA pin-leakage limit and ADC behavior. Its 100 kΩ ADC impedance is switched-capacitor behavior at500 ksps, not a permanent DC shunt. The 10 nF reservoir and low sampling rate help settling, but do not remove static leakage, reference error or ADC nonlinearity. Published ADC characterization is not a guaranteed complete absolute-error budget for this module.

Thus660 mV fits the ideal ranges but cannot yet be certified for every unit/source: adverse measurement error could grant full current on a default-current source. The retained 800 mV threshold adds false-grant margin while allowing a **known false-negative possibility** for valid low-end1.5 A advertisements.2200 mV covers the nominal3 A upper range with useful room-temperature error margin; it remains subject to qualification.

## Prototype qualification

Test known 5 V C-to-C supplies in both plug orientations, recording raw CC, reference voltage, BC status, USB configuration and selected duty. Use controlled boundary measurements near610/700 mV and at the3 A upper range before claiming support for all valid Type-C advertisements. Calibrate/qualify the complete divider–ADC path, including temperature and scan noise. Firmware thresholds can then change without a PCB change. A serial status report aids diagnosis; it does not measure source current. Separately measure startup, full-white and suspend current.

This is an engineering prototype policy, not a universal USB compatibility or compliance claim.
