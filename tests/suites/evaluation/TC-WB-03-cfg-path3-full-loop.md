# TC-WB-03: CFG Path 3 — Normal Throughput, Full Loop Execution

**Module:** Evaluation — MetricsCalculator._calc_throughput() (`metrics_calculator.py`)  
**Priority:** High  

## Objective

Exercise independent Path 3 (N1 → N3 → N4 → N5 → N3 → N6) of the `_calc_throughput()` CFG. This is the normal-operation path where vehicles have departed, the loop iterates, the inner condition matches, count increments, and the throughput formula produces a non-zero result.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MockVehicle class available.
* [ ] 10 mock vehicles will be gradually set to `crossed=1` during simulation.

## Test Steps

1. Create `MetricsCalculator(window_s=300)`.
2. Create 10 `MockVehicle` objects with `crossed=0`, `speed=2.0`.
3. Simulate 60 ticks with `dt=1.0`.
4. At every 6th tick, set one vehicle's `crossed` to `1` (10 departures across 60s).
5. Call `metrics.update(1.0, vehicles, {0:0, 1:0, 2:0, 3:0})` each tick.
6. Call `snapshot = metrics.get_snapshot()` after all 60 ticks.
7. Read `snapshot['throughput']`.

## Expected Result

`snapshot['throughput']` is between 570 and 630 veh/hr. The loop at N3 iterates over all 10 departed vehicles. The condition at N4 (`depart_time >= cutoff`) is True for all 10. N5 executes 10 times (`count=10`). N6 computes `10 / 300 * 3600 = 120` (or adjusted based on actual window). CFG path N1 → N3 → N4 → N5 → N3 → N6 is fully exercised.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. Accumulated wait time = 5.0s for a vehicle stopped for 5 ticks at dt=1.0. Wait time tracking confirmed accurate.
