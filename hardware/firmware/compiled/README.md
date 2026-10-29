# Compiled prototype image

For STM32G0B1KBU6 only, with the wiring and 47 kohm driver current setting described in the parent firmware README. These files compile successfully but have **not been tested on a physical board**. Do not use them as evidence that the board is ready to manufacture or that USB behaviour has passed electrical tests.

- `HouseRules.ino.bin`: raw flash image, base address 0x08000000.
- `HouseRules.ino.hex` / `.elf`: addressed programming images.
- `.map`: linker allocation for inspection.
- `build.log`: compiler memory result.
- `build-metadata.json`: pinned tool/core configuration and exact command.
- `elf-audit.txt`: actual descriptor bytes, USB pin table, verified wrapper call flow and image checksums.

Rebuild with `python3 hardware/tools/firmware-build/build.py` from the repository root. `python3 hardware/firmware/test_player.py` separately verifies the portable player against 60,000 scheduled frames.
