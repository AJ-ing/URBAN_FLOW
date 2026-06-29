"""
test_renderer.py — POD 4: White Box Tests for Dashboard State Machine.

Covers every test case from Section 4.4.1 of the UrbanFlow Black Box
Testing Document, plus additional boundary-value and state-transition
tests to guarantee robustness.

All tests run in HEADLESS mode (no display required) — the SDL dummy
video driver is set before pygame is imported anywhere so these tests
can run on any CI machine.

Run with:
    pytest test_renderer.py -v

Author: Rushil Shandil (POD 4 — Visualization)
"""

from __future__ import annotations

import os

# MUST be set before any pygame import chain (CI / headless safety).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest

from src.visualization.dashboard_state import (
    CHART_HISTORY_SECONDS,
    MODE_ADAPTIVE,
    MODE_FIXED,
    VALID_GRIDS,
    ChartSample,
    DashboardState,
)

# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def state() -> DashboardState:
    """Fresh DashboardState for each test."""
    return DashboardState()


@pytest.fixture
def mock_snapshot() -> dict:
    """Canonical POD 3 snapshot shape — matches MetricsCalculator.get_snapshot()."""
    return {
        "throughput": 450.0,
        "avg_wait": 12.3,
        "avg_travel": 28.7,
        "queue_length": 6,
    }


# ===========================================================================
# TC-P4-RS-01 — Construction and Defaults
# ===========================================================================


class TestConstruction:
    """Verify factory-fresh state matches specification."""

    def test_defaults_playing_true(self, state):
        assert state.is_playing is True

    def test_defaults_mode_fixed(self, state):
        assert state.controller_mode == MODE_FIXED

    def test_defaults_elapsed_zero(self, state):
        assert state.elapsed_sim_time == 0.0

    def test_defaults_no_pending_actions(self, state):
        assert state.step_requested is False
        assert state.reset_requested is False
        assert state.export_requested is False

    def test_defaults_chart_empty(self, state):
        assert len(state.chart_history) == 0

    def test_defaults_export_disabled(self, state):
        assert state.export_enabled is False

    def test_defaults_grid_selector_disabled(self, state):
        """Grid selector is placeholder (POD 1 not yet integrated)."""
        assert state.grid_selector_enabled is False


# ===========================================================================
# TC-P4-RS-02 — Playback Controls: Space Toggle / R Reset
# ===========================================================================


class TestPlaybackToggle:
    """SPACE key → is_playing flips. Covers spec line in TC-P4-RS-02."""

    def test_space_pauses_when_playing(self, state):
        assert state.is_playing is True
        state.toggle_play()
        assert state.is_playing is False

    def test_space_resumes_when_paused(self, state):
        state.toggle_play()  # → paused
        state.toggle_play()  # → playing
        assert state.is_playing is True

    def test_pause_is_idempotent(self, state):
        state.pause()
        state.pause()
        assert state.is_playing is False

    def test_play_is_idempotent(self, state):
        state.play()
        state.play()
        assert state.is_playing is True

    def test_rapid_toggle_no_race(self, state):
        """Simulate spam-clicking play/pause — must end deterministically."""
        for _ in range(1000):
            state.toggle_play()
        # 1000 toggles from True → back to True
        assert state.is_playing is True


class TestResetRequest:
    """R key → reset_requested latched, consumed once by main loop."""

    def test_reset_request_sets_flag(self, state):
        state.request_reset()
        assert state.reset_requested is True

    def test_reset_consumed_exactly_once(self, state):
        state.request_reset()
        assert state.consume_reset() is True
        assert state.consume_reset() is False  # already consumed

    def test_reset_method_returns_to_defaults(self, state):
        state.toggle_play()
        state.set_mode(MODE_ADAPTIVE)
        state.elapsed_sim_time = 99.9
        state.chart_history.append(ChartSample(1.0, 500.0, 3, 10.0))
        state.reset()
        assert state.is_playing is True
        assert state.controller_mode == MODE_FIXED
        assert state.elapsed_sim_time == 0.0
        assert len(state.chart_history) == 0

    def test_reset_is_idempotent(self, state):
        state.reset()
        state.reset()
        assert state.is_playing is True


class TestStepRequest:
    """Right-arrow → step one frame while paused."""

    def test_step_request_latches(self, state):
        state.request_step()
        assert state.step_requested is True

    def test_step_consumed_once(self, state):
        state.request_step()
        assert state.consume_step() is True
        assert state.consume_step() is False


# ===========================================================================
# Controller Mode State Transitions
# ===========================================================================


class TestControllerMode:
    """A key → adaptive, F key → fixed."""

    def test_set_adaptive(self, state):
        assert state.set_mode(MODE_ADAPTIVE) is True
        assert state.controller_mode == MODE_ADAPTIVE

    def test_set_fixed(self, state):
        state.set_mode(MODE_ADAPTIVE)
        assert state.set_mode(MODE_FIXED) is True
        assert state.controller_mode == MODE_FIXED

    def test_invalid_mode_rejected(self, state):
        assert state.set_mode("random_mode") is False
        assert state.controller_mode == MODE_FIXED  # unchanged

    def test_empty_mode_rejected(self, state):
        assert state.set_mode("") is False

    def test_toggle_flips(self, state):
        state.toggle_mode()
        assert state.controller_mode == MODE_ADAPTIVE
        state.toggle_mode()
        assert state.controller_mode == MODE_FIXED


# ===========================================================================
# Grid Selector (Placeholder — greyed out)
# ===========================================================================


