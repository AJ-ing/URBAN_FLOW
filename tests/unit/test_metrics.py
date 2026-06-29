"""
test_metrics_calculator.py — Unit tests for metrics_calculator.py (POD 3: Analytics)

Tests metrics collection, calculation accuracy, and snapshot generation.

Run with:
    pytest tests/unit/test_metrics.py -v
"""

from __future__ import annotations

import pytest

from metrics_calculator import MetricsCalculator


class TestMetricsCalculatorInitialization:
    """Test metrics calculator setup and initialization."""

    def test_metrics_calculator_init_default_window(self):
        """MetricsCalculator initializes with default 300s window."""
        calc = MetricsCalculator()
        assert calc.window_s == 300, "Default window should be 300s"

    def test_metrics_calculator_init_custom_window(self):
        """MetricsCalculator accepts custom window size."""
        calc = MetricsCalculator(window_s=600)
        assert calc.window_s == 600, "Should use custom window"

    def test_metrics_calculator_reset(self):
        """MetricsCalculator can reset to initial state."""
        calc = MetricsCalculator()

        # Add some data
        calc.update(0.1, [], {0: 2, 1: 1, 2: 0, 3: 1})

        # Reset
        calc.reset()

        # Should be back to initial state
        assert len(calc.departed_vehicles) == 0, "Departed vehicles cleared"
        assert calc.tick_count == 0, "Tick count reset"
        assert calc.current_time == 0.0, "Time reset"


class TestThroughputCalculation:
    """Test throughput metric calculation (vehicles/hour)."""

    def test_throughput_calculation_basic(self):
        """Throughput is calculated in vehicles per hour."""
        calc = MetricsCalculator(window_s=60)  # 1 minute window

        # Simulate 5 vehicles crossing in 60 seconds
        for i in range(5):
            calc.departed_vehicles.append(
                (float(i * 10), 5.0, 25.0)
            )  # (time, wait, travel)

        calc.current_time = 60.0
        throughput = calc._calc_throughput()

        # 5 vehicles / 60 s * 3600 = 300 vph
        expected = 5.0 / 60.0 * 3600.0
        assert throughput == expected, f"Expected {expected} vph, got {throughput}"

    def test_throughput_zero_when_no_vehicles(self):
        """Throughput is zero when no vehicles have crossed."""
        calc = MetricsCalculator()
        calc.current_time = 60.0

        throughput = calc._calc_throughput()
        assert throughput == 0.0, "Throughput should be zero with no vehicles"

    def test_throughput_uses_rolling_window(self):
        """Throughput only counts vehicles within rolling window."""
        calc = MetricsCalculator(window_s=60)

        # current_time = 100, window = 60, cutoff = 40
        calc.departed_vehicles.append((5.0, 4.0, 20.0))  # t=5, outside window [40,100]
        calc.departed_vehicles.append((50.0, 5.0, 22.0))  # t=50, inside window
        calc.departed_vehicles.append((80.0, 3.0, 18.0))  # t=80, inside window

        calc.current_time = 100.0
        throughput = calc._calc_throughput()

        # Only 2 vehicles within [40, 100] window → 2/60*3600 = 120 vph
        expected = 2.0 / 60.0 * 3600.0
        assert (
            throughput == expected
        ), f"Should only count recent vehicles, expected {expected}, got {throughput}"

    def test_throughput_scales_to_hours(self):
        """Throughput is correctly scaled to vehicles/hour."""
        calc = MetricsCalculator(window_s=30)  # 30s window = 0.5 minutes

        # 3 vehicles in 30 seconds = 6 vehicles/hour
        calc.departed_vehicles = [
            (5.0, 2.0, 15.0),
            (10.0, 3.0, 18.0),
            (25.0, 1.0, 12.0),
        ]
        calc.current_time = 30.0

        throughput = calc._calc_throughput()
        # 3 vehicles in 30s = 3 * (3600/30) = 360 vph
        expected = 3.0 * (3600.0 / 30.0)
        assert throughput == expected, f"Expected {expected}, got {throughput}"


class TestAverageWaitTime:
    """Test average wait time calculation."""

    def test_average_wait_time_basic(self):
        """Average wait time is mean of all wait times."""
        calc = MetricsCalculator()

        calc.departed_vehicles = [
            (5.0, 10.0, 25.0),  # 10s wait
            (15.0, 20.0, 35.0),  # 20s wait
            (25.0, 30.0, 45.0),  # 30s wait
        ]

        avg_wait = calc._calc_avg_wait()
        expected = (10.0 + 20.0 + 30.0) / 3.0  # 20.0
        assert avg_wait == expected, f"Expected {expected}, got {avg_wait}"

    def test_average_wait_time_zero_when_no_vehicles(self):
        """Average wait is zero when no vehicles departed."""
        calc = MetricsCalculator()
        avg_wait = calc._calc_avg_wait()
        assert avg_wait == 0.0, "Should be zero with no vehicles"

    def test_average_wait_time_all_zero_wait(self):
        """Average wait is zero when all vehicles had no wait."""
        calc = MetricsCalculator()
        calc.departed_vehicles = [
            (5.0, 0.0, 15.0),
            (15.0, 0.0, 18.0),
        ]

        avg_wait = calc._calc_avg_wait()
        assert avg_wait == 0.0, "Should be zero with zero waits"


