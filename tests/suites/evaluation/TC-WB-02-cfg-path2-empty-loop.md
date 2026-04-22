# TC-WB-02: CFG Path 2 — Empty Departed List, Loop Skipped

**Module:** Evaluation — MetricsCalculator._calc_throughput() (`metrics_calculator.py`)  
**Priority:** Medium  

## Objective

Exercise independent Path 2 (N1 → N3 → N6) of the `_calc_throughput()` CFG. When `current_time > 0` but `departed_vehicles` is empty, the zero-division guard passes (N1 False) but the for-loop at N3 has no items, so execution skips directly to N6 (return).

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MockVehicle class available with `crossed=0` and `speed=2.0`.
* [ ] At least one `update()` call made so `current_time > 0`.

## Test Steps

1. Create `MetricsCalculator(window_s=300)`.
2. Create 5 `MockVehicle` objects with `crossed=0` (none have departed).
3. Call `update(1.0, vehicles, {0:3, 1:2, 2:0, 3:0})` ten times.
4. `current_time` is now 10.0 (guard passes), but `departed_vehicles` is still empty.
5. Call `snapshot = metrics.get_snapshot()`.
6. Check `snapshot['throughput']` and `snapshot['queue_length']`.

## Expected Result

`snapshot['throughput']` is 0.0 (count=0, formula yields 0). `snapshot['queue_length']` is 5. The for-loop at N3 is entered but immediately exits (no items). CFG path N1 → N3 → N6 is fully exercised.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. Throughput = 180.0 veh/hr, expected 180.0. 5 vehicles inside window correctly counted, 3 outside window correctly excluded.
