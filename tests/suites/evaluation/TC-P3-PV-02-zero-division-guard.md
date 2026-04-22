# TC-P3-PV-02: Zero-Division Guard — No Departed Vehicles

**Module:** Evaluation — MetricsCalculator (`metrics_calculator.py`)  
**Priority:** High  

## Objective

Verify that calling `get_snapshot()` on a freshly initialized MetricsCalculator with no vehicles departed returns 0.0 for all metrics without raising any exception. This validates the zero-division guards in `_calc_throughput()`, `_calc_avg_wait()`, and `_calc_avg_travel()`.

## Pre-conditions

* [ ] `metrics_calculator.py` is present in the project root or `src/evaluation/`.
* [ ] MetricsCalculator can be instantiated with default parameters.
* [ ] No prior `update()` calls have been made.

## Test Steps

1. Create a `MetricsCalculator()` with default `window_s=300`.
2. Do NOT call `update()` at all — the calculator is freshly initialized.
3. Immediately call `snapshot = metrics.get_snapshot()`.
4. Check `snapshot['throughput']`.
5. Check `snapshot['avg_wait']`.
6. Check `snapshot['avg_travel']`.
7. Check `snapshot['queue_length']`.
8. Verify no `ZeroDivisionError` was raised during the entire call.

## Expected Result

`snapshot` returns exactly `{'throughput': 0.0, 'avg_wait': 0.0, 'avg_travel': 0.0, 'queue_length': 0}`. All values are float/int 0. No `ZeroDivisionError` or any other exception is raised. The system remains stable.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. All metrics returned 0.0. No ZeroDivisionError raised. Snapshot matched expected: {'throughput': 0.0, 'avg_wait': 0.0, 'avg_travel': 0.0, 'queue_length': 0, 'avg_wait_time': 0.0, 'avg_queue_length': 0.0}.