class TestAverageTravelTime:
    """Test average travel time calculation."""

    def test_average_travel_time_basic(self):
        """Average travel time is mean of all travel times."""
        calc = MetricsCalculator()

        calc.departed_vehicles = [
            (5.0, 2.0, 20.0),  # 20s travel
            (15.0, 3.0, 25.0),  # 25s travel
            (25.0, 1.0, 30.0),  # 30s travel
        ]

        avg_travel = calc._calc_avg_travel()
        expected = (20.0 + 25.0 + 30.0) / 3.0  # 25.0
        assert avg_travel == expected, f"Expected {expected}, got {avg_travel}"

    def test_average_travel_time_zero_when_no_vehicles(self):
        """Average travel is zero when no vehicles departed."""
        calc = MetricsCalculator()
        avg_travel = calc._calc_avg_travel()
        assert avg_travel == 0.0, "Should be zero with no vehicles"

    def test_travel_time_greater_than_wait_time(self):
        """Travel time should typically exceed wait time."""
        calc = MetricsCalculator()
        calc.departed_vehicles = [
            (5.0, 5.0, 25.0),
            (15.0, 8.0, 30.0),
            (25.0, 3.0, 28.0),
        ]

        avg_wait = calc._calc_avg_wait()
        avg_travel = calc._calc_avg_travel()

        assert avg_travel > avg_wait, "Travel time should be >= wait time"


class TestQueueLengthTracking:
    """Test queue length snapshot calculation."""

    def test_queue_length_snapshot(self):
        """Queue length is recorded in snapshot."""
        calc = MetricsCalculator()

        snapshot = calc.get_snapshot()
        assert "queue_length" in snapshot, "Should have queue_length in snapshot"
        assert isinstance(
            snapshot["queue_length"], (int, float)
        ), "Queue length should be numeric"

    def test_queue_length_updated(self):
        """Queue length updates when provided."""
        calc = MetricsCalculator()
        calc.queue_lengths = {0: 5, 1: 3, 2: 0, 3: 2}

        snapshot = calc.get_snapshot()
        total_queue = sum(calc.queue_lengths.values())
        assert snapshot["queue_length"] == total_queue, "Should sum all directions"

    def test_queue_length_zero_when_empty(self):
        """Queue length is zero when all directions empty."""
        calc = MetricsCalculator()
        calc.queue_lengths = {0: 0, 1: 0, 2: 0, 3: 0}

        snapshot = calc.get_snapshot()
        assert snapshot["queue_length"] == 0, "Queue length should be zero"


class TestSnapshotGeneration:
    """Test metrics snapshot format and content."""

    def test_snapshot_has_required_keys(self):
        """Snapshot contains all required metric keys."""
        calc = MetricsCalculator()
        snapshot = calc.get_snapshot()

        required_keys = ["throughput", "avg_wait", "avg_travel", "queue_length"]
        for key in required_keys:
            assert key in snapshot, f"Missing required key: {key}"

    def test_snapshot_values_are_numeric(self):
        """All snapshot values are numeric."""
        calc = MetricsCalculator()
        snapshot = calc.get_snapshot()

        for key, value in snapshot.items():
            assert isinstance(
                value, (int, float)
            ), f"{key} should be numeric, got {type(value)}"

    def test_snapshot_values_are_non_negative(self):
        """All snapshot values are non-negative."""
        calc = MetricsCalculator()
        snapshot = calc.get_snapshot()

        for key, value in snapshot.items():
            assert value >= 0, f"{key}={value} should be non-negative"

    def test_snapshot_roundtrip(self):
        """Snapshot can be created and read multiple times."""
        calc = MetricsCalculator()

        # Generate snapshots at different times
        snapshots = []
        for t in range(0, 30, 10):
            calc.current_time = float(t)
            snapshot = calc.get_snapshot()
            snapshots.append(snapshot)

        # All should have valid structure (6 keys: 4 canonical + 2 aliases)
        required_keys = {"throughput", "avg_wait", "avg_travel", "queue_length"}
        for snapshot in snapshots:
            assert required_keys.issubset(
                snapshot.keys()
            ), f"Snapshot missing required keys. Got: {set(snapshot.keys())}"


