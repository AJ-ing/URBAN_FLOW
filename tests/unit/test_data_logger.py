"""
test_data_logger.py — Unit tests for data_logger.py (POD 3: Data Export)

Tests data collection, CSV/JSON export, and comparison analysis.

Run with:
    pytest tests/unit/test_data_logger.py -v
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from src.evaluation.data_logger import (ComparisonAnalyzer, CSVExporter,
                                        DataLogger, JSONExporter)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Project-relative temp directory so exports stay within CWD
# (required by the path-traversal security guard).
_EXPORT_TMP = Path(__file__).parent / ".tmp_test_exports"


@pytest.fixture(autouse=True)
def _cleanup_export_tmp():
    """Create and clean up the project-local temp export directory."""
    _EXPORT_TMP.mkdir(exist_ok=True)
    yield
    # Cleanup any .csv / .json files written during the test
    for f in _EXPORT_TMP.glob("*.csv"):
        f.unlink(missing_ok=True)
    for f in _EXPORT_TMP.glob("*.json"):
        f.unlink(missing_ok=True)


class TestDataLoggerCollection:
    """Test data collection and record management."""

    def test_data_logger_initialization(self):
        """DataLogger initializes with empty records."""
        logger = DataLogger()

        records = logger.get_records()
        assert len(records) == 0, "Should start with no records"

    def test_data_logger_logs_snapshot(self):
        """DataLogger collects snapshot data."""
        logger = DataLogger()

        snapshot = {
            "throughput": 100.5,
            "avg_wait": 15.3,
            "avg_travel": 25.8,
            "queue_length": 5,
        }

        logger.log(snapshot, sim_time_s=10.0)

        records = logger.get_records()
        assert len(records) == 1, "Should have one record"

    def test_data_logger_rounds_values(self):
        """DataLogger rounds values to 2 decimal places."""
        logger = DataLogger()

        snapshot = {
            "throughput": 100.123456,
            "avg_wait": 15.999999,
            "avg_travel": 25.5555,
            "queue_length": 5,
        }

        logger.log(snapshot, sim_time_s=10.0)

        records = logger.get_records()
        record = records[0]

        assert record["throughput"] == 100.12, "Should round to 2 decimals"
        assert record["avg_wait"] == 16.0, "Should round 15.99 to 16.0"
        assert record["avg_travel"] == 25.56, "Should round to 2 decimals"

    def test_data_logger_accumulates_records(self):
        """DataLogger accumulates multiple snapshots."""
        logger = DataLogger()

        for i in range(5):
            snapshot = {
                "throughput": 100.0 + i,
                "avg_wait": 15.0 + i,
                "avg_travel": 25.0 + i,
                "queue_length": i,
            }
            logger.log(snapshot, sim_time_s=float(i * 10))

        records = logger.get_records()
        assert len(records) == 5, "Should have 5 records"

    def test_data_logger_records_time(self):
        """DataLogger records simulation time for each snapshot."""
        logger = DataLogger()

        snapshot = {
            "throughput": 100.0,
            "avg_wait": 15.0,
            "avg_travel": 25.0,
            "queue_length": 0,
        }

        logger.log(snapshot, sim_time_s=42.5)

        records = logger.get_records()
        assert records[0]["time_s"] == 42.5, "Should record exact sim time"


class TestCSVExport:
    """Test CSV export functionality."""

    def test_csv_export_creates_file(self):
        """CSVExporter creates output file."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        filepath = _EXPORT_TMP / "creates.csv"
        CSVExporter.export(logger, str(filepath))

        assert filepath.exists(), "CSV file should be created"

    def test_csv_export_contains_headers(self):
        """CSV export includes proper headers."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        filepath = _EXPORT_TMP / "headers.csv"
        CSVExporter.export(logger, str(filepath))

        with open(filepath) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        expected_headers = [
            "time_s",
            "throughput",
            "avg_wait",
            "avg_travel",
            "queue_length",
        ]
        assert headers == expected_headers, f"Headers should be {expected_headers}"

    def test_csv_export_data_integrity(self):
        """CSV export preserves data accurately."""
        logger = DataLogger()

        snapshot1 = {
            "throughput": 150.5,
            "avg_wait": 12.3,
            "avg_travel": 28.7,
            "queue_length": 3,
        }
        snapshot2 = {
            "throughput": 175.0,
            "avg_wait": 18.5,
            "avg_travel": 32.1,
            "queue_length": 7,
        }

        logger.log(snapshot1, sim_time_s=5.0)
        logger.log(snapshot2, sim_time_s=15.0)

        filepath = _EXPORT_TMP / "integrity.csv"
        CSVExporter.export(logger, str(filepath))

        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2, "Should have 2 data rows"
        assert float(rows[0]["time_s"]) == 5.0
        assert float(rows[0]["throughput"]) == 150.5
        assert float(rows[1]["time_s"]) == 15.0
        assert float(rows[1]["avg_wait"]) == 18.5

    def test_csv_export_empty_logger(self):
        """CSVExporter handles empty logger."""
        logger = DataLogger()

        filepath = _EXPORT_TMP / "empty.csv"
        # Should not raise
        CSVExporter.export(logger, str(filepath))

        # File should still exist
        assert filepath.exists(), "File should be created even for empty log"

    def test_csv_export_roundtrip(self):
        """CSV can be exported and loaded back."""
        logger = DataLogger()

        snapshots = [
            {
                "throughput": 100.0,
                "avg_wait": 10.0,
                "avg_travel": 20.0,
                "queue_length": 2,
            },
            {
                "throughput": 120.0,
                "avg_wait": 12.0,
                "avg_travel": 22.0,
                "queue_length": 3,
            },
        ]

        for i, snap in enumerate(snapshots):
            logger.log(snap, sim_time_s=float(i * 10))

        filepath = _EXPORT_TMP / "roundtrip.csv"
        CSVExporter.export(logger, str(filepath))
        loaded = CSVExporter.load(str(filepath))

        assert len(loaded) == 2, "Should load same number of records"
        assert float(loaded[0]["time_s"]) == 0.0


class TestJSONExport:
    """Test JSON export functionality."""

    def test_json_export_creates_file(self):
        """JSONExporter creates output file."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        filepath = _EXPORT_TMP / "creates.json"
        JSONExporter.export(logger, str(filepath))

        assert filepath.exists(), "JSON file should be created"

    def test_json_export_structure(self):
        """JSON export has hierarchical structure with metadata."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        filepath = _EXPORT_TMP / "structure.json"
        JSONExporter.export(logger, str(filepath))

        with open(filepath) as f:
            data = json.load(f)

        assert "metadata" in data, "Should have metadata"
        assert "records" in data, "Should have records"
        assert "summary" in data, "Should have summary"

    def test_json_export_metadata(self):
        """JSON metadata includes export time and record count."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        filepath = _EXPORT_TMP / "metadata.json"
        JSONExporter.export(logger, str(filepath))

        with open(filepath) as f:
            data = json.load(f)

        metadata = data["metadata"]
        assert "exported_at" in metadata, "Should have export timestamp"
        assert "record_count" in metadata, "Should have record count"
        assert metadata["record_count"] == 1, "Should count records"

    def test_json_export_records(self):
        """JSON records section contains all data."""
        logger = DataLogger()

        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )
        logger.log(
            {
                "throughput": 120.0,
                "avg_wait": 18.0,
                "avg_travel": 28.0,
                "queue_length": 7,
            },
            sim_time_s=20.0,
        )

        filepath = _EXPORT_TMP / "records.json"
        JSONExporter.export(logger, str(filepath))

        with open(filepath) as f:
            data = json.load(f)

        records = data["records"]
        assert len(records) == 2, "Should have 2 records"
        assert records[0]["time_s"] == 10.0
        assert records[1]["throughput"] == 120.0

    def test_json_export_summary_statistics(self):
        """JSON summary contains aggregate statistics."""
        logger = DataLogger()

        snapshots = [
            {
                "throughput": 100.0,
                "avg_wait": 10.0,
                "avg_travel": 20.0,
                "queue_length": 2,
            },
            {
                "throughput": 120.0,
                "avg_wait": 12.0,
                "avg_travel": 22.0,
                "queue_length": 3,
            },
            {
                "throughput": 110.0,
                "avg_wait": 11.0,
                "avg_travel": 21.0,
                "queue_length": 2,
            },
        ]

        for i, snap in enumerate(snapshots):
            logger.log(snap, sim_time_s=float(i * 10))

        filepath = _EXPORT_TMP / "summary.json"
        JSONExporter.export(logger, str(filepath))

        with open(filepath) as f:
            data = json.load(f)

        summary = data["summary"]
        assert "avg_throughput" in summary, "Should have avg throughput"
        assert "avg_wait" in summary, "Should have avg wait"
        assert "avg_travel" in summary, "Should have avg travel"

    def test_json_export_with_metadata(self):
        """JSONExporter accepts custom metadata."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        custom_meta = {
            "controller_mode": "adaptive",
            "test_scenario": "rush_hour",
        }

        filepath = _EXPORT_TMP / "with_meta.json"
        JSONExporter.export(logger, str(filepath), metadata=custom_meta)

        with open(filepath) as f:
            data = json.load(f)

        metadata = data["metadata"]
        assert (
            metadata.get("controller_mode") == "adaptive"
        ), "Should include custom metadata"
        assert (
            metadata.get("test_scenario") == "rush_hour"
        ), "Should include custom metadata"


class TestComparisonAnalyzer:
    """Test comparison analysis between two runs."""

    def test_comparison_analyzer_improvement_calculation(self):
        """ComparisonAnalyzer calculates improvement percentages."""
        baseline_logger = DataLogger()
        test_logger = DataLogger()

        baseline_snapshots = [
            {
                "throughput": 100.0,
                "avg_wait": 20.0,
                "avg_travel": 30.0,
                "queue_length": 5,
            },
            {
                "throughput": 110.0,
                "avg_wait": 18.0,
                "avg_travel": 28.0,
                "queue_length": 4,
            },
        ]
        test_snapshots = [
            {
                "throughput": 120.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 3,
            },
            {
                "throughput": 130.0,
                "avg_wait": 12.0,
                "avg_travel": 22.0,
                "queue_length": 2,
            },
        ]

        for i, snap in enumerate(baseline_snapshots):
            baseline_logger.log(snap, sim_time_s=float(i * 10))
        for i, snap in enumerate(test_snapshots):
            test_logger.log(snap, sim_time_s=float(i * 10))

        analyzer = ComparisonAnalyzer(baseline_logger, test_logger)
        results = analyzer.compare()

        # Throughput should improve (higher is better): 125 vs 105 baseline
        assert (
            results.get("throughput_improvement_pct", 0) > 0
        ), "Throughput should improve"
        # Wait time should reduce (lower is better)
        assert results.get("wait_reduction_pct", 0) > 0, "Wait time should reduce"

    def test_comparison_analyzer_handles_empty(self):
        """ComparisonAnalyzer handles empty DataLoggers gracefully."""
        empty_baseline = DataLogger()
        empty_test = DataLogger()
        analyzer = ComparisonAnalyzer(empty_baseline, empty_test)

        # Should not raise
        results = analyzer.compare()

        assert isinstance(results, dict), "Should return dict"

    def test_comparison_shows_degradation(self):
        """ComparisonAnalyzer detects when test performs worse."""
        baseline_logger = DataLogger()
        test_logger = DataLogger()

        baseline_logger.log(
            {
                "throughput": 150.0,
                "avg_wait": 10.0,
                "avg_travel": 20.0,
                "queue_length": 2,
            },
            sim_time_s=0.0,
        )
        test_logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 30.0,
                "avg_travel": 40.0,
                "queue_length": 8,
            },
            sim_time_s=0.0,
        )

        analyzer = ComparisonAnalyzer(baseline_logger, test_logger)
        results = analyzer.compare()

        # Throughput degraded → improvement should be negative
        assert (
            results.get("throughput_improvement_pct", 0) < 0
        ), "Degraded throughput should give negative improvement"
        # Wait time worsened → reduction should be negative
        assert (
            results.get("wait_reduction_pct", 0) < 0
        ), "Higher wait time should give negative reduction"


class TestPathTraversalProtection:
    """Test that export path validation prevents path traversal."""

    def test_export_rejects_parent_directory_path(self):
        """Export should reject paths that go to parent directory."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        # Try to export to parent directory
        bad_path = "../../../../../etc/passwd"

        # Should raise ValueError
        with pytest.raises(ValueError):
            CSVExporter.export(logger, bad_path)

    def test_export_rejects_absolute_path(self):
        """Export should reject absolute paths outside current directory."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        # Absolute path
        bad_path = "/etc/passwd"

        # Should raise ValueError
        with pytest.raises(ValueError):
            CSVExporter.export(logger, bad_path)

    def test_json_export_rejects_dangerous_path(self):
        """JSONExporter also validates paths."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )

        bad_path = "../../sensitive_file.json"

        with pytest.raises(ValueError):
            JSONExporter.export(logger, bad_path)

    def test_export_allows_safe_relative_path(self):
        """Export accepts safe relative paths in current directory."""
        logger = DataLogger()
        logger.log(
            {
                "throughput": 100.0,
                "avg_wait": 15.0,
                "avg_travel": 25.0,
                "queue_length": 5,
            },
            sim_time_s=10.0,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Safe relative path
                safe_path = "output.csv"

                # Should not raise
                CSVExporter.export(logger, safe_path)

                assert Path(safe_path).exists(), "File should be created"
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
