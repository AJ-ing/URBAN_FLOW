# TC-WB-05: _calc_avg_wait() — Average Wait Time Calculation

**Module:** Evaluation — MetricsCalculator._calc_avg_wait() (`metrics_calculator.py`)  
**Priority:** Medium  

## Objective

Verify that `_calc_avg_wait()` correctly computes the mean wait (stopped) time across all departed vehicles by manually populating `departed_vehicles` with known wait times and checking the average.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MetricsCalculator can be instantiated with default parameters.
* [ ] `departed_vehicles` list can be manually populated for whitebox testing.

## Test Steps

1. Create a `MetricsCalculator()` with default settings.
2. Manually set `departed_vehicles` to three entries with known wait times: `(10.0, 5.0, 10.0)`, `(20.0, 10.0, 15.0)`, `(30.0, 15.0, 20.0)`.
3. Call `mc._calc_avg_wait()`.
4. Compute expected result: `(5 + 10 + 15) / 3 = 10.0`.
5. Compare actual result to expected.

## Expected Result

`_calc_avg_wait()` returns `10.0`. The formula `sum(wait_times) / len(departed_vehicles)` produces the correct mean. No `ZeroDivisionError`.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [ ] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** YYYY-MM-DD  
**Tested Version/Commit:** [Commit Hash or Version Number]  
**Actual Result / Notes:**  
> [Record what actually happened here. If it failed, link to the bug issue.]
