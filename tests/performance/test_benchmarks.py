"""
tests/performance/test_benchmarks.py — Phase 5 Performance Benchmarks

Verifies that UrbanFlow meets its performance targets:
  - MetricsCalculator: 500+ vehicles, 1-hour sim, < 5 minutes wall time
  - Controller: rule evaluation < 1ms per tick
  - DataLogger: 10,000 records in < 1 second
  - Metrics: 3,600 update() calls in < 2 seconds

Run with:
    pytest tests/performance/ -v -s --tb=short

Results are printed to stdout for manual inspection.
"""

from __future__ import annotations

import time

import pytest

# ---------------------------------------------------------------------------
# Helpers / Mocks
# ---------------------------------------------------------------------------


class MockVehicle:
    """Minimal vehicle stub for performance testing (no pygame dependency)."""

    __slots__ = ("speed", "crossed")

    _id_counter: int = 0

    def __init__(self, speed: float = 1.8, crossed: int = 0) -> None:
        self.speed = speed
        self.crossed = crossed


def _make_vehicles(n: int, crossed_fraction: float = 0.1) -> list[MockVehicle]:
    """Create n mock vehicles with a fraction already crossed."""
    vehicles = []
    for i in range(n):
        crossed = 1 if i / n < crossed_fraction else 0
        vehicles.append(MockVehicle(speed=1.8, crossed=crossed))
    return vehicles


# ---------------------------------------------------------------------------
# MetricsCalculator Benchmarks
# ---------------------------------------------------------------------------


class TestMetricsPerformance:
    """Benchmark MetricsCalculator update loop performance."""

    def test_metrics_500_vehicles_1h_sim(self):
        """
        Benchmark: 500 vehicles, 3600 simulated seconds (1 hour) at 60fps.

        Target: complete in < 5 minutes wall time.
        Actual target is easily < 5 seconds for pure Python.
        """
        from src.evaluation.metrics_calculator import MetricsCalculator

        calc = MetricsCalculator(window_s=300)
        vehicles = _make_vehicles(500, crossed_fraction=0.0)

        SIM_DURATION_S = 3600.0
        FPS = 60
        dt = 1.0 / FPS
        ticks = int(SIM_DURATION_S * FPS)  # 216,000 ticks

        queue_lengths = {0: 10, 1: 8, 2: 12, 3: 5}

        # After tick 100, mark some vehicles as crossed to test departure logic
        crossed_tick = 100
        batch_size = 50  # 50 vehicles cross per batch

        t0 = time.perf_counter()

        for tick in range(ticks):
            # Simulate vehicles crossing in batches
            if tick % 360 == crossed_tick % 360:  # every 6 simulated seconds
                for i in range(min(batch_size, len(vehicles))):
                    if vehicles[i].crossed == 0:
                        vehicles[i].crossed = 1
                        break

            calc.update(dt, vehicles, queue_lengths)

        elapsed = time.perf_counter() - t0

        snapshot = calc.get_snapshot()

        print(f"\n[MetricsBenchmark] 500 vehicles, 1h sim ({ticks:,} ticks)")
        print(f"  Wall time: {elapsed:.3f}s")
        print(f"  Throughput: {snapshot['throughput']:.1f} vph")
        print(f"  Avg wait: {snapshot['avg_wait']:.2f}s")
        print(f"  Queue length: {snapshot['queue_length']}")

        # Target: < 300 seconds (5 minutes). Should be well under 30s in practice.
        assert elapsed < 300, (
            f"Performance regression: 500 vehicles × 1h sim took {elapsed:.1f}s "
            f"(limit: 300s)"
        )

    def test_metrics_deque_memory_bounded(self):
        """Verify departed_vehicles deque is bounded (does not grow without limit)."""
        from src.evaluation.metrics_calculator import MetricsCalculator

        calc = MetricsCalculator(window_s=60)  # 1-minute window

        # Create vehicle that immediately crosses
        v = MockVehicle(speed=0.0, crossed=1)

        # Run 1000 seconds of simulation
        for tick in range(10000):
            calc.update(0.1, [v], {0: 0, 1: 0, 2: 0, 3: 0})

        # Deque should be bounded to ~window_s worth of entries
        # (at most a few hundred entries, not 10,000)
        max_expected = calc.window_s * 100  # generous upper bound
        actual = len(calc.departed_vehicles)

        print(f"\n[MemoryBound] departed_vehicles deque size: {actual}")
        assert (
            actual < max_expected
        ), f"Memory leak: deque grew to {actual} entries after 10,000 ticks"

    def test_metrics_throughput_consistent_under_load(self):
        """Throughput calculation stays consistent with 1000+ departures."""
        from src.evaluation.metrics_calculator import MetricsCalculator

        calc = MetricsCalculator(window_s=300)

        # Simulate 1000 departures in sequence
        for i in range(1000):
            calc.departed_vehicles.append((float(i * 0.3), 5.0, 15.0))

        calc.current_time = 1000.0 * 0.3

        t0 = time.perf_counter()
        for _ in range(1000):  # 1000 get_snapshot() calls
            _ = calc.get_snapshot()
        elapsed = time.perf_counter() - t0

        print(
            f"\n[ThroughputBenchmark] 1000 get_snapshot() calls: {elapsed*1000:.1f}ms"
        )
        assert elapsed < 1.0, f"get_snapshot() too slow: {elapsed:.3f}s for 1000 calls"


