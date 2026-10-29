# USB carrier routing verification

29 October 2026, KiCad 10.0.7. Final board: `hardware/kicad/house-rules-usb.kicad_pcb`.

Native `kicad-cli pcb drc --schematic-parity` reports **0 violations, 0 unconnected items and 0 schematic parity issues**, including warnings. The JSON report is `usb-routing-final-drc.json`. Separate native pad/net and field comparison against `circuit-spec.json` is recorded in `usb-routing-verification.json`.

The autorouter session left two missing nets. A short front copper bridge joins ESD CC2 pad 6 to the existing CC2 route. The left USB VBUS contact group escapes north of the connector's locating hole, reaches a 0.4/0.2 via and joins the other VBUS contact group with a short 0.3 mm In1.Cu route and second via. The connector's two VBUS groups, input capacitor, TVS and harness VBUS are now one connected net. The unused dangling CC2 via was removed. The `USB 5V` back legend moved away from shell solder pads to local (10,1).

The locked USB data paths were preserved. This carrier uses four copper layers, with existing CC1 routing on inner layers; the final step did not convert these into power planes. The board remains 16.0 × 16.8 × 1.0. Component placements, footprints, pin assignments and schematic nets were unchanged. Full footprint library IDs and hidden MPN/LCSC/Datasheet/Description fields match the circuit specification.

`hardware/tools/finish_usb_routing.py` reproduces the final manual connections after the recorded `.ses` import. The `.ses` file is the earlier autorouter result and lacks those finishing connections. Re-importing it must be followed by the finishing script and a fresh native DRC; use `finalize_pcbs.py --board usb --metadata-only` when refreshing fields on the final board.

These checks verify board connectivity and geometric rules. They do not establish USB signal integrity, ESD immunity, thermal behaviour, connector force resistance or physical enclosure fit. USB enumeration with both connector orientations and representative USB-A and USB-C sources remains a bench check on the first assembled prototype.
