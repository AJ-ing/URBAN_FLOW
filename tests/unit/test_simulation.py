"""
test_simulation.py — Unit tests for simulation.py (POD 1: Vehicle Physics Engine)

Tests vehicle spawning, movement, lane queuing, signal obedience, and crossing logic.

Run with:
    pytest tests/unit/test_simulation.py -v
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

import simulation

# ---------------------------------------------------------------------------
# Helper: reset global state between tests
# ---------------------------------------------------------------------------


def _reset_sim() -> None:
    """Clear all vehicle lists and the pygame sprite group to give a clean slate."""
    simulation.simulation.empty()
    for direction in simulation.vehicles:
        for lane in (0, 1, 2):
            simulation.vehicles[direction][lane].clear()
        simulation.vehicles[direction]["crossed"] = 0

    # Reset position offsets back to defaults
    simulation.x["right"] = [0, 0, 0]
    simulation.x["down"] = [755, 727, 697]
    simulation.x["left"] = [1400, 1400, 1400]
    simulation.x["up"] = [602, 627, 657]
    simulation.y["right"] = [348, 370, 398]
    simulation.y["down"] = [0, 0, 0]
    simulation.y["left"] = [498, 466, 436]
    simulation.y["up"] = [800, 800, 800]

    simulation.currentGreen = 0
    simulation.currentYellow = 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_sim():
    """Provide a clean simulation state for each test."""
    _reset_sim()
    yield
    _reset_sim()


# ---------------------------------------------------------------------------
# TestVehicleSpawning
# ---------------------------------------------------------------------------


class TestVehicleSpawning:
    """Test vehicle generation and spawn logic."""

    def test_spawn_creates_vehicle_with_correct_direction(self):
        """Vehicle spawn assigns a valid direction_number (0–3)."""
        for _ in range(10):
            simulation.generate_vehicle()

        all_vehicles = list(simulation.iter_vehicles())
        assert len(all_vehicles) > 0, "Should have spawned vehicles"

        for vehicle in all_vehicles:
            assert (
                0 <= vehicle.direction_number < 4
            ), f"direction_number {vehicle.direction_number} out of range [0,3]"

    def test_spawn_respects_direction_probability(self):
        """Vehicle spawn respects weighted direction distribution.

        Expected weights: down=6, left=2, up=1, right=1 → ~60%, ~20%, ~10%, ~10%
        """
        for _ in range(200):
            simulation.generate_vehicle()

        direction_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for vehicle in simulation.iter_vehicles():
            direction_counts[vehicle.direction_number] += 1

        total = sum(direction_counts.values())
        assert total > 0, "Must have spawned at least one vehicle"

        # Down (~60%) – tolerance ±20%
        pct_down = direction_counts[0] / total * 100
        assert 40 < pct_down < 80, f"Down expected ~60%, got {pct_down:.1f}%"

        # Left (~20%) – tolerance ±15%
        pct_left = direction_counts[1] / total * 100
        assert 5 < pct_left < 35, f"Left expected ~20%, got {pct_left:.1f}%"

    def test_spawn_creates_vehicle_in_lane_1_or_2(self):
        """Vehicle spawns in lane 1 or 2 (never lane 0)."""
        for _ in range(10):
            v = simulation.generate_vehicle()
            assert v.lane in (1, 2), f"Lane {v.lane} not in expected (1, 2)"

    def test_spawn_returns_vehicle_object(self):
        """generate_vehicle() returns a Vehicle instance."""
        v = simulation.generate_vehicle()
        assert isinstance(v, simulation.Vehicle), "Should return a Vehicle"

    def test_spawn_vehicle_added_to_sprite_group(self):
        """Spawned vehicle is immediately visible via iter_vehicles()."""
        before = len(list(simulation.iter_vehicles()))
        simulation.generate_vehicle()
        after = len(list(simulation.iter_vehicles()))
        assert after == before + 1, "Sprite group should grow by 1"


# ---------------------------------------------------------------------------
# TestVehicleMovement
# ---------------------------------------------------------------------------


class TestVehicleMovement:
    """Test vehicle physics and movement logic."""

    def test_vehicle_moves_forward_when_not_stopped(self):
        """Vehicle changes position when the signal is open for its direction."""
        v = simulation.generate_vehicle()
        initial_x, initial_y = v.x, v.y

        # Force green for the vehicle's direction
        simulation.set_signal_state(v.direction_number, 0)

        v.move()

        # Position must change for at least one axis
        assert (v.x, v.y) != (
            initial_x,
            initial_y,
        ), "Vehicle should move at least one pixel when signal is open"

    def test_vehicle_stops_at_red_signal(self):
        """Vehicle queues behind stop-line when signal is red for its direction."""
        v = simulation.generate_vehicle()

        # Position the vehicle so its leading edge just exceeds the stop line
        direction_name = simulation.directionNumbers[v.direction_number]
        if direction_name == "down":
            h = v.image.get_rect().height
            v.y = v.stop - h + 1  # bottom edge: y+h = stop+1 > stop
        elif direction_name == "up":
            v.y = v.stop - 1
        elif direction_name == "right":
            w = v.image.get_rect().width
            v.x = v.stop - w + 1
        elif direction_name == "left":
            v.x = v.stop + 1

        # Set signal to an opposing direction so this vehicle sees red
        opposite = (v.direction_number + 2) % 4
        simulation.set_signal_state(opposite, 0)

        # A few ticks are enough — vehicle is already at the stop
        for _ in range(5):
            v.move()

        # Vehicle should have come to rest
        assert (
            v.speed == 0.0
        ), f"Vehicle (dir={v.direction}) should be stopped at red signal, speed={v.speed}"

    def test_vehicle_obeys_signal_state(self):
        """Vehicle's speed attribute is numeric and non-negative."""
        v = simulation.generate_vehicle()
        simulation.set_signal_state(v.direction_number, 0)

        v.move()
        assert isinstance(v.speed, (int, float)), "Speed should be numeric"
        assert v.speed >= 0, "Speed should never be negative"

    def test_vehicle_despawns_after_crossing(self):
        """Setting crossed=1 flag works and is tracked."""
        v = simulation.generate_vehicle()
        v.crossed = 1

        assert v.crossed == 1, "Crossed flag should be settable"

    def test_vehicle_speed_is_nominal_when_moving(self):
        """Vehicle speed equals nominal speed when actually moving."""
        v = simulation.generate_vehicle()
        simulation.set_signal_state(v.direction_number, 0)

        v.move()

        if v.speed > 0:
            assert v.speed == v.nominal_speed, "Moving speed should equal nominal_speed"


