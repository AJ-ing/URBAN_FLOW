# TC-WB-06: _calc_avg_travel() — Average Travel Time Calculation

**Module:** Evaluation — MetricsCalculator._calc_avg_travel() (`metrics_calculator.py`)  
**Priority:** Medium  

## Objective

Verify that `_calc_avg_travel()` correctly computes the mean travel time across all departed vehicles by manually populating `departed_vehicles` with known travel times and checking the average.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MetricsCalculator can be instantiated with default parameters.
* [ ] `departed_vehicles` list can be manually populated for whitebox testing.

## Test Steps

1. Create a `MetricsCalculator()` with default settings.
2. Manually set `departed_vehicles` to three entries with known travel times: `(10.0, 2.0, 8.0)`, `(20.0, 3.0, 12.0)`, `(30.0, 1.0, 16.0)`.
3. Call `mc._calc_avg_travel()`.
4. Compute expected result: `(8 + 12 + 16) / 3 = 12.0`.
5. Compare actual result to expected.

## Expected Result

`_calc_avg_travel()` returns `12.0`. The formula `sum(travel_times) / len(departed_vehicles)` produces the correct mean. No `ZeroDivisionError`.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. avg_travel = 12.00, expected 12.00. Formula (8+12+16)/3 = 12.0 confirmed correct.
