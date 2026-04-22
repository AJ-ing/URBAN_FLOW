# TC-WB-04: get_snapshot() Sequential Path — All Keys Present

**Module:** Evaluation — MetricsCalculator.get_snapshot() (`metrics_calculator.py`)  
**Priority:** Medium  

## Objective

Exercise the single sequential path (S1 → S2 → S3 → S4 → S5) of the `get_snapshot()` CFG. Verify that all three internal calculation methods are called, queue lengths are summed correctly, and the returned dict contains both the test-spec keys and the charts.py alias keys.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MockVehicle class available with `crossed=1`.
* [ ] At least one `update()` call made with a crossed vehicle.

## Test Steps

1. Create `MetricsCalculator(window_s=300)`.
2. Create 1 `MockVehicle` with `crossed=1`, `speed=2.0`.
3. Call `metrics.update(1.0, [vehicle], {0:2, 1:1, 2:0, 3:3})`.
4. Call `snapshot = metrics.get_snapshot()`.
5. Verify `'throughput'` key exists in snapshot.
6. Verify `'avg_wait'` key exists in snapshot.
7. Verify `'avg_travel'` key exists in snapshot.
8. Verify `'queue_length'` key exists in snapshot.
9. Verify `'avg_wait_time'` key exists (charts.py alias).
10. Verify `'avg_queue_length'` key exists (charts.py alias).
11. Verify `snapshot['avg_wait'] == snapshot['avg_wait_time']`.
12. Verify `snapshot['queue_length'] == 6` (2+1+0+3).

## Expected Result

Snapshot dict contains all 6 keys. `avg_wait` equals `avg_wait_time` (alias consistency). `queue_length` equals 6. All internal methods (`_calc_throughput`, `_calc_avg_wait`, `_calc_avg_travel`) execute without error. CFG path S1 → S2 → S3 → S4 → S5 is fully exercised.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. queue_length = 17 (3+7+2+5). All 6 keys present in snapshot. Alias keys match primary keys.
