# TLC59283 with matched current — follow-up

**Quote TLC59283RGER plus four 7.15 kΩ current resistors before choosing solely on price.** This is a credible alternative with the same copper and external geometry, subject to analogue prototype tests. No CAD, BOM or firmware was changed.

Calculated nominal peak is **7.4001 mA**, only **0.335% below** the original7.4249mA.7.13k would be0.055% below, but7.15k is a standard E96 value. Parent live JLC search confirmed0603WAF7151T5E/C25980:61,580 stock, Extended, ±1%,100mW,0603,$0.0018 at1+. The existing470µs light time can remain with7.15k. Loading fees are included in the parent's complete assembly quotation rather than inferred from this unit price.

| Comparison at the published test conditions | Original59282 | Candidate59281 | Candidate59283 |
| --- | ---: | ---: | ---: |
| Device current error, typical / maximum | ±1% / ±3% | ±1% / ±6% | ±2% / ±4% |
| Channel current error, typical / maximum | ±0.6% / ±2% | ±1% / ±3% | ±1.4% / ±3% |
| Supply-current maxima, on / blank | 15 /6mA |18 /8mA |9 /4mA |
| Grouped transitions | Yes | No | Yes |
| Precharge | No | No | Yes |

Using the same conservative planning method as B2,59283/7.15k reduces estimated whole-product consumption by **24.19mA at full brightness** and **8.86mA at DIM** relative to the original.59281 instead increases it by11.15mA/8.17mA. These figures are planning comparisons, not certified USB maxima.59283 offers better power margin and retains staged switching, while59281 requires fewer BOM changes and has no new precharge path. Neither replacement matches all original accuracy specifications.

The powered steady-state gate analysis has **no identified hard incompatibility**: TI specifies low leakage with OUT=10V and BLANK/precharge enabled, so the precharge feature cannot simply be treated as a clamp from a5V gate to3.3V. A4.7k pullup loses at most2.35mV using the quoted125°C leakage bound. The programmed sink also retains ample pull-down margin. The7.15k resistor addresses the original current-gain difference.

**Existing QOD rails mitigate shutdown but do not prove it is qualified.** Neither datasheet gives the necessary VCC=0 reverse-current guarantee. The added internal path could behave differently as3.3V falls faster than the higher-capacitance5V rail. Retain the current clear/blank/Hi-Z sequence; verify both rails and gate/cathode waveforms during power-up, shutdown, reset and suspend. If that fails, independent sequencing or altered discharge circuitry could require a real PCB change. No such change is assumed in this price comparison.

At3.3V, precharge spans about1.3–2.5V; this is below the owned LED family's5V absolute reverse rating. That does not establish transient or long-term optical acceptance. TI's application note explicitly uses driver outputs to control common-line PNP transistors, supporting the broad topology, while warning about ringing with large wiring inductance. Our PMOS variant and narrow board still need measured ghosting, current-loop stability and temperature checks. Lower10V output headroom versus the original17V is another documented tradeoff, although both accommodate the normal5V rail.

Sources: [TI59283 datasheet](https://www.ti.com/lit/ds/symlink/tlc59283.pdf), [TI59281 datasheet](https://www.ti.com/lit/ds/symlink/tlc59281.pdf), [TI59282 datasheet](https://www.ti.com/lit/ds/symlink/tlc59282.pdf), [TI SLVAFP4 stability note](https://www.ti.com/lit/an/slvafp4/slvafp4.pdf), existing `hardware/reference/LMD07057AUE.pdf`. [Numerical/qualification record](tlc59283-matched-current-followup.json).
