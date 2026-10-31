#!/usr/bin/env python3
"""Illustrate the TLC59281 destructive-latch contract with four serial registers.

This is an independent digital thought experiment from the TI datasheet's
register description (SBVS139B, p.14), not a chip simulation or firmware emulator.
It does not execute application.cpp, model electrical timing, or predict actual
TI production-test data. Arbitrary reserved register contents are deliberately
injected after each latch to test whether the next complete write flushes them.

Run from any directory:
  python3 protocol_latch_probe.py --output protocol-latch-probe-result.json
"""

import argparse
import json
import random
from pathlib import Path


class RegisterChain:
    """Serial state only; LAT captures outputs then invalidates shift contents."""

    def __init__(self, rng, devices=4):
        self.rng = rng
        self.devices = devices
        self.shift = [rng.randrange(65536) for _ in range(devices)]
        self.output = [rng.randrange(65536) for _ in range(devices)]

    def clock(self, bit):
        for device in range(self.devices):
            old = self.shift[device]
            self.shift[device] = ((old << 1) | bit) & 0xFFFF
            bit = (old >> 15) & 1

    def write_words(self, desired):
        # The last serial device's word enters first; each word is MSB-first.
        for word in reversed(desired):
            for bit_number in range(15, -1, -1):
                self.clock((word >> bit_number) & 1)

    def latch_rising(self):
        self.output = self.shift.copy()
        # Actual TI reserved values are unspecified. Random values exercise the
        # contract without assuming production-test contents are zero or stable.
        self.shift = [self.rng.randrange(65536) for _ in range(self.devices)]


def probe():
    seed = 59281
    rng = random.Random(seed)
    chain = RegisterChain(rng)
    frames = 1000
    for _ in range(frames):
        desired = [rng.randrange(65536) for _ in range(4)]
        chain.write_words(desired)
        chain.latch_rising()
        assert chain.output == desired, "A complete write failed to flush reserved data"

    # Wake/shutdown-style clear: all reserved contents are replaced by zeros.
    chain.write_words([0] * 4)
    chain.latch_rising()
    assert chain.output == [0] * 4

    # An allowed adversarial reserved state demonstrates the extra-LAT hazard.
    # This is not a prediction of the actual part's reserved production data.
    chain.shift = [0xFFFF] * 4
    chain.latch_rising()
    assert chain.output != [0] * 4
    extra_latch_corruption = chain.output.copy()

    # 63 clocks cannot guarantee replacement of all 64 old bits.
    chain.shift = [0xFFFF] * 4
    for _ in range(63):
        chain.clock(0)
    chain.latch_rising()
    assert chain.output == [0, 0, 0, 0x8000]

    return {
        "review_date": "2026-10-31",
        "status": "PASS",
        "model_type": "Illustrative independent digital register model",
        "source": "https://www.ti.com/lit/ds/symlink/tlc59281.pdf",
        "source_section": "Register Configuration, printed page14",
        "seed": seed,
        "devices": 4,
        "bits_per_device": 16,
        "fresh_bits_per_frame": 64,
        "complete_frames_checked": frames,
        "full_write_before_single_latch": "PASS for every frame",
        "full_zero_write_after_reserved_data": "PASS",
        "extra_latch_without_write_counterexample": extra_latch_corruption,
        "partial_63_clock_clear_counterexample": chain.output,
        "conclusion": "A complete64bit write before each single LAT flushes arbitrary reserved contents; relatching or partial writes are unsafe.",
        "limitations": [
            "Not a real-device model, analogue simulator or full firmware emulator.",
            "Reserved contents are deliberately arbitrary, not actual TI test data.",
            "No setup/hold, propagation, current, MOSFET, USB or thermal behavior modeled.",
            "Firmware source inspection is a separate review, not executed by this probe.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe()
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
