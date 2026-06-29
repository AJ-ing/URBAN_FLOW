"""
data_logger.py — POD 3, Task 5.3: Data Export for UrbanFlow Traffic Simulation.

Pure-Python module (no pygame, simulation, or metrics_calculator imports).
Provides four classes:

* **DataLogger** – collects metric snapshots over the course of a simulation run.
* **CSVExporter** – writes / reads records as CSV.
* **JSONExporter** – writes records + summary + metadata as hierarchical JSON.
* **ComparisonAnalyzer** – computes improvement percentages between two runs.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path Validation (Security)
# ---------------------------------------------------------------------------


def _validate_export_path(filepath: str) -> Path:
    """Validate export path for security (prevent path traversal attacks).

    Ensures the resolved path is within the current working directory
    or raises ValueError if it attempts to escape.
    """
    path = Path(filepath).resolve()
    cwd = Path.cwd().resolve()

    try:
        path.relative_to(cwd)
    except ValueError:
        raise ValueError(f"Export path escapes current directory: {filepath}")

    return path


# ---------------------------------------------------------------------------
# DataLogger
# ---------------------------------------------------------------------------


class DataLogger:
    """Memory-efficient collector for per-frame metric snapshots.

    Each record is a slim dict with only the canonical metric keys,
    rounded to two decimal places to keep memory and file sizes small.
    """

    def __init__(self) -> None:
        self.records: List[Dict[str, float | int]] = []
        self._is_cleared: bool = True

    # -- recording --------------------------------------------------------

    def log(self, snapshot: Dict[str, Any], sim_time_s: float) -> None:
        """Append one metric snapshot.

        Parameters
        ----------
        snapshot : dict
            Output of ``MetricsCalculator.get_snapshot()``.
        sim_time_s : float
            Current simulation wall-clock time in seconds.
        """
        record: Dict[str, float | int] = {
            "time_s": round(sim_time_s, 2),
            "throughput": round(snapshot["throughput"], 2),
            "avg_wait": round(snapshot["avg_wait"], 2),
            "avg_travel": round(snapshot["avg_travel"], 2),
            "queue_length": int(snapshot["queue_length"]),
        }
        self.records.append(record)
        self._is_cleared = False

    # -- accessors --------------------------------------------------------

    def get_records(self) -> List[Dict[str, float | int]]:
        """Return a shallow copy of the records list."""
        return list(self.records)

    def get_latest(self) -> Optional[Dict[str, float | int]]:
        """Return the most recent record, or ``None`` if empty."""
        if not self.records:
            return None
        return self.records[-1]

    # -- lifecycle --------------------------------------------------------

    def clear(self) -> None:
        """Remove all records.  Must be called between runs for
        ``ComparisonAnalyzer`` to work correctly."""
        self.records.clear()
        self._is_cleared = True

    def __len__(self) -> int:
        return len(self.records)


# ---------------------------------------------------------------------------
# CSVExporter
# ---------------------------------------------------------------------------


class CSVExporter:
    """Reads and writes ``DataLogger`` records as CSV files."""

    _FIELDNAMES: List[str] = [
        "time_s",
        "throughput",
        "avg_wait",
        "avg_travel",
        "queue_length",
    ]

    @staticmethod
    def export(data_logger: DataLogger, filepath: str) -> str:
        """Write all records to *filepath* as CSV.

        Parameters
        ----------
        data_logger : DataLogger
            Source of records.
        filepath : str
            Destination file path.

        Returns
        -------
        str
            The filepath that was written to.
        """
        # Validate path for security
        safe_path = _validate_export_path(filepath)

        with open(safe_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSVExporter._FIELDNAMES)
            writer.writeheader()
            for record in data_logger.records:
                writer.writerow(
                    {
                        "time_s": round(record["time_s"], 2),
                        "throughput": round(record["throughput"], 2),
                        "avg_wait": round(record["avg_wait"], 2),
                        "avg_travel": round(record["avg_travel"], 2),
                        "queue_length": int(record["queue_length"]),
                    }
                )
        return str(safe_path)

    @staticmethod
    def load(filepath: str) -> List[Dict[str, float | int]]:
        """Read a CSV file back into a list of record dicts.

        Numeric values are parsed to ``float`` / ``int`` as appropriate.

        Parameters
        ----------
        filepath : str
            Path to CSV previously written by :meth:`export`.

        Returns
        -------
        list[dict]
            One dict per row with the same keys as ``DataLogger.log`` produces.
        """
        records: List[Dict[str, float | int]] = []
        with open(filepath, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                records.append(
                    {
                        "time_s": float(row["time_s"]),
                        "throughput": float(row["throughput"]),
                        "avg_wait": float(row["avg_wait"]),
                        "avg_travel": float(row["avg_travel"]),
                        "queue_length": int(row["queue_length"]),
                    }
                )
        return records


# ---------------------------------------------------------------------------
# JSONExporter
# ---------------------------------------------------------------------------


class JSONExporter:
    """Writes ``DataLogger`` records as a hierarchical JSON document."""

    @staticmethod
    def export(
        data_logger: DataLogger,
        filepath: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write records, summary statistics, and metadata to *filepath*.

        Parameters
        ----------
        data_logger : DataLogger
            Source of records.
        filepath : str
            Destination file path.
        metadata : dict or None
            Extra key/value pairs merged into the ``"metadata"`` block.

        Returns
        -------
        str
            The filepath that was written to.
        """
        # Validate path for security
        safe_path = _validate_export_path(filepath)

        records = data_logger.get_records()
        count = len(records)

        total_sim_time: float = records[-1]["time_s"] if records else 0.0

        # Build metadata block
        meta: Dict[str, Any] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "record_count": count,
            "total_sim_time_s": total_sim_time,
        }
        if metadata:
            meta.update(metadata)

        # Build summary block (means of each metric)
        if count > 0:
            summary: Dict[str, float] = {
                "avg_throughput": round(
                    sum(r["throughput"] for r in records) / count, 2
                ),
                "avg_wait": round(sum(r["avg_wait"] for r in records) / count, 2),
                "avg_travel": round(sum(r["avg_travel"] for r in records) / count, 2),
                "avg_queue_length": round(
                    sum(r["queue_length"] for r in records) / count, 2
                ),
            }
        else:
            summary = {
                "avg_throughput": 0.0,
                "avg_wait": 0.0,
                "avg_travel": 0.0,
                "avg_queue_length": 0.0,
            }

        document: Dict[str, Any] = {
            "metadata": meta,
            "records": records,
            "summary": summary,
        }

        with open(safe_path, "w", encoding="utf-8") as fh:
            json.dump(document, fh, indent=2)

        return str(safe_path)


