"""
test_data_export.py — White-box tests for POD 3, Task 5.3: Data Export.

Covers TC-P3-SS-01 (CSV round-trip) and TC-P3-SS-02 (ComparisonAnalyzer 35%
improvement threshold), plus additional coverage for DataLogger, JSONExporter,
and edge cases.

Runs standalone (``python test_data_export.py``) and is pytest-compatible.
No pygame dependency required.
"""

import json
import os
import unittest

from data_logger import (
    ComparisonAnalyzer,
    CSVExporter,
    DataLogger,
    JSONExporter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Directory for temporary test artefacts (inside project root)
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def _make_snapshot(
    throughput: float = 0.0,
    avg_wait: float = 0.0,
    avg_travel: float = 0.0,
    queue_length: int = 0,
) -> dict:
    """Build a snapshot dict matching MetricsCalculator.get_snapshot() shape."""
    return {
        "throughput": throughput,
        "avg_wait": avg_wait,
        "avg_travel": avg_travel,
        "queue_length": queue_length,
        # Dashboard aliases
        "avg_wait_time": avg_wait,
        "avg_queue_length": float(queue_length),
    }


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestDataExport(unittest.TestCase):
    """White-box tests for DataLogger, CSVExporter, JSONExporter,
    and ComparisonAnalyzer."""

    # ---- TC-P3-SS-01: CSV Export Round-Trip Validation --------------------

    def test_TC_P3_SS_01_csv_round_trip(self) -> None:
        """100 snapshots → CSV → load back; row count and values must match."""
        logger = DataLogger()
        csv_path = os.path.join(_TEST_DIR, "_tc_ss01_test.csv")

        # 1–2. Log 100 snapshots with varying values
        for i in range(1, 101):
            snap = _make_snapshot(
                throughput=100.0 + i * 2.5,
                avg_wait=3.0 + i * 0.1,
                avg_travel=8.0 + i * 0.2,
                queue_length=i % 15,
            )
            logger.log(snap, sim_time_s=float(i))

        # 3. Export
        returned_path = CSVExporter.export(logger, csv_path)
        self.assertEqual(returned_path, csv_path)

        try:
            # 7. Verify header
            with open(csv_path, "r", encoding="utf-8") as fh:
                header_line = fh.readline().strip()
            self.assertEqual(
                header_line,
                "time_s,throughput,avg_wait,avg_travel,queue_length",
            )

            # 4. Load back
            loaded = CSVExporter.load(csv_path)

            # 5. Assert row count
            self.assertEqual(len(loaded), 100)

            # 6. Assert value accuracy (2 decimal places)
            original = logger.get_records()
            for orig, row in zip(original, loaded):
                self.assertAlmostEqual(row["time_s"], orig["time_s"], places=2)
                self.assertAlmostEqual(
                    row["throughput"], orig["throughput"], places=2
                )
                self.assertAlmostEqual(
                    row["avg_wait"], orig["avg_wait"], places=2
                )
                self.assertAlmostEqual(
                    row["avg_travel"], orig["avg_travel"], places=2
                )
                self.assertEqual(row["queue_length"], orig["queue_length"])

            passed = True
        except Exception:
            passed = False
            raise
        finally:
            # 8. Clean up
            if os.path.exists(csv_path):
                os.remove(csv_path)
            status = "PASS" if passed else "FAIL"
            print(
                f"TC-P3-SS-01 [{status}] — CSV round-trip: "
                f"100 rows exported/loaded, values match to 2 dp"
            )

    # ---- TC-P3-SS-02: ComparisonAnalyzer 35% Improvement ----------------

    def test_TC_P3_SS_02_comparison_35pct(self) -> None:
        """Adaptive run outperforms fixed baseline by >35% throughput."""
        baseline = DataLogger()
        adaptive = DataLogger()

        # 2–4. Populate 50 records each
        for i in range(50):
            t = float(i + 1)
            baseline.log(
                _make_snapshot(
                    throughput=400.0,
                    avg_wait=20.0,
                    avg_travel=30.0,
                    queue_length=10,
                ),
                sim_time_s=t,
            )
            adaptive.log(
                _make_snapshot(
                    throughput=600.0,
                    avg_wait=12.0,
                    avg_travel=22.0,
                    queue_length=5,
                ),
                sim_time_s=t,
            )

        # 5–6. Compare
        ca = ComparisonAnalyzer(baseline, adaptive)
        result = ca.compare()

        # 7. Throughput improvement > 35%
        self.assertGreater(result["throughput_improvement_pct"], 35.0)

        # 8. Wait reduction > 0
        self.assertGreater(result["wait_reduction_pct"], 0.0)

        # Also verify travel and queue improvements are positive
        self.assertGreater(result["travel_reduction_pct"], 0.0)
        self.assertGreater(result["queue_reduction_pct"], 0.0)

        # 9. Idempotency: same logger for both → all 0.0
        ca_same = ComparisonAnalyzer(baseline, baseline)
        result_same = ca_same.compare()
        for key, val in result_same.items():
            self.assertEqual(val, 0.0, f"Idempotency failed for {key}")

        status = "PASS"
        print(
            f"TC-P3-SS-02 [{status}] — throughput_improvement = "
            f"{result['throughput_improvement_pct']:.1f}% (>35%), "
            f"idempotency OK"
        )

    # ---- test_data_logger_clear -----------------------------------------

    def test_data_logger_clear(self) -> None:
        """clear() empties records and sets _is_cleared = True."""
        logger = DataLogger()
        for i in range(5):
            logger.log(_make_snapshot(throughput=float(i)), sim_time_s=float(i))
        self.assertEqual(len(logger), 5)
        self.assertFalse(logger._is_cleared)

        logger.clear()
        self.assertEqual(len(logger), 0)
        self.assertTrue(logger._is_cleared)

        status = "PASS"
        print(f"test_data_logger_clear [{status}] — len=0, _is_cleared=True")

    # ---- test_data_logger_get_latest ------------------------------------

    def test_data_logger_get_latest(self) -> None:
        """get_latest() returns None when empty, last record otherwise."""
        logger = DataLogger()

        # Empty
        self.assertIsNone(logger.get_latest())

        # After logging
        logger.log(_make_snapshot(throughput=100.0), sim_time_s=1.0)
        logger.log(_make_snapshot(throughput=200.0), sim_time_s=2.0)
        latest = logger.get_latest()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["time_s"], 2.0)
        self.assertEqual(latest["throughput"], 200.0)

        status = "PASS"
        print(
            f"test_data_logger_get_latest [{status}] — "
            f"None when empty, correct record after logging"
        )

    # ---- test_json_export_structure -------------------------------------

    def test_json_export_structure(self) -> None:
        """JSON output has metadata, records, and summary with correct averages."""
        logger = DataLogger()
        json_path = os.path.join(_TEST_DIR, "_tc_json_test.json")

        for i in range(1, 11):
            logger.log(
                _make_snapshot(
                    throughput=100.0 * i,
                    avg_wait=float(i),
                    avg_travel=float(i * 2),
                    queue_length=i,
                ),
                sim_time_s=float(i),
            )

        JSONExporter.export(
            logger, json_path, metadata={"controller": "adaptive", "version": 1}
        )

        try:
            with open(json_path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)

            # Top-level keys
            self.assertIn("metadata", doc)
            self.assertIn("records", doc)
            self.assertIn("summary", doc)

            # Metadata
            self.assertEqual(doc["metadata"]["record_count"], 10)
            self.assertEqual(doc["metadata"]["controller"], "adaptive")
            self.assertIn("exported_at", doc["metadata"])
            self.assertEqual(doc["metadata"]["total_sim_time_s"], 10.0)

            # Records
            self.assertEqual(len(doc["records"]), 10)

            # Summary averages  (throughput: mean of 100..1000 = 550)
            self.assertAlmostEqual(doc["summary"]["avg_throughput"], 550.0, places=1)
            # avg_wait: mean of 1..10 = 5.5
            self.assertAlmostEqual(doc["summary"]["avg_wait"], 5.5, places=1)
            # avg_travel: mean of 2,4,...,20 = 11.0
            self.assertAlmostEqual(doc["summary"]["avg_travel"], 11.0, places=1)
            # avg_queue_length: mean of 1..10 = 5.5
            self.assertAlmostEqual(doc["summary"]["avg_queue_length"], 5.5, places=1)

            passed = True
        except Exception:
            passed = False
            raise
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)
            status = "PASS" if passed else "FAIL"
            print(
                f"test_json_export_structure [{status}] — "
                f"metadata, records, summary all correct"
            )

    # ---- test_comparison_zero_division ----------------------------------

    def test_comparison_zero_division(self) -> None:
        """Baseline with all-zero metrics → compare() returns 0.0, no crash."""
        baseline = DataLogger()
        test_log = DataLogger()

        for i in range(10):
            baseline.log(
                _make_snapshot(
                    throughput=0.0, avg_wait=0.0, avg_travel=0.0, queue_length=0
                ),
                sim_time_s=float(i),
            )
            test_log.log(
                _make_snapshot(
                    throughput=100.0, avg_wait=5.0, avg_travel=10.0, queue_length=3
                ),
                sim_time_s=float(i),
            )

        ca = ComparisonAnalyzer(baseline, test_log)
        try:
            result = ca.compare()
            raised = False
        except ZeroDivisionError:
            raised = True
            result = {}

        self.assertFalse(raised, "ZeroDivisionError was raised")
        for key, val in result.items():
            self.assertEqual(val, 0.0, f"{key} should be 0.0 when baseline is 0")

        # Also test: both empty
        ca_empty = ComparisonAnalyzer(DataLogger(), DataLogger())
        try:
            result_empty = ca_empty.compare()
            raised_empty = False
        except ZeroDivisionError:
            raised_empty = True
            result_empty = {}

        self.assertFalse(raised_empty)
        for key, val in result_empty.items():
            self.assertEqual(val, 0.0)

        status = "PASS"
        print(
            f"test_comparison_zero_division [{status}] — "
            f"all-zero baseline and empty loggers handled safely"
        )

    # ---- test_csv_empty_logger ------------------------------------------

    def test_csv_empty_logger(self) -> None:
        """Empty DataLogger → CSV contains header row only."""
        logger = DataLogger()
        csv_path = os.path.join(_TEST_DIR, "_tc_empty_test.csv")

        CSVExporter.export(logger, csv_path)

        try:
            with open(csv_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()

            # Only header, no data
            self.assertEqual(len(lines), 1)
            self.assertEqual(
                lines[0].strip(),
                "time_s,throughput,avg_wait,avg_travel,queue_length",
            )

            # load() also returns empty list
            loaded = CSVExporter.load(csv_path)
            self.assertEqual(len(loaded), 0)

            passed = True
        except Exception:
            passed = False
            raise
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            status = "PASS" if passed else "FAIL"
            print(
                f"test_csv_empty_logger [{status}] — "
                f"header only, 0 data rows"
            )


# ---------------------------------------------------------------------------
# Standalone runner with summary
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("POD 3 — Data Export White-Box Test Suite")
    print("=" * 70)
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDataExport)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passes = total - failures
    print(f"SUMMARY: {passes}/{total} tests passed, {failures} failed")
    print("=" * 70)