class TestGridSelector:
    """Selector disabled until POD 1 delivers multi-intersection network."""

    def test_grid_change_ignored_when_disabled(self, state):
        assert state.set_grid("3x3") is False
        assert state.selected_grid == "1x1"  # unchanged

    def test_grid_change_accepted_when_enabled(self, state):
        state.grid_selector_enabled = True
        assert state.set_grid("2x2") is True
        assert state.selected_grid == "2x2"

    def test_invalid_grid_rejected_even_when_enabled(self, state):
        state.grid_selector_enabled = True
        assert state.set_grid("5x5") is False

    @pytest.mark.parametrize("grid", VALID_GRIDS)
    def test_all_valid_grids_accepted(self, state, grid):
        state.grid_selector_enabled = True
        assert state.set_grid(grid) is True


# ===========================================================================
# Export Button Gating
# ===========================================================================


class TestExportGating:
    """Export button must be disabled until data exists (no-empty-CSV rule)."""

    def test_export_rejected_when_no_data(self, state):
        assert state.request_export() is False

    def test_export_accepted_after_snapshot(self, state, mock_snapshot):
        state.update_snapshot(mock_snapshot, sim_time_s=1.0)
        assert state.request_export() is True

    def test_export_consumed_once(self, state, mock_snapshot):
        state.update_snapshot(mock_snapshot, sim_time_s=1.0)
        state.request_export()
        assert state.consume_export() is True
        assert state.consume_export() is False


# ===========================================================================
# Snapshot Ingestion (POD 3 ↔ POD 4 Interface)
# ===========================================================================


class TestSnapshotIngestion:
    """update_snapshot() must survive malformed POD 3 data gracefully."""

    def test_valid_snapshot_recorded(self, state, mock_snapshot):
        state.update_snapshot(mock_snapshot, sim_time_s=1.0)
        assert state.latest_snapshot["throughput"] == 450.0
        assert state.latest_snapshot["queue_length"] == 6

    def test_none_snapshot_handled(self, state):
        """POD 3 may return None during warm-up. Must not crash."""
        state.update_snapshot(None, sim_time_s=1.0)  # type: ignore[arg-type]
        # State unchanged
        assert state.latest_snapshot["throughput"] == 0.0

    def test_missing_key_defaults_to_zero(self, state):
        state.update_snapshot({"throughput": 100.0}, sim_time_s=1.0)
        assert state.latest_snapshot["throughput"] == 100.0
        assert state.latest_snapshot["avg_wait"] == 0.0

    def test_none_value_defaults_to_zero(self, state):
        """Defensive against {'throughput': None} — has happened in POD 3 warm-up."""
        state.update_snapshot({"throughput": None}, sim_time_s=1.0)
        assert state.latest_snapshot["throughput"] == 0.0

    def test_chart_samples_at_1hz(self, state, mock_snapshot):
        # Ten updates within the first second → only 1 sample
        for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
            state.update_snapshot(mock_snapshot, sim_time_s=t)
        assert len(state.chart_history) == 1

    def test_chart_samples_across_seconds(self, state, mock_snapshot):
        for t in range(5):
            state.update_snapshot(mock_snapshot, sim_time_s=float(t))
        assert len(state.chart_history) == 5


# ===========================================================================
# Chart Buffer Memory Safety
# ===========================================================================


class TestChartBuffer:
    """Deque must never grow past CHART_HISTORY_SECONDS."""

    def test_buffer_bounded(self, state, mock_snapshot):
        for t in range(CHART_HISTORY_SECONDS + 50):
            state.update_snapshot(mock_snapshot, sim_time_s=float(t))
        assert len(state.chart_history) == CHART_HISTORY_SECONDS

    def test_oldest_evicted_first(self, state):
        """After overflow, the oldest sample must be gone."""
        for t in range(CHART_HISTORY_SECONDS + 10):
            snap = {"throughput": float(t), "avg_wait": 0, "queue_length": 0}
            state.update_snapshot(snap, sim_time_s=float(t))
        values = state.chart_values()
        assert values[0] == 10.0  # first 10 evicted
        assert values[-1] == float(CHART_HISTORY_SECONDS + 9)


# ===========================================================================
# TC-P4-RS-01 — Headless 100-Frame Stress Test
# ===========================================================================


class TestHeadless100Frames:
    """Spec: 100 consecutive state updates in headless mode → no exception."""

    def test_100_frames_no_crash(self, state, mock_snapshot):
        for frame in range(100):
            sim_t = frame * 0.1
            state.update_snapshot(mock_snapshot, sim_time_s=sim_t)
            if frame % 10 == 0:
                state.toggle_play()
        # If we got here without raising, the test passes
        assert state.elapsed_sim_time == pytest.approx(9.9)


# ===========================================================================
# Integration — Full Reset Cycle
# ===========================================================================


class TestFullResetCycle:
    """After dirtying every field, reset() → identical to fresh construction."""

    def test_dirty_then_reset_equals_fresh(self, mock_snapshot):
        dirty = DashboardState()
        dirty.toggle_play()
        dirty.set_mode(MODE_ADAPTIVE)
        dirty.request_step()
        dirty.request_reset()
        for t in range(10):
            dirty.update_snapshot(mock_snapshot, sim_time_s=float(t))
        dirty.request_export()
        dirty.reset()

        fresh = DashboardState()
        assert dirty.is_playing == fresh.is_playing
        assert dirty.controller_mode == fresh.controller_mode
        assert dirty.elapsed_sim_time == fresh.elapsed_sim_time
        assert len(dirty.chart_history) == len(fresh.chart_history)
        assert dirty.export_enabled == fresh.export_enabled
