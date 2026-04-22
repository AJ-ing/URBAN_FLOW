# TC-WB-01: CFG Path 1 — Zero-Division Guard Early Exit

**Module:** Evaluation — MetricsCalculator._calc_throughput() (`metrics_calculator.py`)  
**Priority:** High  

## Objective

Exercise independent Path 1 (N1 → N2) of the `_calc_throughput()` CFG. When `current_time == 0`, the zero-division guard must fire and return 0.0 immediately without entering the loop.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] No `update()` calls made — `current_time` remains 0.0.
* [ ] `departed_vehicles` is empty.

## Test Steps

1. Create `MetricsCalculator(window_s=300)`.
2. Call `get_snapshot()` immediately (no `update()` calls).
3. Internally, `_calc_throughput()` checks `self.current_time == 0` at node N1.
4. Condition is True — execution flows to N2 (return 0.0).
5. Verify all snapshot values are 0.

## Expected Result

`_calc_throughput()` returns 0.0 via the early exit at N2. No loop iteration occurs. No `ZeroDivisionError`. CFG path N1 → N2 is fully exercised.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [ ] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** YYYY-MM-DD  
**Tested Version/Commit:** [Commit Hash or Version Number]  
**Actual Result / Notes:**  
> [Record what actually happened here. If it failed, link to the bug issue.]
