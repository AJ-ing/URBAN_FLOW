# UrbanFlow — Frozen Module Interface Contracts

**File:** `docs/api/interfaces.md`
**Version:** 2.1 (Option C — Fixed)
**Author:** Aayush Jain (POD 0 — Integration Lead)
**Status:** FROZEN — merged to `develop` branch
**Date:** March 23, 2026

> These interfaces are the single source of truth for all inter-module contracts.
> No POD may change a method signature, parameter name, or class name without
> Aayush's sign-off and a 24-hour notification to all PODs.

---

## How to use this document

Every POD imports from `src/utils/mock_data.py` for unit tests — never invent
custom fake data. If an interface changes, Aayush updates `mock_data.py` and
notifies all PODs within 24 hours via GitHub Discussions.

---

## Interface 1 — `src/network.py` (POD 1: C N Sai Tarun)

> **FIX 1:** Class is named `Network`, **not** `NetworkEngine`. Any import of
> `NetworkEngine` anywhere in the codebase is a merge blocker.

```python
from typing import Dict, List

class Network:
    def __init__(self, config_path: str) -> None:
        """Load grid config from JSON and build all intersections and roads."""
        ...

    def get_intersections(self) -> List[dict]:
        """Return list of intersection dicts: [{'id': str, 'phase': str}, ...]"""
        ...

    def get_queue_lengths(self) -> Dict[str, int]:
        """Aggregate queue lengths across all intersections.

        Returns: {'N': int, 'S': int, 'E': int, 'W': int}
        """
        ...

    def apply_signals(self, signal_commands: dict) -> None:
        """Apply signal commands to intersections.

        Args:
            signal_commands: {'all': 'N'} to apply same direction to all,
                             or {'IN_00': 'N', 'IN_01': 'E'} per-intersection.
        """
        ...

    def tick(self, dt: float) -> None:
        """Advance simulation by dt seconds: move vehicles, handle queues,
        generate arrivals, route departures."""
        ...

    def get_state(self) -> dict:
        """Return current simulation snapshot.

        Returns:
            {
                'vehicles': [{'x': float, 'y': float, 'dir': str}, ...],
                'intersections': [{'id': str, 'phase': str}, ...]
            }
        """
        ...
```

### Correctness rules

- `tick(dt)` must complete in under 5 ms for a 2×2 grid with 200 vehicles.
- Same `random_seed` must produce identical vehicle positions at every tick (determinism).
- `Vehicle.route` is an ordered list of intersection IDs. When exhausted, the
  vehicle exits the network. **No pygame, no colors, no drawing code in this file.**

---

## Interface 2 — `src/controller.py` (POD 2: Laural Alex Jacob & Dev Mangal)

> **FIX 2:** `get_signal()` is **singular** — not `get_signals()`.
> **FIX 5:** `tick(dt)` **must** be called every frame before `get_signal()`.
> The integration loop calls `controller.tick(dt)` first, then `controller.get_signal(queues)`.
> Controllers that skip `tick()` will have broken internal timers.

```python
from typing import Dict

class FixedTimeController:
    PLAN_A = {'green_s': 25, 'yellow_s': 3}   # light traffic,    112s cycle
    PLAN_B = {'green_s': 39, 'yellow_s': 3}   # moderate traffic, 168s cycle (baseline for 35% test)
    PLAN_C = {'green_s': 54, 'yellow_s': 3}   # heavy traffic,    228s cycle

    def __init__(self, green_s: int = 30, yellow_s: int = 3) -> None:
        ...

    def tick(self, dt: float) -> None:
        """Advance internal timer. MUST be called each frame from the main loop."""
        ...

    def get_signal(self, queue_lengths: Dict[str, int]) -> str:
        """Return current green direction. Read-only — no timer logic here.

        Args:
            queue_lengths: {'N': int, 'S': int, 'E': int, 'W': int}
                           Received but NOT used — this is fixed-time.
        Returns:
            One of: 'N', 'S', 'E', 'W'
        """
        ...


class AdaptiveController:
    def __init__(self, params_path: str) -> None:
        """Load adaptive parameters from JSON (configs/adaptive_params.json)."""
        ...

    def tick(self, dt: float) -> None:
        """Advance all internal timers (red_timers, service_time).
        MUST be called each frame from the main loop."""
        ...

    def get_signal(self, queue_lengths: Dict[str, int]) -> str:
        """Evaluate rules against current state. Returns active green direction.

        Args:
            queue_lengths: {'N': int, 'S': int, 'E': int, 'W': int}
        Returns:
            One of: 'N', 'S', 'E', 'W'
        """
        ...
```