class TestMetricsUpdate:
    """Test metrics update logic with vehicle list."""

    def test_update_with_empty_vehicle_list(self):
        """Update handles empty vehicle list gracefully."""
        calc = MetricsCalculator()

        # Should not raise
        calc.update(0.1, [], {0: 0, 1: 0, 2: 0, 3: 0})

        assert calc.tick_count == 1, "Should increment tick count"
        assert calc.current_time == 0.1, "Should update current time"

    def test_update_accumulates_time(self):
        """Multiple updates accumulate time correctly."""
        calc = MetricsCalculator()

        calc.update(0.1, [], {0: 0, 1: 0, 2: 0, 3: 0})
        calc.update(0.1, [], {0: 0, 1: 0, 2: 0, 3: 0})
        calc.update(0.1, [], {0: 0, 1: 0, 2: 0, 3: 0})

        # Use approx due to floating-point accumulation
        assert abs(calc.current_time - 0.3) < 1e-9, "Time should accumulate"
        assert calc.tick_count == 3, "Tick count should accumulate"

    def test_update_records_queue_lengths(self):
        """Update records queue length information."""
        calc = MetricsCalculator()

        queues = {0: 3, 1: 2, 2: 5, 3: 1}
        calc.update(0.1, [], queues)

        assert calc.queue_lengths == queues, "Should record queue lengths"

    def test_update_with_multiple_calls(self):
        """Multiple updates maintain consistent state."""
        calc = MetricsCalculator()

        for tick in range(10):
            queues = {
                0: tick % 4,
                1: (tick + 1) % 4,
                2: (tick + 2) % 4,
                3: (tick + 3) % 4,
            }
            calc.update(0.1, [], queues)

        assert calc.tick_count == 10, "Should have 10 ticks"
        assert abs(calc.current_time - 1.0) < 1e-9, "Should be at 1.0 second"


class TestMetricsEdgeCases:
    """Test metrics calculation with edge cases."""

    def test_single_vehicle_metrics(self):
        """Metrics work correctly with single vehicle."""
        calc = MetricsCalculator()
        calc.departed_vehicles = [(10.0, 5.0, 20.0)]
        calc.current_time = 10.0

        snapshot = calc.get_snapshot()
        assert snapshot["avg_wait"] == 5.0, "Single vehicle wait should be exact"
        assert snapshot["avg_travel"] == 20.0, "Single vehicle travel should be exact"

    def test_very_high_wait_time(self):
        """Metrics handle very high wait times."""
        calc = MetricsCalculator()
        calc.departed_vehicles = [
            (100.0, 500.0, 600.0),  # 500s wait (extreme)
        ]
        calc.current_time = 100.0

        snapshot = calc.get_snapshot()
        assert snapshot["avg_wait"] == 500.0, "Should handle high wait"

    def test_very_short_travel_time(self):
        """Metrics handle very short travel times."""
        calc = MetricsCalculator()
        calc.departed_vehicles = [
            (5.0, 0.1, 1.0),  # 1s travel (very fast)
        ]
        calc.current_time = 5.0

        snapshot = calc.get_snapshot()
        assert snapshot["avg_travel"] == 1.0, "Should handle short travel"

    def test_metrics_with_many_vehicles(self):
        """Metrics work correctly with many vehicles."""
        calc = MetricsCalculator()

        # Add 1000 vehicles
        for i in range(1000):
            calc.departed_vehicles.append(
                (
                    float(i),
                    float(i % 50),
                    float(20 + (i % 30)),
                )
            )

        calc.current_time = 1000.0
        snapshot = calc.get_snapshot()

        # Should still have valid metrics
        assert 0 <= snapshot["avg_wait"] <= 50, "Average wait should be reasonable"
        assert 20 <= snapshot["avg_travel"] <= 50, "Average travel should be reasonable"


class TestMetricsConsistency:
    """Test that metrics remain consistent and correct."""

    def test_metrics_consistency_across_updates(self):
        """Metrics remain consistent with repeated updates."""
        calc = MetricsCalculator()

        calc.departed_vehicles = [
            (5.0, 10.0, 25.0),
            (15.0, 15.0, 30.0),
            (25.0, 5.0, 20.0),
        ]
        calc.current_time = 30.0

        snapshot1 = calc.get_snapshot()
        snapshot2 = calc.get_snapshot()

        assert snapshot1 == snapshot2, "Repeated snapshots should be identical"

    def test_metrics_order_independence(self):
        """Metrics don't depend on vehicle order."""
        calc1 = MetricsCalculator()
        calc2 = MetricsCalculator()

        vehicles_a = [
            (5.0, 10.0, 25.0),
            (15.0, 15.0, 30.0),
            (25.0, 5.0, 20.0),
        ]

        vehicles_b = list(reversed(vehicles_a))

        calc1.departed_vehicles = vehicles_a
        calc1.current_time = 30.0

        calc2.departed_vehicles = vehicles_b
        calc2.current_time = 30.0

        snap1 = calc1.get_snapshot()
        snap2 = calc2.get_snapshot()

        assert snap1["avg_wait"] == snap2["avg_wait"], "Order shouldn't affect average"
        assert (
            snap1["avg_travel"] == snap2["avg_travel"]
        ), "Order shouldn't affect travel"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
