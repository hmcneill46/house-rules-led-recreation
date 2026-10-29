# Freerouting 2.5 neckdown controls

Read-only audit, 29 October 2026. No board was loaded or changed by this check.

The installed native CLI identifies itself as **Freerouting CLI v2.5.0, build2026-10-05** and accepts these exact flags:

```text
--router.automatic_neckdown=false
--router.neck_width_um=110
```

Verified in an isolated `/tmp/house-rules-b2-neckdown-audit` configuration with analytics disabled and DEBUG output. It logged both settings as applied, then exited with the expected “No input design file specified” error. This establishes installed-parser support, not a successful reroute.

These options control different behaviours. `automatic_neckdown` lets the router reduce width at a small pin. The pinned v2.5.0 `AutorouteControl` reads this flag into `withNeckdown`. The separate `neck_width_um` is an opt-in retry at a specified manufacturable width after the net-class width fails; zero/absent disables that retry. Supply the **full trace width**, in micrometres, not a radius. For the B2 minimum0.11 mm,110 is the legal retry value. Disable automatic neckdown explicitly; setting the retry width alone does not disable the pin-based path. [Pinned RouterSettings source](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/RouterSettings.java), [pinned AutorouteControl source](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/autoroute/maze/AutorouteControl.java).

The CLI parser strips the `router.` prefix and applies the named fields. CLI settings override file/DSN/rules settings; API caller settings have higher priority if using the server. Exact implementation and precedence are documented in the [pinned CLI source](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/sources/CliSettings.java) and [pinned settings documentation](https://github.com/freerouting/freerouting/blob/v2.5.0/docs/settings.md).

These switches do not widen or erase narrow traces already present in the input. Existing illegal necks need removal/widening and native KiCad DRC. A reroute should be checked for minimum width, clearance, connectivity and the actual power-net rules; a router exit status is not a manufacturing acceptance check. This audit does not establish that every observed0.075/0.09 mm segment came from the same neckdown path.