### Correctness rules

- `N` and `E` must **never** both be green simultaneously (safety invariant).
- Two instances with the same parameters must return an identical sequence for
  10 000 calls (determinism).
- `AdaptiveController` must show ≥ 35 % throughput improvement vs
  `FixedTimeController.PLAN_B` on `grid_2x2.json`, `seed=42`, 300 ticks.

### Six adaptive rules (all thresholds in `configs/adaptive_params.json`)

| Priority | Rule | Trigger |
|----------|------|---------|
| 100 | `WaitTimeThreshold` | Any red direction waiting > `max_wait_s` (45 s). Prevents starvation. |
| 90 | `QueueLengthExtension` | Extend green when queue > threshold (default 5). Max 1 extension per phase. |
| 80 | `EarlyTermination` | Switch when current queue = 0 AND `min_green_s` (8 s) elapsed. |
| 70 | `DemandResponsiveSelection` | Switch to highest-queue direction when current green queue = 0. |
| 60 | `PeakHourBoost` | Extend green by `boost_factor` (1.3×) during `peak_start_s` to `peak_end_s`. |
| 50 | `BalancedServiceGuarantee` | Switch to under-served direction if one direction has > 2× service time of another. |

---

## Interface 3 — `src/metrics.py` (POD 3: Pranav Vishwakarma)

> **FIX 6:** Second parameter is `active_direction: str` (e.g. `'N'`),
> **not** `signal_state`. Any code using `signal_state` as the parameter name
> will fail the integration test.

```python
from typing import Dict

class MetricsCalculator:
    def __init__(self, window_s: float = 300.0) -> None:
        """
        Args:
            window_s: Rolling window size in seconds for throughput calculation.
        """
        ...

    def update(self, vehicles: list, active_direction: str) -> None:
        """Ingest one frame of simulation data.

        Args:
            vehicles: List of vehicle dicts from network.get_state()['vehicles'].
                      Each dict has at least: speed (float), crossed (bool),
                      wait_time (float), travel_time (float).
            active_direction: The currently green direction, e.g. 'N'.
        """
        ...

    def get_snapshot(self) -> dict:
        """Return current metric values.

        Returns:
            {
                'throughput':   float,  # vehicles/hour in rolling window
                'avg_wait':     float,  # seconds
                'avg_travel':   float,  # seconds
                'queue_length': int,    # count of stopped, uncrossed vehicles
            }
        Notes:
            Returns 0.0 for all metrics if no vehicles have departed yet.
            Never divides by zero.
        """
        ...
```

### Metric formulas (must match exactly)

| Metric | Formula |
|--------|---------|
| Throughput | `departed_in_window / window_s * 3600` (veh/hr) |
| Avg wait | `sum(v.wait_time for v in departed) / len(departed)` |
| Avg travel | `sum(v.travel_time for v in departed) / len(departed)` |
| Queue length | `count of vehicles where speed == 0 and crossed == False` |

---

## Interface 4 — `src/renderer.py` (POD 4: Rushil Shandil)

