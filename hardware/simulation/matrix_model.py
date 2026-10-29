"""Functional pin-level LED/IS31FL3729 model, not an analogue simulator.

The module's internal diodes are independent of the project's wiring CSV. A
register image is decoded through those twelve terminals, rather than drawing
the intended framebuffer directly. Physical pad orientation remains unverified.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANODE_PINS = (1, 3, 10, 7, 8)
CATHODE_PINS = (12, 11, 2, 9, 4, 5, 6)
CONTINUOUS_ABSOLUTE_MAX_A = 0.020
USED_SINKS = (14, 14, 14, 7)
DRIVER_PACKAGE_PINS = {
    **{f"SW{i + 1}": 22 - i for i in range(8)},
    **dict(zip((f"CS{i}" for i in range(1, 17)),
               (30, 31, 32, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14))),
}


@dataclass(frozen=True)
class Terminal:
    driver: int  # zero based
    signal: str


@dataclass(frozen=True)
class PixelPath:
    module: int
    x: int
    y: int
    anode_pin: int
    cathode_pin: int
    driver: int
    sw: int
    cs: int

    @property
    def register(self) -> int:
        return (self.sw - 1) * 16 + self.cs


def load_connections(path: Path | None = None) -> dict[tuple[int, int], Terminal]:
    path = path or ROOT / "hardware/design/module-connections.csv"
    result = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (int(row["module"]) - 1, int(row["module_pin"]))
            if key in result:
                raise ValueError(f"Duplicate module terminal {key}")
            if DRIVER_PACKAGE_PINS.get(row["driver_signal"]) != int(row["driver_package_pin"]):
                raise ValueError(f"Incorrect package pin for {row['driver_signal']}")
            result[key] = Terminal(int(row["driver"]) - 1, row["driver_signal"])
    return result


class ModuleArray:
    """Seven modules, each with five anodes and seven cathodes."""

    def __init__(self, connections: dict[tuple[int, int], Terminal] | None = None):
        self.connections = load_connections() if connections is None else connections
        if set(self.connections) != {(m, p) for m in range(7) for p in range(1, 13)}:
            raise ValueError("Exactly twelve separate terminals per module are required")
        paths = []
        for module in range(7):
            for col, anode in enumerate(ANODE_PINS):
                source = self.connections[module, anode]
                if not source.signal.startswith("SW"):
                    raise ValueError(f"Module {module + 1} anode pin {anode} is not on a source switch")
                sw = int(source.signal[2:])
                for row, cathode in enumerate(CATHODE_PINS):
                    sink = self.connections[module, cathode]
                    if not sink.signal.startswith("CS"):
                        raise ValueError(f"Module {module + 1} cathode pin {cathode} is not on a current sink")
                    cs = int(sink.signal[2:])
                    if source.driver != sink.driver:
                        raise ValueError("A diode cannot be split between two independent driver chips")
                    if not (0 <= source.driver < 4 and 1 <= sw <= 5 and 1 <= cs <= 16):
                        raise ValueError("Connection falls outside the proposed four-chip five-scan topology")
                    paths.append(PixelPath(module, module * 5 + col, row,
                                           anode, cathode, source.driver, sw, cs))
        if len({(p.driver, p.register) for p in paths}) != 245:
            raise ValueError("Driver address aliases two or more physical pixels")
        self.paths = tuple(paths)

    def encode(self, columns: bytes, brightness: int = 255) -> list[dict[int, int]]:
        if len(columns) != 35 or any(c > 127 for c in columns):
            raise ValueError("Frame must contain 35 seven-bit columns")
        if not 0 <= brightness <= 255:
            raise ValueError("PWM brightness must be between 0 and 255")
        registers = [dict.fromkeys(range(1, 0x81), 0) for _ in range(4)]
        # Software's intended logical mapping is deliberately separate from the
        # physical pin paths used by decode(). This detects swapped wiring.
        for x, column in enumerate(columns):
            module, col = divmod(x, 5)
            driver, slot = divmod(module, 2)
            for row in range(7):
                register = col * 16 + slot * 7 + row + 1
                registers[driver][register] = brightness if column & (1 << row) else 0
        return registers

    def decode(self, drivers: list[Driver], scan_phase: int | None = None) -> bytes:
        columns = bytearray(35)
        if len(drivers) != 4:
            raise ValueError("Four drivers are required")
        for p in self.paths:
            driver = drivers[p.driver]
            if scan_phase is not None and p.sw != scan_phase:
                continue
            if driver.pixel_average_a(p.sw, p.cs) > 0:
                columns[p.x] |= 1 << p.y
        return bytes(columns)

    def average_current_a(self, drivers: list[Driver]) -> float:
        return sum(drivers[p.driver].pixel_average_a(p.sw, p.cs) for p in self.paths)

    def worst_active_phase_a(self, drivers: list[Driver]) -> float:
        """Conservative simultaneous on-current, with all driver phases aligned.

        This does not average PWM and assumes every nonzero PWM pulse overlaps.
        Supply decoupling and real asynchronous scan phase effects are unmodelled.
        """
        return max(sum(drivers[p.driver].peak_a(p.cs)
                       for p in self.paths if p.sw == phase
                       and drivers[p.driver].enabled
                       and drivers[p.driver].registers[p.register] > 0)
                   for phase in range(1, 6))


class Driver:
    """Small model of the relevant registers and hardware shutdown behaviour.

    Only the proposed n=5, 32 kHz PWM mode is used for current calculations.
    It intentionally rejects unmodelled modes rather than guessing their timing.
    """

    def __init__(self, iset_ohms: float = 47000, resistor_tolerance: float = 0):
        if iset_ohms <= 0 or not 0 <= resistor_tolerance < 1:
            raise ValueError("Invalid current-setting resistor")
        self.iset_ohms = iset_ohms * (1 - resistor_tolerance)
        self.sdb = False
        self.time_us = 0
        self.last_i2c_us = -10
        self.last_sdb_rise_us = -10
        self.reset()

    def reset(self):
        self.registers = bytearray(256)
        self.registers[0xA0] = 0x10  # n=8, software shutdown
        self.registers[0xB0] = 0x33
        self.registers[0xB2] = 0x01

    def wait_us(self, elapsed: int):
        if elapsed < 0:
            raise ValueError("Time cannot move backwards")
        self.time_us += elapsed

    def set_sdb(self, high: bool):
        if high and not self.sdb:
            if self.time_us - self.last_i2c_us < 10:
                raise ValueError("Allow 10 us without I2C before SDB rising")
            self.last_sdb_rise_us = self.time_us
        self.sdb = high

    def write(self, register: int, value: int):
        if not (0 <= register <= 255 and 0 <= value <= 255):
            raise ValueError("Registers and values are bytes")
        if self.time_us - self.last_sdb_rise_us < 10:
            raise ValueError("Allow 10 us after SDB rising before I2C")
        if register == 0xCF and value == 0xAE:
            self.reset()
        elif register == 0xA1:
            self.registers[register] = min(value & 0x7F, 0x40)
        else:
            self.registers[register] = value
        self.last_i2c_us = self.time_us

    @property
    def enabled(self) -> bool:
        return self.sdb and bool(self.registers[0xA0] & 1)

    @property
    def scans(self) -> int:
        selection = self.registers[0xA0] >> 4
        return {0: 9, 1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2}.get(selection, 0)

    def peak_a(self, cs: int) -> float:
        if not 1 <= cs <= 16:
            raise ValueError("CS must be 1 through 16")
        return (342 / self.iset_ohms * self.registers[0xA1] / 64
                * self.registers[0x90 + cs - 1] / 256)

    def pixel_average_a(self, sw: int, cs: int) -> float:
        if not self.enabled:
            return 0
        if self.scans != 5 or self.registers[0xB2] != 1:
            raise ValueError("Only five-scan / 32 kHz current timing is modelled")
        if sw > self.scans:
            return 0
        slot_utilisation = 30 / (30 + 0.8 + 0.27)
        pwm = self.registers[(sw - 1) * 16 + cs]
        return self.peak_a(cs) * pwm / 256 * slot_utilisation / 5


def prepare_drivers(resistor_tolerance: float = 0) -> list[Driver]:
    """Populate registers while hardware/software shutdown both remain active."""
    drivers = [Driver(resistor_tolerance=resistor_tolerance) for _ in range(4)]
    for index, driver in enumerate(drivers):
        driver.wait_us(10)  # after the 5 V rail stabilises; POR timing is not modelled
        driver.write(0xCF, 0xAE)
        driver.write(0xA0, 0x40)  # five scans, low logic threshold, SSD=0
        driver.write(0xA1, 0x40)
        driver.write(0xB2, 0x01)
        for cs in range(1, 17):
            driver.write(0x90 + cs - 1, 255 if cs <= USED_SINKS[index] else 0)
    return drivers


@dataclass(frozen=True)
class PowerPolicy:
    """Explicit source authorisation, not inferred from cable presence.

    authorised=False keeps LEDs in shutdown before USB enumeration or before a
    separately established charger/Type-C current advertisement. A 30 mA
    controller/driver reserve is an engineering allowance, not a measurement.
    """
    authorised: bool = False
    available_ma: float = 100
    reserve_ma: float = 30

    def pwm_ceiling(self, array: ModuleArray, drivers: list[Driver]) -> int:
        if len(drivers) != 4:
            raise ValueError("Four drivers are required")
        if not self.authorised or self.available_ma <= self.reserve_ma:
            return 0
        probe = prepare_drivers(resistor_tolerance=0.01)
        for copy, original in zip(probe, drivers):
            copy.iset_ohms = original.iset_ohms * 0.99
        set_frame(array, probe, bytes([127]) * 35, 255, enable=True)
        full_ma = array.average_current_a(probe) * 1000
        return min(255, max(0, int(255 * (self.available_ma - self.reserve_ma) / full_ma)))


def set_frame(array: ModuleArray, drivers: list[Driver], columns: bytes,
              brightness: int = 255, enable: bool = True):
    if len(drivers) != 4:
        raise ValueError("Four drivers are required")
    for driver, image in zip(drivers, array.encode(columns, brightness)):
        for register, value in image.items():
            driver.write(register, value)
        if enable:
            driver.wait_us(10)
            driver.set_sdb(True)
            driver.wait_us(10)
            driver.write(0xA0, 0x41)
        else:
            driver.set_sdb(False)
            driver.write(0xA0, 0x40)


def apply_power_policy(array: ModuleArray, drivers: list[Driver], columns: bytes,
                       policy: PowerPolicy, requested_brightness: int = 255) -> int:
    ceiling = policy.pwm_ceiling(array, drivers)
    brightness = min(max(0, requested_brightness), ceiling)
    set_frame(array, drivers, columns, brightness, enable=brightness > 0)
    return brightness


def firmware_power_gcc(*, configured=False, suspended=False, host_seen=False,
                       cc_high=False, bc_finished=False, bc_port="unknown") -> int:
    """The prototype's source-selection contract, including the dim fallback.

    BC1.2 allowance needs both a positive CDP/DCP result and successful completion.
    This models supplied classification results, not the analogue detection.
    """
    charging = bc_finished and bc_port in {"cdp", "dcp"}
    if suspended and (host_seen or not (cc_high or charging)):
        return 0
    return 64 if configured or cc_high or charging else 8


def apply_firmware_power(array: ModuleArray, drivers: list[Driver], columns: bytes,
                         **state) -> int:
    gcc = firmware_power_gcc(**state)
    for driver in drivers:
        driver.write(0xA1, gcc)
    set_frame(array, drivers, columns, 255, enable=gcc > 0)
    return gcc
