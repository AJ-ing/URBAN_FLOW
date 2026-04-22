# TC-WB-07: reset() — Clears All Internal State

**Module:** Evaluation — MetricsCalculator.reset() (`metrics_calculator.py`)  
**Priority:** High  

## Objective

Verify that after populating the MetricsCalculator with vehicle data and non-zero metrics, calling `reset()` returns all snapshot values back to zero and clears all internal tracking state.

## Pre-conditions

* [ ] `metrics_calculator.py` is importable without pygame.
* [ ] MockVehicle class available with configurable `crossed` and `speed`.
* [ ] MetricsCalculator must first be driven to a non-zero state before reset.

## Test Steps

1. Create a `MetricsCalculator()` with default settings.
2. Create 3 `MockVehicle` objects with `crossed=0`, `speed=2.0`.
3. Run 10 update ticks with `dt=1.0`. After tick 3, set all vehicles to `crossed=1`.
4. Call `get_snapshot()` and confirm `throughput > 0` (non-zero state).
5. Call `mc.reset()`.
6. Call `get_snapshot()` again.
7. Verify the post-reset snapshot equals `{'throughput': 0.0, 'avg_wait': 0.0, 'avg_travel': 0.0, 'queue_length': 0, 'avg_wait_time': 0.0, 'avg_queue_length': 0.0}`.

## Expected Result

After `reset()`, `get_snapshot()` returns all zeros. `departed_vehicles` is empty. `_vehicle_spawn_times` is empty. `current_time` is 0.0. `tick_count` is 0. The calculator behaves as if freshly constructed.

---

## Execution Record

*Leave this section blank until you actually run the test.*

**Status:** [ ] Pass | [ ] Fail | [ ] Blocked  
**Date Tested:** YYYY-MM-DD  
**Tested Version/Commit:** [Commit Hash or Version Number]  
**Actual Result / Notes:**  
> [Record what actually happened here. If it failed, link to the bug issue.]