```python
import pygame

class Renderer:
    WINDOW_W: int = 1280
    WINDOW_H: int = 720
    PANEL_X:  int = 768   # left 768 px = traffic view; right 512 px = dashboard
    PANEL_W:  int = 512

    # Integration loop reads these three properties every frame:
    is_running:        bool   # False → quit the main loop
    is_playing:        bool   # False → simulation is paused
    speed_multiplier:  float  # range 0.25 – 10.0

    def __init__(self) -> None:
        """Call pygame.init() and open 1280×720 window here.
        Integration loop must NOT call pygame.init() separately."""
        ...

    def handle_events(self) -> None:
        """Process all pygame events. Sets is_running=False on QUIT.
        Keyboard shortcuts: Space=play/pause, R=reset, S=step, +/-=speed."""
        ...

    def draw_traffic(self, sim_state: dict) -> None:
        """Draw roads, vehicles, and traffic lights in left 768 px.

        Args:
            sim_state: dict from network.get_state()
                       Keys: 'vehicles', 'intersections'
        """
        ...

    def draw_dashboard(self, snapshot: dict) -> None:
        """Draw dark-gray panel (30,30,30) from x=768 to 1280 with:
        - 2 px white divider at x=768
        - Stats box: 2×2 grid of Throughput / Avg Wait / Avg Travel / Queue
        - Live polyline charts: throughput (green) + avg wait (amber)
        - Control panel: Play/Pause/Step/Reset + speed slider + controller selector

        Args:
            snapshot: dict from metrics.get_snapshot()
        """
        ...
```

### Correctness rules

- Renderer tests must set `os.environ['SDL_VIDEODRIVER'] = 'dummy'` and
  `os.environ['SDL_AUDIODRIVER'] = 'dummy'` **before** any `import pygame`.
  See FIX 8 in the spec.
- `draw_dashboard` must not crash when `snapshot` contains all-zero values.
- Dashboard must render at ≥ 30 FPS with the simulation running (measured via
  `pygame.time.Clock()`).

---

## Integration loop contract (POD 0 — `main.py`)

The canonical call order every frame is:

```python
dt = clock.tick(60) / 1000.0
renderer.handle_events()

if renderer.is_playing:
    controller.tick(dt * renderer.speed_multiplier)   # FIX 5: tick BEFORE get_signal
    queues      = network.get_queue_lengths()
    signal_cmd  = controller.get_signal(queues)        # FIX 2: singular
    network.apply_signals({'all': signal_cmd})
    network.tick(dt * renderer.speed_multiplier)
    state       = network.get_state()
    metrics.update(state['vehicles'], signal_cmd)      # FIX 6: active_direction

renderer.draw_traffic(network.get_state())
renderer.draw_dashboard(metrics.get_snapshot())
pygame.display.flip()
```

Violating this order — especially calling `get_signal()` before `tick()` —
is a correctness bug and will cause the CI integration test to fail.

---

## Mock data (`src/utils/mock_data.py`)

All PODs import from this file for unit tests. Do **not** invent custom fake data.

```python
MOCK_VEHICLES = [
    {'x': 300, 'y': 200, 'speed': 5,  'direction': 'N', 'lane': 0,
     'crossed': False, 'wait_time': 3.2, 'travel_time': 0.0},
    {'x': 310, 'y': 200, 'speed': 0,  'direction': 'N', 'lane': 0,
     'crossed': False, 'wait_time': 8.1, 'travel_time': 0.0},
    {'x': 200, 'y': 300, 'speed': 3,  'direction': 'E', 'lane': 2,
     'crossed': False, 'wait_time': 0.0, 'travel_time': 0.0},
]

MOCK_QUEUES    = {'N': 3, 'S': 1, 'E': 0, 'W': 5}
MOCK_SIGNAL    = 'N'
MOCK_SNAPSHOT  = {
    'throughput':   12.0,
    'avg_wait':     8.3,
    'avg_travel':   22.1,
    'queue_length': 4,
}
```

---

## Change log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 2.1 | 2026-03-23 | Aayush Jain | Initial freeze. FIX 1-2, 5-8, 10 applied. Merged to `develop`. |

---

*IS F341 — Software Engineering | BITS Pilani, Goa Campus | Group 2*
