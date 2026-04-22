# TC-WB-08: update() — Tracks New Vehicles by ID

**Module:** Evaluation — MetricsCalculator.update() (`metrics_calculator.py`)  
**Priority:** Medium  

## Objective

Verify that `update()` registers each new vehicle in `_vehicle_spawn_times` the first time it appears, and does not duplicate entries on subsequent frames. New vehicles added in later frames must also be tracked.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MockVehicle class available.
* [ ] `_vehicle_spawn_times` dict is accessible for whitebox inspection.

## Test Steps

1. Create a `MetricsCalculator()` with default settings.
2. Create 3 `MockVehicle` objects: `v1`, `v2`, `v3`.
3. Call `mc.update(1.0, [v1, v2], {0:0, 1:0, 2:0, 3:0})` — first tick with 2 vehicles.
4. Check `len(mc._vehicle_spawn_times)` — should be 2.
5. Call `mc.update(1.0, [v1, v2, v3], {0:0, 1:0, 2:0, 3:0})` — second tick with 3 vehicles.
6. Check `len(mc._vehicle_spawn_times)` — should be 3.
7. Confirm `v1` and `v2` were not re-registered (their spawn times remain from tick 1).

## Expected Result

After tick 1, `_vehicle_spawn_times` has 2 entries. After tick 2, it has 3 entries. Existing vehicles are not duplicated. New vehicle `v3` is added on its first appearance. The `id(vehicle)` keying correctly distinguishes individual vehicle objects.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [x] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** 2026-04-22  
**Tested Version/Commit:** pod3/metrics-and-export  
**Actual Result / Notes:**  
> Test passed. Tracked 2 vehicles after tick 1, 3 vehicles after tick 2. New vehicle correctly registered on first appearance without duplicating existing entries.
