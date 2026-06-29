# API Reference Documentation

This document describes the public classes, methods, parameters, and types of the UrbanFlow engine modules.

---

## 1. Analytics Module (`metrics_calculator.py`)

### `MetricsCalculator`
Accumulates per-frame vehicle telemetry and exposes aggregate KPIs.

#### Methods
- **`__init__(window_s: int = 300)`**:
  - Sets up the metrics rolling window in seconds.
- **`reset() -> None`**:
  - Clears all internal states back to zero.
- **`update(dt: float, vehicles_iter: Iterable[Any], queue_lengths: Dict[int, int]) -> None`**:
  - Ingests a simulation frame. Computes wait times for stopped vehicles and records crossings.
- **`get_snapshot() -> Dict[str, float | int]`**:
  - Returns a dictionary containing `"throughput"`, `"avg_wait"`, `"avg_travel"`, `"queue_length"`.

---

## 2. Persistence Module (`data_logger.py`)

### `DataLogger`
Accumulates snapshots over the course of a simulation run.
- **`log(snapshot: dict, sim_time_s: float) -> None`**: Logs a telemetry record.
- **`get_records() -> list[dict]`**: Returns logged telemetry.
- **`clear() -> None`**: Empties memory buffers.

### `CSVExporter`
Exposes static export utilities.
- **`export(logger: DataLogger, filepath: str) -> None`**: Writes in-memory logs to a CSV file. Validates path boundaries to prevent traversal attacks.

### `ComparisonAnalyzer`
Compares telemetry stats between two simulation runs.
- **`compare(baseline: DataLogger, test: DataLogger) -> dict`**: Computes relative improvements in wait times, queue sizes, and throughput.

---

## 3. Signal Controllers Module (`controller.py`)

### `FixedTimeController`
Configurable pre-timed cycle.
- **`tick(dt: float) -> None`**: Advances phase timing.
- **`get_signal(queues: dict) -> int`**: Returns the green phase direction index.
- **`time_until_green(direction: int) -> float`**: Calculates the precise countdown until the requested direction turns green.

### `AdaptiveController`
Rule-engine based signal optimization.
- **`tick(dt: float) -> None`**: Updates timers.
- **`get_signal(queues: dict) -> int`**: Queries the rule engine and updates phase durations.

---

## 4. UI State Machine (`dashboard_state.py`)

### `DashboardState`
The pure-Python state machine for the dashboard widgets.
- **`toggle_play() -> None`**: Flips the run state between playing and paused.
- **`request_reset() -> None`**: Latches a reset trigger.
- **`update_snapshot(snapshot: dict, sim_time_s: float) -> None`**: Adds telemetry samples to the chart buffer.