# ---------------------------------------------------------------------------
# ComparisonAnalyzer
# ---------------------------------------------------------------------------


class ComparisonAnalyzer:
    """Computes improvement percentages between a baseline and a test run.

    Positive values mean the *test* run performed **better**.
    """

    def __init__(
        self,
        baseline_logger: DataLogger,
        test_logger: DataLogger,
    ) -> None:
        self.baseline_logger: DataLogger = baseline_logger
        self.test_logger: DataLogger = test_logger

    # -- public API -------------------------------------------------------

    def compare(self) -> Dict[str, float]:
        """Return improvement percentages (test vs baseline).

        Returns
        -------
        dict
            ``throughput_improvement_pct`` – positive ⇒ test has higher throughput.
            ``wait_reduction_pct`` – positive ⇒ test has lower wait.
            ``travel_reduction_pct`` – positive ⇒ test has lower travel time.
            ``queue_reduction_pct`` – positive ⇒ test has shorter queues.
        """
        base = self._get_means(self.baseline_logger)
        test = self._get_means(self.test_logger)

        return {
            "throughput_improvement_pct": self._pct_change(
                base["throughput"], test["throughput"], higher_is_better=True
            ),
            "wait_reduction_pct": self._pct_change(
                base["avg_wait"], test["avg_wait"], higher_is_better=False
            ),
            "travel_reduction_pct": self._pct_change(
                base["avg_travel"], test["avg_travel"], higher_is_better=False
            ),
            "queue_reduction_pct": self._pct_change(
                base["queue_length"], test["queue_length"], higher_is_better=False
            ),
        }

    # -- internals --------------------------------------------------------

    def _get_means(self, logger: DataLogger) -> Dict[str, float]:
        """Compute the mean of each metric across all records.

        Returns a dict with keys: throughput, avg_wait, avg_travel, queue_length.
        All values are 0.0 when the logger is empty (zero-division guard).
        """
        records = logger.records
        n = len(records)
        if n == 0:
            return {
                "throughput": 0.0,
                "avg_wait": 0.0,
                "avg_travel": 0.0,
                "queue_length": 0.0,
            }
        return {
            "throughput": sum(r["throughput"] for r in records) / n,
            "avg_wait": sum(r["avg_wait"] for r in records) / n,
            "avg_travel": sum(r["avg_travel"] for r in records) / n,
            "queue_length": sum(r["queue_length"] for r in records) / n,
        }

    @staticmethod
    def _pct_change(
        baseline_val: float,
        test_val: float,
        *,
        higher_is_better: bool,
    ) -> float:
        """Compute a signed improvement percentage.

        Parameters
        ----------
        baseline_val : float
            Mean metric value from the baseline run.
        test_val : float
            Mean metric value from the test run.
        higher_is_better : bool
            If ``True``, formula is ``(test - baseline) / baseline * 100``
            (throughput).
            If ``False``, formula is ``(baseline - test) / baseline * 100``
            (wait, travel, queue — lower is better).

        Returns
        -------
        float
            Percentage improvement.  Returns 0.0 when ``baseline_val == 0``
            (zero-division guard).
        """
        if baseline_val == 0:
            return 0.0
        if higher_is_better:
            return ((test_val - baseline_val) / baseline_val) * 100.0
        return ((baseline_val - test_val) / baseline_val) * 100.0
