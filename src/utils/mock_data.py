"""
Shared test fixtures for UrbanFlow unit tests.

Every POD imports from this file in their unit tests.
No POD should define their own fake data — use these constants.

If an interface changes, Aayush (POD 0) updates this file
and notifies all PODs within 24 hours.

Direction convention (matches interfaces.md):
    'N' = North (down in screen space)
    'S' = South (up in screen space)
    'E' = East  (right in screen space)
    'W' = West  (left in screen space)
"""

from typing import Dict, List

# ── Vehicles ──────────────────────────────────────────────────────────
# speed=0  → stopped, will be counted in queue length
# speed>0  → moving, will NOT be counted in queue length
# crossed=False + speed=0  → waiting at red, counted in queue
# crossed=True             → past stop line, counted in throughput

MOCK_VEHICLES: List[dict] = [
    # Stopped at red — counts toward queue
    {
        "x": 300,
        "y": 200,
        "speed": 0,
        "direction": "N",
        "lane": 0,
        "crossed": False,
        "wait_time": 8.1,
    },
    # Moving — does NOT count toward queue
    {
        "x": 310,
        "y": 200,
        "speed": 5,
        "direction": "N",
        "lane": 0,
        "crossed": False,
        "wait_time": 3.2,
    },
    # Moving from East approach
    {
        "x": 200,
        "y": 300,
        "speed": 3,
        "direction": "E",
        "lane": 2,
        "crossed": False,
        "wait_time": 0.0,
    },
    # Already crossed stop line — counts toward throughput
    {
        "x": 650,
        "y": 200,
        "speed": 5,
        "direction": "N",
        "lane": 1,
        "crossed": True,
        "wait_time": 5.0,
    },
]

# ── Queue lengths ─────────────────────────────────────────────────────
# Represents stopped vehicle counts per approach direction.
# Used by controller tests and metrics tests.
# North-heavy to exercise WaitTimeThreshold and QueueLengthExtension rules.

MOCK_QUEUES: Dict[str, int] = {
    "N": 3,
    "S": 1,
    "E": 0,
    "W": 5,
}

# ── Current green signal ──────────────────────────────────────────────
# Single active green direction — matches controller.get_signal() return type.

MOCK_SIGNAL: str = "N"

# ── Metrics snapshot ──────────────────────────────────────────────────
# Matches MetricsCalculator.get_snapshot() return structure exactly.
# Used by renderer tests (draw_dashboard) and exporter tests.

MOCK_SNAPSHOT: dict = {
    "throughput": 12,       # vehicles per hour in rolling window
    "avg_wait": 8.3,        # seconds
    "queue_length": 4,      # count of stopped vehicles
    "avg_travel": 22.1,     # seconds
}

# ── Simulation state ──────────────────────────────────────────────────
# Matches Network.get_state() return structure exactly.
# Used by renderer tests (draw_traffic) and integration tests.

MOCK_SIM_STATE: dict = {
    "vehicles": [
        {"x": v["x"], "y": v["y"], "dir": v["direction"]}
        for v in MOCK_VEHICLES
    ],
    "intersections": [
        {"id": "IN_00", "phase": "NS_GREEN"},
        {"id": "IN_01", "phase": "EW_GREEN"},
        {"id": "IN_10", "phase": "NS_GREEN"},
        {"id": "IN_11", "phase": "EW_GREEN"},
    ],
}

# ── Adaptive params path ──────────────────────────────────────────────
# Canonical path to the adaptive controller config.
# Import this instead of hardcoding the path in tests.

ADAPTIVE_PARAMS_PATH: str = "configs/adaptive_params.json"
GRID_2X2_CONFIG_PATH: str = "configs/grid_2x2.json"
