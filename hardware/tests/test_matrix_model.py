import csv
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("matrix_model", ROOT / "hardware/simulation/matrix_model.py")
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


class MatrixModelTests(unittest.TestCase):
    def setUp(self):
        self.array = model.ModuleArray()
        self.drivers = model.prepare_drivers()

    def test_all_245_walking_pixels_decode_through_physical_diode_pins(self):
        for x in range(35):
            for y in range(7):
                frame = bytearray(35)
                frame[x] = 1 << y
                model.set_frame(self.array, self.drivers, bytes(frame))
                self.assertEqual(self.array.decode(self.drivers), bytes(frame), (x, y))

    def test_checkerboard_and_all_on_patterns(self):
        for frame in [bytes([127]) * 35, bytes([0]) * 35,
                      bytes(sum(1 << y for y in range(7) if (x + y) % 2) for x in range(35))]:
            model.set_frame(self.array, self.drivers, frame)
            self.assertEqual(self.array.decode(self.drivers), frame)

    def test_swapped_row_wiring_is_detected_in_the_reconstructed_display(self):
        connections = dict(self.array.connections)
        connections[0, 12], connections[0, 11] = connections[0, 11], connections[0, 12]
        wrong = model.ModuleArray(connections)
        frame = bytes([1] + [0] * 34)
        model.set_frame(wrong, self.drivers, frame)
        self.assertNotEqual(wrong.decode(self.drivers), frame)
        self.assertEqual(wrong.decode(self.drivers)[0], 2)

    def test_reversed_anode_cathode_connection_is_rejected(self):
        connections = dict(self.array.connections)
        connections[0, 1], connections[0, 12] = connections[0, 12], connections[0, 1]
        with self.assertRaisesRegex(ValueError, "anode.*not on a source"):
            model.ModuleArray(connections)

    def test_accidentally_shared_pair_cathodes_alias_and_are_rejected(self):
        connections = dict(self.array.connections)
        for pin in model.CATHODE_PINS:
            connections[1, pin] = connections[0, pin]
        with self.assertRaisesRegex(ValueError, "aliases"):
            model.ModuleArray(connections)

    def test_generated_pixel_csv_matches_independently_derived_diode_paths(self):
        expected = {(p.x, p.y): (p.driver + 1, p.sw, p.cs, p.register) for p in self.array.paths}
        with (ROOT / "hardware/design/pixel-map.csv").open(newline="") as handle:
            for row in csv.DictReader(handle):
                key = (int(row["x_0based"]), int(row["y_0based"]))
                actual = (int(row["driver_1based"]), int(row["SW_1based"]),
                          int(row["CS_1based"]), int(row["PWM_register"], 16))
                self.assertEqual(int(row["i2c_7bit_address"], 16), 0x33 + actual[0])
                self.assertEqual(expected.pop(key), actual)
        self.assertFalse(expected)

    def test_five_scan_phases_partition_all_245_pixels(self):
        model.set_frame(self.array, self.drivers, bytes([127]) * 35)
        phases = [self.array.decode(self.drivers, p) for p in range(1, 6)]
        self.assertTrue(all(sum(bin(c).count("1") for c in frame) == 49 for frame in phases))
        self.assertEqual(bytes(phases[0][x] | phases[1][x] | phases[2][x]
                               | phases[3][x] | phases[4][x] for x in range(35)), bytes([127]) * 35)

    def test_current_estimate_peak_margin_and_unused_outputs(self):
        model.set_frame(self.array, self.drivers, bytes([127]) * 35)
        average = self.array.average_current_a(self.drivers)
        self.assertAlmostEqual(average, 245 * (342/47000) * (255/256)**2 * (30/31.07) / 5)
        self.assertGreater(average, 0.34)
        self.assertLess(average, 0.35)
        worst_tolerance_peak = (342 / (47000 * 0.99)) * 255/256
        self.assertLess(worst_tolerance_peak, model.CONTINUOUS_ABSOLUTE_MAX_A)
        self.assertLess(self.array.worst_active_phase_a(self.drivers), 0.36)
        for index, driver in enumerate(self.drivers):
            for sw in range(1, 9):
                for cs in range(1, 17):
                    if sw > 5 or cs > model.USED_SINKS[index]:
                        self.assertEqual(driver.registers[(sw - 1)*16 + cs], 0)

    def test_reset_and_initialisation_leave_leds_dark(self):
        self.assertEqual(self.array.decode(self.drivers), bytes(35))
        for driver in self.drivers:
            self.assertEqual(driver.scans, 5)
            self.assertFalse(driver.enabled)
            driver.write(0xCF, 0xAE)
            self.assertEqual(driver.registers[0xA1], 0)
            self.assertFalse(driver.enabled)

    def test_sdb_bus_guard_times_are_enforced(self):
        driver = self.drivers[0]
        with self.assertRaisesRegex(ValueError, "before SDB"):
            driver.set_sdb(True)
        driver.wait_us(10)
        driver.set_sdb(True)
        with self.assertRaisesRegex(ValueError, "after SDB"):
            driver.write(0xA0, 0x41)
        driver.wait_us(10)
        driver.write(0xA0, 0x41)

    def test_optional_strict_policy_keeps_leds_off_until_500ma_is_authorised(self):
        all_on = bytes([127]) * 35
        self.assertEqual(model.apply_power_policy(self.array, self.drivers, all_on, model.PowerPolicy()), 0)
        self.assertEqual(self.array.decode(self.drivers), bytes(35))
        policy = model.PowerPolicy(authorised=True, available_ma=500)
        self.assertEqual(model.apply_power_policy(self.array, self.drivers, all_on, policy), 255)
        self.assertEqual(self.array.decode(self.drivers), all_on)
        self.assertLess(self.array.average_current_a(self.drivers)*1000 + policy.reserve_ma, 500)

    def test_authorised_low_budget_limits_average_current_and_suspend_shuts_down(self):
        all_on = bytes([127]) * 35
        policy = model.PowerPolicy(authorised=True, available_ma=100)
        brightness = model.apply_power_policy(self.array, self.drivers, all_on, policy)
        self.assertGreater(brightness, 0)
        self.assertLess(brightness, 255)
        self.assertLessEqual(self.array.average_current_a(self.drivers)*1000 + policy.reserve_ma, 100)
        model.apply_power_policy(self.array, self.drivers, all_on, model.PowerPolicy())
        self.assertTrue(all(not d.enabled for d in self.drivers))

    def test_hardware_current_setting_cannot_be_replaced_by_dim_pwm(self):
        unsafe = model.Driver(iset_ohms=10000)
        unsafe.write(0xA1, 0x40)
        unsafe.write(0x90, 255)
        self.assertGreater(unsafe.peak_a(1), model.CONTINUOUS_ABSOLUTE_MAX_A)
        unsafe.write(0x01, 1)  # Dim PWM does not change the instantaneous peak.
        self.assertGreater(unsafe.peak_a(1), model.CONTINUOUS_ABSOLUTE_MAX_A)

    def test_unmodelled_all_switches_on_mode_fails_instead_of_understating_current(self):
        model.set_frame(self.array, self.drivers, bytes([127]) * 35)
        self.drivers[0].write(0xA0, 0x81)
        with self.assertRaisesRegex(ValueError, "Only five-scan"):
            self.array.average_current_a(self.drivers)

    def test_firmware_default_dim_uses_lower_peak_current_and_stays_under_default_budget(self):
        gcc = model.apply_firmware_power(self.array, self.drivers, bytes([127]) * 35)
        self.assertEqual(gcc, 8)
        self.assertLess(self.array.average_current_a(self.drivers)*1000 + 30, 100)
        self.assertLess(self.drivers[0].peak_a(1)*1000, 1)

    def test_only_completed_positive_bc12_results_grant_charger_current(self):
        for port in ["unknown", "sdp", "error", "timeout"]:
            self.assertEqual(model.firmware_power_gcc(bc_finished=True, bc_port=port), 8)
        for port in ["cdp", "dcp"]:
            self.assertEqual(model.firmware_power_gcc(bc_finished=False, bc_port=port), 8)
            self.assertEqual(model.firmware_power_gcc(bc_finished=True, bc_port=port), 64)
        self.assertEqual(model.firmware_power_gcc(bc_finished=True, bc_port="dcp", suspended=True), 64)
        self.assertEqual(model.firmware_power_gcc(bc_finished=True, bc_port="cdp", suspended=True, host_seen=True), 0)


if __name__ == "__main__":
    unittest.main()