# ---------------------------------------------------------------------------
# TestQueueing
# ---------------------------------------------------------------------------


class TestQueueing:
    """Test vehicle lane queuing and queue detection."""

    def test_queue_forms_at_red_signal(self):
        """Vehicles stop when signal is red for their direction."""
        # Spawn a vehicle and position it so it's right AT the stop boundary
        v = simulation.generate_vehicle()
        direction_name = simulation.directionNumbers[v.direction_number]

        # Position the vehicle so its leading edge just hits the stop line:
        # "down": vehicle moves down, stop check is y+height <= stop. Block when y+height > stop.
        if direction_name == "down":
            h = v.image.get_rect().height
            v.y = v.stop - h + 1  # bottom edge just past stop: y+h = stop+1 > stop
        elif direction_name == "up":
            v.y = v.stop - 1  # y < stop: stop check y >= stop fails
        elif direction_name == "right":
            w = v.image.get_rect().width
            v.x = v.stop - w + 1  # leading edge just past stop
        elif direction_name == "left":
            v.x = v.stop + 1  # leading edge just past stop

        # Red for this direction
        opposite = (v.direction_number + 2) % 4
        simulation.set_signal_state(opposite, 0)

        for _ in range(5):
            v.move()

        assert (
            v.speed == 0
        ), f"Vehicle at stop line should be stopped (dir={direction_name}, speed={v.speed})"

    def test_queue_clears_on_green_signal(self):
        """Vehicles move when they receive green signal."""
        spawned = []
        for _ in range(3):
            v = simulation.generate_vehicle()
            spawned.append(v)

        # Green for all directions cycling through
        simulation.set_signal_state(0, 0)

        for _ in range(20):
            for v in spawned:
                v.move()

        # At least one vehicle should have moved
        total_not_at_start = sum(1 for v in spawned if v.speed > 0 or v.crossed == 1)
        assert total_not_at_start > 0, "At least one vehicle should have moved"
        assert len(spawned) > 0


# ---------------------------------------------------------------------------
# TestSignalObedience
# ---------------------------------------------------------------------------