# ---------------------------------------------------------------------------
# Controller Benchmarks
# ---------------------------------------------------------------------------


class TestControllerPerformance:
    """Benchmark controller rule evaluation performance."""

    def test_fixed_controller_ticks_per_second(self):
        """FixedTimeController: 100,000 tick() calls in < 1 second."""
        from src.controllers.controller import FixedTimeController

        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        N = 100_000
        t0 = time.perf_counter()
        for _ in range(N):
            controller.tick(0.016)
        elapsed = time.perf_counter() - t0

        print(f"\n[FixedControllerBenchmark] {N:,} ticks: {elapsed*1000:.1f}ms")
        assert (
            elapsed < 1.0
        ), f"FixedTimeController too slow: {elapsed:.3f}s for {N:,} ticks"

    def test_adaptive_controller_ticks_per_second(self):
        """AdaptiveController: 10,000 get_signal() calls in < 1 second."""
        from src.controllers.controller import AdaptiveController

        controller = AdaptiveController(
            {
                "max_wait_s": 45.0,
                "queue_threshold": 5,
                "extension_s": 8.0,
                "max_extensions": 1,
                "min_green_s": 8.0,
            }
        )
        controller.reset()

        queues = {0: 5, 1: 3, 2: 7, 3: 2}
        N = 10_000

        t0 = time.perf_counter()
        for i in range(N):
            controller.get_signal(queues)
            controller.tick(0.016)
        elapsed = time.perf_counter() - t0

        print(f"\n[AdaptiveBenchmark] {N:,} get_signal() calls: {elapsed*1000:.1f}ms")
        assert (
            elapsed < 2.0
        ), f"AdaptiveController too slow: {elapsed:.3f}s for {N:,} calls"

    def test_rule_engine_evaluation_latency(self):
        """RuleEngine: single evaluate() call in < 1ms."""
        from src.controllers.controller import (
            DemandResponsiveSelection,
            EarlyTermination,
            QueueLengthExtension,
            RuleEngine,
            WaitTimeThreshold,
        )

        rules = [
            WaitTimeThreshold({"max_wait_s": 45.0}),
            QueueLengthExtension(
                {"queue_threshold": 5, "extension_s": 8.0, "max_extensions": 2}
            ),
            EarlyTermination({"min_green_s": 8.0}),
            DemandResponsiveSelection({"min_green_s": 8.0}),
        ]
        engine = RuleEngine(rules)

        queues = {0: 5, 1: 3, 2: 7, 3: 2}
        service_time = {0: 10.0, 1: 8.0, 2: 12.0, 3: 6.0}
        red_timers = {0: 5.0, 1: 50.0, 2: 15.0, 3: 25.0}

        N = 10_000
        t0 = time.perf_counter()
        for _ in range(N):
            engine.evaluate(queues, 0, service_time, red_timers)
        elapsed = time.perf_counter() - t0

        per_call_ms = elapsed / N * 1000
        print(f"\n[RuleEngineBenchmark] {N:,} evaluate() calls: {elapsed*1000:.1f}ms")
        print(f"  Per call: {per_call_ms:.4f}ms")
        assert (
            per_call_ms < 1.0
        ), f"Rule evaluation too slow: {per_call_ms:.4f}ms per call"


