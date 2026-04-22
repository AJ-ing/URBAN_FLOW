# TC-P3-PV-01: Throughput Calculation Accuracy

**Module:** Evaluation — MetricsCalculator (`metrics_calculator.py`)  
**Priority:** High  

## Objective

Verify that when 10 vehicles depart within a 60-second window, the MetricsCalculator reports throughput of exactly 600 vehicles/hour (within 5% tolerance: 570–630 veh/hr). This validates the core throughput formula: `departed_in_window / window_s * 3600`.

## Pre-conditions

* [ ] `metrics_calculator.py` is present in the project root or `src/evaluation/`.
* [ ] MockVehicle class is available (no pygame dependency needed).
* [ ] MetricsCalculator can be instantiated with `window_s=300`.

## Test Steps

1. Create a `MetricsCalculator(window_s=300)`.
2. Create 10 `MockVehicle` objects with `crossed=0` and `speed=2.0`.
3. Simulate 60 seconds of ticks using `dt=1.0` (60 iterations).
4. At every 6th tick, set one vehicle's `crossed` attribute to `1` (spreading 10 departures across 60 seconds).
5. Call `metrics.update(1.0, vehicles, {0:0, 1:0, 2:0, 3:0})` each tick.
6. After all 60 ticks, call `snapshot = metrics.get_snapshot()`.
7. Read `snapshot['throughput']`.

## Expected Result

`snapshot['throughput']` is between 570 and 630 veh/hr (600 ± 5%). No division-by-zero error is raised. The formula `departed_in_window / window_s * 3600` produces the correct result.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [ ] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** YYYY-MM-DD  
**Tested Version/Commit:** [Commit Hash or Version Number]  
**Actual Result / Notes:**  
> [Record what actually happened here. If it failed, link to the bug issue.]