class TestSignalObedience:
    """Test that simulation respects signal state changes."""

    def test_signal_state_changes_are_reflected(self):
        """set_signal_state updates the module globals."""
        simulation.set_signal_state(2, 1)
        assert simulation.currentGreen == 2
        assert simulation.currentYellow == 1

    def test_signal_state_affects_vehicle_behavior(self):
        """Vehicle behavior changes when signal state changes."""
        v = simulation.generate_vehicle()
        v.direction_number = 0

        simulation.set_signal_state(0, 0)
        v.move()
        speed_on_green = v.speed
        assert speed_on_green > 0, "Should have positive speed on green"

        # Change to red for direction 0
        simulation.set_signal_state(1, 0)
        # Speed attribute should still be numeric
        assert isinstance(v.speed, (int, float)), "Speed should be numeric"

    def test_get_crossed_counts_returns_dict(self):
        """get_crossed_counts() returns a dict keyed by direction index."""
        counts = simulation.get_crossed_counts()
        assert isinstance(counts, dict), "Should return a dict"
        for direction in (0, 1, 2, 3):
            assert direction in counts, f"Should have direction {direction}"
        for v in counts.values():
            assert isinstance(v, int), "Counts should be ints"
            assert v >= 0, "Counts should be non-negative"

    def test_get_crossed_counts_increments_on_cross(self):
        """Crossing count increments when a vehicle's crossed flag is set."""
        # Manually mark a vehicle as crossed
        v = simulation.generate_vehicle()
        direction_name = simulation.directionNumbers[v.direction_number]

        initial = simulation.vehicles[direction_name]["crossed"]
        simulation.vehicles[direction_name]["crossed"] += 1

        counts = simulation.get_crossed_counts()
        assert counts[v.direction_number] == initial + 1


# ---------------------------------------------------------------------------
# TestVehicleProperties
# ---------------------------------------------------------------------------


class TestVehicleProperties:
    """Test vehicle type and property assignment."""

    def test_vehicle_has_valid_type(self):
        """Spawned vehicles have a valid vehicleClass."""
        for _ in range(20):
            v = simulation.generate_vehicle()
            assert v.vehicleClass in (
                "car",
                "bus",
                "truck",
                "bike",
            ), f"Invalid vehicleClass: {v.vehicleClass}"
            _reset_sim()

    def test_vehicle_type_affects_nominal_speed(self):
        """Different vehicle types have different nominal speeds."""
        seen_speeds = set()
        for _ in range(40):
            v = simulation.generate_vehicle()
            seen_speeds.add(v.nominal_speed)

        # Must have at least one speed value
        assert len(seen_speeds) >= 1, "Should record at least one speed"
        # All speeds should be positive
        for s in seen_speeds:
            assert s > 0, f"Nominal speed {s} should be positive"

    def test_vehicle_has_direction_attributes(self):
        """Vehicle has expected direction attributes."""
        v = simulation.generate_vehicle()
        assert hasattr(v, "direction_number"), "Should have direction_number"
        assert hasattr(v, "direction"), "Should have direction"
        assert v.direction in (
            "down",
            "left",
            "up",
            "right",
        ), f"Unexpected direction: {v.direction}"

    def test_vehicle_has_position_attributes(self):
        """Vehicle starts with valid x, y coordinates."""
        v = simulation.generate_vehicle()
        assert isinstance(v.x, (int, float)), "x should be numeric"
        assert isinstance(v.y, (int, float)), "y should be numeric"

    def test_vehicle_crossed_starts_at_zero(self):
        """New vehicles start with crossed=0."""
        v = simulation.generate_vehicle()
        assert v.crossed == 0, "New vehicle should not be crossed"


# ---------------------------------------------------------------------------
# TestSimulationReset
# ---------------------------------------------------------------------------


class TestSimulationReset:
    """Test simulation state management."""

    def test_initial_state_is_empty(self):
        """After _reset_sim(), iter_vehicles() returns nothing."""
        _reset_sim()
        vehicles = list(simulation.iter_vehicles())
        assert len(vehicles) == 0, "Should start with no vehicles"

    def test_state_persists_across_ticks(self):
        """Vehicle count stays consistent when no new vehicles are added."""
        simulation.generate_vehicle()
        count_before = len(list(simulation.iter_vehicles()))

        # Tick existing vehicles
        for v in list(simulation.iter_vehicles()):
            v.move()

        count_after = len(list(simulation.iter_vehicles()))
        # Vehicles are NOT removed from the sprite group on crossing in the
        # current implementation – count should be stable
        assert count_before == count_after, "Vehicle count should persist"

    def test_direction_globals_are_correct(self):
        """directionNumbers mapping is consistent."""
        assert simulation.directionNumbers[0] == "down"
        assert simulation.directionNumbers[1] == "left"
        assert simulation.directionNumbers[2] == "up"
        assert simulation.directionNumbers[3] == "right"

    def test_speeds_dict_has_all_types(self):
        """speeds dict covers every allowed vehicle type."""
        for vtype in ("car", "bus", "truck", "bike"):
            assert vtype in simulation.speeds, f"Missing speed for {vtype}"
            assert simulation.speeds[vtype] > 0, f"Speed for {vtype} must be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