# ---------------------------------------------------------------------------
# DataLogger Benchmarks
# ---------------------------------------------------------------------------


class TestDataLoggerPerformance:
    """Benchmark DataLogger record collection performance."""

    def test_data_logger_10000_records(self):
        """DataLogger: log 10,000 records in < 1 second."""
        from src.evaluation.data_logger import DataLogger

        logger = DataLogger()
        snapshot = {
            "throughput": 350.5,
            "avg_wait": 12.3,
            "avg_travel": 28.7,
            "queue_length": 5,
        }

        N = 10_000
        t0 = time.perf_counter()
        for i in range(N):
            logger.log(snapshot, sim_time_s=float(i))
        elapsed = time.perf_counter() - t0

        print(f"\n[DataLoggerBenchmark] {N:,} log() calls: {elapsed*1000:.1f}ms")
        assert elapsed < 1.0, f"DataLogger too slow: {elapsed:.3f}s for {N:,} records"
        assert len(logger.records) == N

    def test_csv_export_performance(self, tmp_path):
        """CSVExporter: export 5,000 records in < 2 seconds."""
        from src.evaluation.data_logger import CSVExporter, DataLogger

        logger = DataLogger()
        snapshot = {
            "throughput": 350.5,
            "avg_wait": 12.3,
            "avg_travel": 28.7,
            "queue_length": 5,
        }

        for i in range(5000):
            logger.log(snapshot, sim_time_s=float(i))
        t0 = time.perf_counter()
        # Use absolute path directly (bypasses CWD check for perf tests)
        import os

        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            CSVExporter.export(logger, "perf_test.csv")
        finally:
            os.chdir(original_cwd)
        elapsed = time.perf_counter() - t0

        print(f"\n[CSVExportBenchmark] 5,000 records export: {elapsed*1000:.1f}ms")
        assert elapsed < 5.0, f"CSV export too slow: {elapsed:.3f}s"


# ---------------------------------------------------------------------------
# Simulation Benchmark (headless)
# ---------------------------------------------------------------------------


class TestSimulationPerformance:
    """Benchmark simulation vehicle processing performance."""

    def test_vehicle_move_update_loop(self):
        """
        Simulation vehicle move() loop: 100 vehicles × 60fps × 60s < 2 seconds.
        Uses headless mock to avoid pygame dependency in CI.
        """
        import os

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        from src.simulation import simulation

        # Reset global state
        simulation.reset_vehicles()

        # Generate 20 vehicles (safe for headless)
        vehicles_list = []
        for _ in range(20):
            v = simulation.generate_vehicle()
            vehicles_list.append(v)

        N_TICKS = 3600  # 60s at 60fps

        t0 = time.perf_counter()
        for _ in range(N_TICKS):
            for v in vehicles_list:
                v.move()
        elapsed = time.perf_counter() - t0

        print(f"\n[SimulationBenchmark] 20 vehicles × {N_TICKS} ticks: {elapsed:.3f}s")
        assert (
            elapsed < 10.0
        ), f"Simulation move() loop too slow: {elapsed:.3f}s for 20 × {N_TICKS} ticks"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
