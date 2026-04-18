"""
test_metrics.py — White-box tests for POD 3: MetricsCalculator.

Runs standalone (``python test_metrics.py``) and is also pytest-compatible.
No pygame dependency required — uses lightweight MockVehicle stubs.
"""

import unittest
from metrics_calculator import MetricsCalculator


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

class MockVehicle:
    """Minimal stand-in for the pygame Vehicle sprite."""

    def __init__(
        self,
        direction_number: int = 0,
        crossed: int = 0,
        speed: float = 2.0,
        vehicle_class: str = "car",
    ) -> None:
        self.direction_number = direction_number
        self.crossed = crossed
        self.speed = speed
        self.vehicleClass = vehicle_class
        self.nominal_speed = speed
        self.lane = 0
        self.direction = "down"


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestMetricsCalculator(unittest.TestCase):
    """White-box tests for MetricsCalculator internals and public API."""

    # ---- TC-P3-PV-01: Throughput Calculation Accuracy --------------------

    def test_TC_P3_PV_01_throughput_accuracy(self) -> None:
        """10 vehicles depart over 60 s → throughput ≈ 600 veh/hr."""
        mc = MetricsCalculator(window_s=60)
        vehicles = [MockVehicle(speed=2.0, crossed=0) for _ in range(10)]
        queue = {0: 0, 1: 0, 2: 0, 3: 0}

        # 60 ticks at dt=1.0 s; depart one vehicle every 6 seconds
        for tick in range(60):
            # Every 6 s, mark the next vehicle as departed
            depart_idx = tick // 6
            if depart_idx < len(vehicles):
                vehicles[depart_idx].crossed = 1
                vehicles[depart_idx].speed = 2.0  # still moving after crossing

            mc.update(1.0, vehicles, queue)

        snap = mc.get_snapshot()
        throughput = snap["throughput"]
        internal = mc._calc_throughput()

        passed = 570 <= throughput <= 630 and throughput == internal
        status = "PASS" if passed else "FAIL"
        print(
            f"TC-P3-PV-01 [{status}] — Throughput = {throughput:.1f} veh/hr "
            f"(tolerance 570–630)"
        )
        self.assertGreaterEqual(throughput, 570)
        self.assertLessEqual(throughput, 630)
        self.assertEqual(throughput, internal)

    # ---- TC-P3-PV-02: Zero-Division Guard --------------------------------

    def test_TC_P3_PV_02_zero_division_guard(self) -> None:
        """Fresh calculator → get_snapshot() returns all zeros, no error."""
        mc = MetricsCalculator()

        try:
            snap = mc.get_snapshot()
            raised = False
        except ZeroDivisionError:
            raised = True
            snap = None

        expected = {
            "throughput": 0.0,
            "avg_wait": 0.0,
            "avg_travel": 0.0,
            "queue_length": 0,
            "avg_wait_time": 0.0,
            "avg_queue_length": 0.0,
        }

        passed = (not raised) and (snap == expected)
        status = "PASS" if passed else "FAIL"
        print(
            f"TC-P3-PV-02 [{status}] — All metrics zero, no ZeroDivisionError"
        )

        self.assertFalse(raised, "ZeroDivisionError was raised")
        self.assertEqual(snap, expected)

        # Also call internal methods directly
        self.assertEqual(mc._calc_throughput(), 0.0)
        self.assertEqual(mc._calc_avg_wait(), 0.0)
        self.assertEqual(mc._calc_avg_travel(), 0.0)

    # ---- Whitebox: _calc_throughput internal ------------------------------

    def test_calc_throughput_internal(self) -> None:
        """Manually populate departed_vehicles and verify throughput formula."""
        mc = MetricsCalculator(window_s=100)
        mc.current_time = 200.0  # pretend 200 s have elapsed

        # Insert 5 departures within the window (t >= 100)
        # and 3 outside the window (t < 100)
        mc.departed_vehicles = [
            (50.0, 1.0, 10.0),   # outside window
            (80.0, 2.0, 12.0),   # outside window
            (90.0, 1.5, 11.0),   # outside window
            (110.0, 3.0, 15.0),  # inside window
            (130.0, 2.5, 14.0),  # inside window
            (150.0, 1.0, 13.0),  # inside window
            (170.0, 2.0, 16.0),  # inside window
            (190.0, 3.5, 18.0),  # inside window
        ]

        # Expected: 5 in window → 5/100 * 3600 = 180.0
        result = mc._calc_throughput()
        expected = 5 / 100 * 3600  # 180.0

        passed = abs(result - expected) < 0.01
        status = "PASS" if passed else "FAIL"
        print(
            f"test_calc_throughput_internal [{status}] — "
            f"throughput = {result:.1f}, expected {expected:.1f}"
        )
        self.assertAlmostEqual(result, expected, places=2)

    # ---- Whitebox: _calc_avg_wait internal --------------------------------

    def test_calc_avg_wait_internal(self) -> None:
        """Populate departed_vehicles with known wait times, verify mean."""
        mc = MetricsCalculator()
        mc.departed_vehicles = [
            (10.0, 5.0, 10.0),
            (20.0, 10.0, 15.0),
            (30.0, 15.0, 20.0),
        ]

        # Expected avg wait: (5 + 10 + 15) / 3 = 10.0
        result = mc._calc_avg_wait()
        expected = 10.0

        passed = abs(result - expected) < 0.01
        status = "PASS" if passed else "FAIL"
        print(
            f"test_calc_avg_wait_internal [{status}] — "
            f"avg_wait = {result:.2f}, expected {expected:.2f}"
        )
        self.assertAlmostEqual(result, expected, places=2)

    # ---- Whitebox: division guards on all paths ---------------------------

    def test_division_guards_all_paths(self) -> None:
        """Every internal division path must survive empty / zero data."""
        errors: list[str] = []

        # 1. Fresh instance, no updates
        mc = MetricsCalculator()
        for method_name in ("_calc_throughput", "_calc_avg_wait", "_calc_avg_travel"):
            try:
                val = getattr(mc, method_name)()
                if val != 0.0:
                    errors.append(f"{method_name} returned {val}, expected 0.0")
            except ZeroDivisionError:
                errors.append(f"{method_name} raised ZeroDivisionError (fresh)")

        # 2. window_s = 0
        mc2 = MetricsCalculator(window_s=0)
        try:
            val = mc2._calc_throughput()
            if val != 0.0:
                errors.append(f"_calc_throughput(window_s=0) returned {val}")
        except ZeroDivisionError:
            errors.append("_calc_throughput raised ZeroDivisionError (window_s=0)")

        # 3. current_time = 0, but with a departed vehicle
        mc3 = MetricsCalculator()
        mc3.departed_vehicles = [(0.0, 1.0, 2.0)]
        mc3.current_time = 0.0
        try:
            val = mc3._calc_throughput()
        except ZeroDivisionError:
            errors.append("_calc_throughput raised ZeroDivisionError (current_time=0)")

        # 4. get_snapshot on empty
        mc4 = MetricsCalculator()
        try:
            mc4.get_snapshot()
        except ZeroDivisionError:
            errors.append("get_snapshot raised ZeroDivisionError")

        passed = len(errors) == 0
        status = "PASS" if passed else "FAIL"
        detail = "all paths safe" if passed else "; ".join(errors)
        print(f"test_division_guards_all_paths [{status}] — {detail}")
        self.assertEqual(errors, [])

    # ---- Whitebox: reset clears state ------------------------------------

    def test_reset_clears_state(self) -> None:
        """After populating the calculator, reset() returns snapshot to zeros."""
        mc = MetricsCalculator()
        vehicles = [MockVehicle(speed=2.0, crossed=0) for _ in range(3)]
        queue = {0: 5, 1: 3, 2: 2, 3: 1}

        # Run a few ticks, depart vehicles
        for tick in range(10):
            if tick >= 3:
                for v in vehicles:
                    v.crossed = 1
            mc.update(1.0, vehicles, queue)

        # Confirm non-zero state
        pre = mc.get_snapshot()
        self.assertGreater(pre["throughput"], 0)

        # Reset and verify
        mc.reset()
        post = mc.get_snapshot()
        expected = {
            "throughput": 0.0,
            "avg_wait": 0.0,
            "avg_travel": 0.0,
            "queue_length": 0,
            "avg_wait_time": 0.0,
            "avg_queue_length": 0.0,
        }

        passed = post == expected
        status = "PASS" if passed else "FAIL"
        print(f"test_reset_clears_state [{status}] — snapshot after reset: {post}")
        self.assertEqual(post, expected)

    # ---- Whitebox: update tracks new vehicles ----------------------------

    def test_update_tracks_new_vehicles(self) -> None:
        """update() must register each new vehicle in _vehicle_spawn_times."""
        mc = MetricsCalculator()
        v1 = MockVehicle()
        v2 = MockVehicle()
        v3 = MockVehicle()

        # Tick 1: pass v1, v2
        mc.update(1.0, [v1, v2], {0: 0, 1: 0, 2: 0, 3: 0})
        count_after_1 = len(mc._vehicle_spawn_times)

        # Tick 2: pass v1, v2, v3
        mc.update(1.0, [v1, v2, v3], {0: 0, 1: 0, 2: 0, 3: 0})
        count_after_2 = len(mc._vehicle_spawn_times)

        passed = count_after_1 == 2 and count_after_2 == 3
        status = "PASS" if passed else "FAIL"
        print(
            f"test_update_tracks_new_vehicles [{status}] — "
            f"tracked {count_after_1} after tick 1, {count_after_2} after tick 2"
        )
        self.assertEqual(count_after_1, 2)
        self.assertEqual(count_after_2, 3)

    # ---- Whitebox: wait time accumulation --------------------------------

    def test_wait_time_accumulation(self) -> None:
        """Stopped vehicles accumulate wait time correctly."""
        mc = MetricsCalculator()
        v = MockVehicle(speed=0.0, crossed=0)  # stopped vehicle
        queue = {0: 1, 1: 0, 2: 0, 3: 0}

        # 5 ticks at dt=1.0 while stopped
        for _ in range(5):
            mc.update(1.0, [v], queue)

        vid = id(v)
        wait = mc._vehicle_stop_times.get(vid, 0.0)

        passed = abs(wait - 5.0) < 0.01
        status = "PASS" if passed else "FAIL"
        print(
            f"test_wait_time_accumulation [{status}] — "
            f"accumulated wait = {wait:.1f}s, expected 5.0s"
        )
        self.assertAlmostEqual(wait, 5.0, places=2)

    # ---- Whitebox: avg_travel internal ------------------------------------

    def test_calc_avg_travel_internal(self) -> None:
        """Populate departed_vehicles with known travel times, verify mean."""
        mc = MetricsCalculator()
        mc.departed_vehicles = [
            (10.0, 2.0, 8.0),
            (20.0, 3.0, 12.0),
            (30.0, 1.0, 16.0),
        ]

        # Expected avg travel: (8 + 12 + 16) / 3 = 12.0
        result = mc._calc_avg_travel()
        expected = 12.0

        passed = abs(result - expected) < 0.01
        status = "PASS" if passed else "FAIL"
        print(
            f"test_calc_avg_travel_internal [{status}] — "
            f"avg_travel = {result:.2f}, expected {expected:.2f}"
        )
        self.assertAlmostEqual(result, expected, places=2)

    # ---- Whitebox: queue_length snapshot ---------------------------------

    def test_queue_length_snapshot(self) -> None:
        """get_snapshot()['queue_length'] sums across all directions."""
        mc = MetricsCalculator()
        queue = {0: 3, 1: 7, 2: 2, 3: 5}
        mc.update(1.0, [], queue)

        snap = mc.get_snapshot()
        expected_total = 17  # 3+7+2+5

        passed = snap["queue_length"] == expected_total
        status = "PASS" if passed else "FAIL"
        print(
            f"test_queue_length_snapshot [{status}] — "
            f"queue_length = {snap['queue_length']}, expected {expected_total}"
        )
        self.assertEqual(snap["queue_length"], expected_total)


# ---------------------------------------------------------------------------
# Standalone runner with summary
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("POD 3 — MetricsCalculator White-Box Test Suite")
    print("=" * 70)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMetricsCalculator)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passes = total - failures
    print(f"SUMMARY: {passes}/{total} tests passed, {failures} failed")
    print("=" * 70)
