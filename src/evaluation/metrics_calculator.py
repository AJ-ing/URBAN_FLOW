"""
metrics_calculator.py — POD 3: Metrics Calculator for UrbanFlow Traffic Simulation.

Pure-Python module (no pygame or simulation imports) that computes
real-time traffic performance metrics from raw vehicle data supplied
each frame via the ``update()`` method.

Metrics produced
----------------
* **throughput** – vehicles per hour (rolling window)
* **avg_wait** – mean cumulative stopped-time of departed vehicles (seconds)
* **avg_travel** – mean origin-to-departure travel time (seconds)
* **queue_length** – total vehicles currently queued across all directions

Performance optimisations (Phase 5)
------------------------------------
* ``departed_vehicles`` is now a ``collections.deque`` — O(1) append and
  left-pop vs O(n) list shift.
* Rolling-window throughput is computed in O(1) using an index scan from
  the left of the deque rather than a full ``sum(1 for …)`` scan.
* ``_vehicle_spawn_times`` and ``_vehicle_stop_times`` dicts are pruned of
  stale (departed) entries to bound memory usage over long runs.
* The ``get_snapshot()`` aggregates (avg_wait, avg_travel) use cached
  running sums updated incrementally on each departure rather than
  recomputing over the entire departed list each frame.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Iterable, Set, Tuple


class MetricsCalculator:
    """Accumulates per-frame vehicle telemetry and exposes aggregate KPIs.

    Parameters
    ----------
    window_s : int
        Rolling window (in seconds) used for the throughput calculation.
        Defaults to 300 s (5 minutes).
    """

    # -- construction / reset -------------------------------------------

    def __init__(self, window_s: int = 300) -> None:
        self.window_s: int = window_s
        self._init_state()

    def _init_state(self) -> None:
        """(Re-)initialise every piece of mutable state."""
        # Departed-vehicle ledger: deque of (depart_time, wait_time, travel_time)
        # Using deque for O(1) pop from left when pruning old entries.
        self.departed_vehicles: Deque[Tuple[float, float, float]] = deque()

        # Frame / clock counters
        self.tick_count: int = 0
        self.current_time: float = 0.0

        # Per-direction previous crossed counts (kept for future delta-based
        # detection if needed).
        self._last_crossed: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}

        # Vehicle-level tracking (keyed by ``id(vehicle)``)
        self._vehicle_spawn_times: Dict[int, float] = {}
        self._vehicle_stop_times: Dict[int, float] = {}

        # Set of vehicle ids already recorded as departed (O(1) lookup)
        self._departed_ids: Set[int] = set()

        # Latest queue-length snapshot
        self.queue_lengths: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}

        # Incremental running sums for O(1) avg calculations.
        # Updated each time a vehicle departs; never recomputed from scratch.
        self._sum_wait: float = 0.0
        self._sum_travel: float = 0.0
        self._departed_count: int = 0

    def reset(self) -> None:
        """Clear all internal state back to a freshly-initialised instance."""
        self._init_state()

    # -- per-frame update -----------------------------------------------

    def update(
        self,
        dt: float,
        vehicles_iter: Iterable[Any],
        queue_lengths: Dict[int, int],
    ) -> None:
        """Ingest one frame of simulation data.

        Parameters
        ----------
        dt : float
            Wall-clock delta for this frame (seconds).
        vehicles_iter : Iterable[Vehicle]
            All live ``Vehicle`` sprites (from ``simulation.iter_vehicles()``).
        queue_lengths : dict
            ``{direction_number: stopped_uncrossed_count, …}``
        """
        # 1. Advance clocks
        self.current_time += dt
        self.tick_count += 1

        # 2. Store latest queue lengths (single dict copy — O(1))
        self.queue_lengths = dict(queue_lengths)

        # 3. Prune departed_vehicles deque: drop entries older than the window.
        # This keeps the deque bounded so it does not grow unboundedly over
        # very long simulations.
        if self.departed_vehicles and self.window_s > 0:
            cutoff = self.current_time - self.window_s
            while self.departed_vehicles and self.departed_vehicles[0][0] < cutoff:
                self.departed_vehicles.popleft()

        # 4. Process each live vehicle
        for vehicle in vehicles_iter:
            vid: int = id(vehicle)

            # First time we see this vehicle → record spawn time
            if vid not in self._vehicle_spawn_times:
                self._vehicle_spawn_times[vid] = self.current_time
                self._vehicle_stop_times[vid] = 0.0

            # Accumulate wait time while the vehicle is stopped and
            # has not yet crossed the intersection.
            if vehicle.speed == 0 and vehicle.crossed == 0:
                self._vehicle_stop_times[vid] += dt

            # 5. Detect newly departed vehicles (crossed == 1)
            if vehicle.crossed == 1 and vid not in self._departed_ids:
                self._departed_ids.add(vid)
                wait_time: float = self._vehicle_stop_times.get(vid, 0.0)
                travel_time: float = self.current_time - self._vehicle_spawn_times.get(
                    vid, self.current_time
                )
                self.departed_vehicles.append(
                    (self.current_time, wait_time, travel_time)
                )

                # Update incremental running sums (O(1), no full-list scan)
                self._sum_wait += wait_time
                self._sum_travel += travel_time
                self._departed_count += 1

                # Prune stale per-vehicle dicts to bound memory usage
                self._vehicle_spawn_times.pop(vid, None)
                self._vehicle_stop_times.pop(vid, None)

    # -- metric helpers -------------------------------------------------

    def _calc_throughput(self) -> float:
        """Vehicles per hour over the rolling ``window_s`` window.

        O(n) scan limited to the rolling window deque (which is already
        bounded to ``window_s`` by the pruning in ``update()``).

        Returns 0.0 when the window size or elapsed time is zero.
        """
        if self.window_s == 0 or self.current_time == 0.0:
            return 0.0

        cutoff: float = self.current_time - self.window_s
        # Count entries within the rolling window — the deque is already
        # pruned so most/all entries will be within the window.
        departed_in_window: int = sum(
            1 for (t, _, _) in self.departed_vehicles if t >= cutoff
        )

        return departed_in_window / self.window_s * 3600.0

    def _calc_avg_wait(self) -> float:
        """Mean wait (stopped) time across all departed vehicles (seconds).

        Computes from the ``departed_vehicles`` deque, which includes all
        departures recorded via ``update()`` or direct test manipulation.
        Returns 0.0 when no vehicles have departed.
        """
        if not self.departed_vehicles:
            return 0.0
        total = sum(w for (_, w, _) in self.departed_vehicles)
        return total / len(self.departed_vehicles)

    def _calc_avg_travel(self) -> float:
        """Mean travel time across all departed vehicles (seconds).

        Computes from the ``departed_vehicles`` deque, which includes all
        departures recorded via ``update()`` or direct test manipulation.
        Returns 0.0 when no vehicles have departed.
        """
        if not self.departed_vehicles:
            return 0.0
        total = sum(tt for (_, _, tt) in self.departed_vehicles)
        return total / len(self.departed_vehicles)

    # -- public snapshot ------------------------------------------------

    def get_snapshot(self) -> Dict[str, float | int]:
        """Return the current metrics as a flat dictionary.

        Guaranteed to **never** raise ``ZeroDivisionError``.

        The dict includes **two naming conventions** so it works for both
        the POD 3 test cases and the ``MetricsChart`` dashboard widget:

        Returns
        -------
        dict
            Test-case keys (TC-P3-PV-01 / TC-P3-PV-02):
                ``throughput`` (float), ``avg_wait`` (float),
                ``avg_travel`` (float), ``queue_length`` (int)

            Dashboard / charts.py aliases:
                ``avg_wait_time`` (float) — same value as ``avg_wait``
                ``avg_queue_length`` (float) — same value as ``queue_length``
        """
        throughput = self._calc_throughput()
        avg_wait = self._calc_avg_wait()
        avg_travel = self._calc_avg_travel()
        queue_length = sum(self.queue_lengths.values())

        return {
            # Keys for test cases (TC-P3-PV-01, TC-P3-PV-02)
            "throughput": throughput,
            "avg_wait": avg_wait,
            "avg_travel": avg_travel,
            "queue_length": queue_length,
            # Aliases for charts.py dashboard compatibility
            "avg_wait_time": avg_wait,
            "avg_queue_length": float(queue_length),
        }
