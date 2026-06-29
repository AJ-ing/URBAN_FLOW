# All the dashboard state lives here. Keeping it separate from the
# rendering code so I can unit test it without needing pygame running.
# Anything the user clicks/presses just mutates this one object.

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

# chart shows last 120 seconds. 1 sample/sec = 120 points max
CHART_HISTORY_SECONDS: int = 120

MODE_FIXED: str = "fixed"
MODE_ADAPTIVE: str = "adaptive"
VALID_MODES: Tuple[str, ...] = (MODE_FIXED, MODE_ADAPTIVE)

# Retained as an import-compatible legacy constant; the selector state/UI is gone.
VALID_GRIDS: Tuple[str, ...] = ("1x1", "2x2", "3x3")


@dataclass(frozen=True)
class ChartSample:
    """One point on the throughput chart."""

    sim_time_s: float
    throughput_vph: float
    queue_length: int
    avg_wait_s: float


class DashboardState:
    """The single source of truth for the dashboard.

    Rules I tried to stick to:
    - no pygame imports anywhere in this file (so tests can run headless)
    - every setter validates input and returns True/False
    - reset() always brings us back to defaults no matter what state we're in
    """

    def __init__(self) -> None:
        # playback flags
        self.is_playing: bool = True
        self.step_requested: bool = False  # main loop checks + clears this
        self.reset_requested: bool = False

        self.elapsed_sim_time: float = 0.0

        self.controller_mode: str = MODE_FIXED

        # grid selector (disabled until POD 1 delivers multi-intersection networks)
        self.grid_selector_enabled: bool = False
        self.selected_grid: str = "1x1"

        # export is disabled until we have at least some data
        self.export_requested: bool = False
        self.export_enabled: bool = False
        self.last_export_path: Optional[str] = None

        # chart history - bounded so memory doesn't grow forever
        self.chart_history: Deque[ChartSample] = deque(maxlen=CHART_HISTORY_SECONDS)
        self._last_sample_time: float = -1.0  # forces first sample to record

        # latest metrics from pod 3 (or mock data if pod 3 not available)
        self.latest_snapshot: Dict[str, float] = {
            "throughput": 0.0,
            "avg_wait": 0.0,
            "avg_travel": 0.0,
            "queue_length": 0,
        }

        self.hovered_button: Optional[str] = None

    # --- playback ---

    def toggle_play(self) -> None:
        # called when user presses space or clicks play/pause
        self.is_playing = not self.is_playing

    def pause(self) -> None:
        self.is_playing = False

    def play(self) -> None:
        self.is_playing = True

    def request_step(self) -> None:
        # right arrow / step button. only useful when paused
        self.step_requested = True

    def consume_step(self) -> bool:
        # main loop calls this. returns True once then goes back to False
        # so we only step one frame per press
        pending = self.step_requested
        self.step_requested = False
        return pending

    def request_reset(self) -> None:
        self.reset_requested = True

    def consume_reset(self) -> bool:
        pending = self.reset_requested
        self.reset_requested = False
        return pending

    # --- controller mode ---

    def set_mode(self, mode: str) -> bool:
        if mode not in VALID_MODES:
            return False
        self.controller_mode = mode
        return True

    def toggle_mode(self) -> None:
        self.controller_mode = (
            MODE_ADAPTIVE if self.controller_mode == MODE_FIXED else MODE_FIXED
        )

    # --- grid selector ---

    def set_grid(self, grid: str) -> bool:
        """Set the simulation grid size if selector is enabled and grid is valid."""
        if not self.grid_selector_enabled:
            return False
        if grid not in VALID_GRIDS:
            return False
        self.selected_grid = grid
        return True

    # --- export ---

    def request_export(self) -> bool:
        # don't let user export if we haven't collected any data yet
        # otherwise we'd write an empty csv
        if not self.export_enabled:
            return False
        self.export_requested = True
        return True

    def consume_export(self) -> bool:
        pending = self.export_requested
        self.export_requested = False
        return pending

    # --- chart data ---

    def update_snapshot(
        self,
        snapshot: Dict[str, float],
        sim_time_s: float,
        sample_every_s: float = 1.0,
    ) -> None:
        """Called every frame by main loop.

        Two things happen here:
        1. update latest_snapshot so stats cards show current values
        2. add a point to the chart, but only once per second (not 60x/sec)
        """
        # defensive: pod 3's metrics sometimes return None during the
        # first few frames while it warms up
        if snapshot is None:
            return

        # .get() with fallback in case pod 3 ever drops a key
        # the "or 0.0" handles the case where the value is explicitly None
        self.latest_snapshot.update(
            {
                "throughput": float(snapshot.get("throughput", 0.0) or 0.0),
                "avg_wait": float(snapshot.get("avg_wait", 0.0) or 0.0),
                "avg_travel": float(snapshot.get("avg_travel", 0.0) or 0.0),
                "queue_length": int(snapshot.get("queue_length", 0) or 0),
            }
        )

        self.elapsed_sim_time = sim_time_s

        # only record to chart once per second (at 60fps we'd get 60 points/sec
        # which kills the chart and uses way too much memory)
        if sim_time_s - self._last_sample_time >= sample_every_s:
            self.chart_history.append(
                ChartSample(
                    sim_time_s=sim_time_s,
                    throughput_vph=self.latest_snapshot["throughput"],
                    queue_length=int(self.latest_snapshot["queue_length"]),
                    avg_wait_s=self.latest_snapshot["avg_wait"],
                )
            )
            self._last_sample_time = sim_time_s
            self.export_enabled = True  # we have data now, export is allowed

    def chart_values(self) -> List[float]:
        # what renderer plots on the y axis
        return [s.throughput_vph for s in self.chart_history]

    def chart_time_axis(self) -> List[float]:
        return [s.sim_time_s for s in self.chart_history]

    # --- reset ---

    def reset(self) -> None:
        """Back to square one. Safe to call multiple times."""
        self.is_playing = True
        self.step_requested = False
        self.reset_requested = False
        self.elapsed_sim_time = 0.0
        self.controller_mode = MODE_FIXED
        self.grid_selector_enabled = False
        self.selected_grid = "1x1"
        self.export_requested = False
        self.export_enabled = False
        self.last_export_path = None
        self.chart_history.clear()
        self._last_sample_time = -1.0
        self.latest_snapshot = {
            "throughput": 0.0,
            "avg_wait": 0.0,
            "avg_travel": 0.0,
            "queue_length": 0,
        }
        self.hovered_button = None

    def __repr__(self) -> str:
        # just for debugging when i print(state) in the repl
        return (
            f"DashboardState(playing={self.is_playing}, "
            f"mode={self.controller_mode}, "
            f"t={self.elapsed_sim_time:.1f}s, "
            f"chart_len={len(self.chart_history)})"
        )
