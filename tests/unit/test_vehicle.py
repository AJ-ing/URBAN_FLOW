"""Unit tests for :mod:`src.simulation.vehicle`."""

import pytest

from src.simulation.vehicle import Vehicle


# ======================================================================
# Construction / defaults
# ======================================================================

class TestVehicleInit:
    """Tests for Vehicle construction and default attribute values."""

    def test_default_attributes(self):
        """Vehicle created with only an id should have sensible defaults."""
        v = Vehicle(id=1)
        assert v.id == 1
        assert v.position == (0.0, 0.0)
        assert v.lane == 0
        assert v.speed == 0.0
        assert v.destination is None

    def test_custom_attributes(self):
        """All attributes should be settable at construction time."""
        v = Vehicle(
            id="car-42",
            position=(10.0, 20.0),
            lane=2,
            speed=25.0,
            destination=(100.0, 200.0),
        )
        assert v.id == "car-42"
        assert v.position == (10.0, 20.0)
        assert v.lane == 2
        assert v.speed == 25.0
        assert v.destination == (100.0, 200.0)


# ======================================================================
# update_position
# ======================================================================

class TestUpdatePosition:
    """Tests for :meth:`Vehicle.update_position`."""

    def test_moves_along_x_axis(self):
        """Position should advance along x by speed * dt."""
        v = Vehicle(id=1, position=(0.0, 0.0), speed=10.0)
        v.update_position(dt=2.0)
        assert v.position == pytest.approx((20.0, 0.0))

    def test_default_dt_is_one_second(self):
        """Calling without dt should default to 1.0 s."""
        v = Vehicle(id=1, position=(5.0, 3.0), speed=7.0)
        v.update_position()
        assert v.position == pytest.approx((12.0, 3.0))

    def test_zero_speed_stays_put(self):
        """A stationary vehicle should not change position."""
        v = Vehicle(id=1, position=(5.0, 5.0), speed=0.0)
        v.update_position(dt=10.0)
        assert v.position == (5.0, 5.0)

    def test_negative_dt_raises(self):
        """A negative time-step should raise ValueError."""
        v = Vehicle(id=1, speed=10.0)
        with pytest.raises(ValueError, match="non-negative"):
            v.update_position(dt=-1.0)

    def test_multiple_updates_accumulate(self):
        """Successive calls should accumulate displacement."""
        v = Vehicle(id=1, position=(0.0, 0.0), speed=5.0)
        v.update_position(dt=1.0)
        v.update_position(dt=1.0)
        v.update_position(dt=1.0)
        assert v.position == pytest.approx((15.0, 0.0))


# ======================================================================
# change_lane
# ======================================================================

class TestChangeLane:
    """Tests for :meth:`Vehicle.change_lane`."""

    def test_successful_lane_change(self):
        """Lane should update and method should return True."""
        v = Vehicle(id=1, lane=0)
        result = v.change_lane(2)
        assert result is True
        assert v.lane == 2

    def test_change_to_same_lane(self):
        """Changing to the current lane should still succeed."""
        v = Vehicle(id=1, lane=1)
        result = v.change_lane(1)
        assert result is True
        assert v.lane == 1

    def test_negative_lane_raises(self):
        """A negative target lane should raise ValueError."""
        v = Vehicle(id=1, lane=0)
        with pytest.raises(ValueError, match="non-negative"):
            v.change_lane(-1)

    def test_change_lane_to_zero(self):
        """Edge case: changing to lane 0 should succeed."""
        v = Vehicle(id=1, lane=3)
        result = v.change_lane(0)
        assert result is True
        assert v.lane == 0


# ======================================================================
# get_state
# ======================================================================

class TestGetState:
    """Tests for :meth:`Vehicle.get_state`."""

    def test_state_keys(self):
        """Returned dict should contain exactly the expected keys."""
        v = Vehicle(id=1)
        state = v.get_state()
        assert set(state.keys()) == {
            "id", "position", "lane", "speed", "destination",
        }

    def test_state_values_match_attributes(self):
        """State dict values should mirror the vehicle's attributes."""
        v = Vehicle(
            id=99,
            position=(1.0, 2.0),
            lane=3,
            speed=15.5,
            destination=(50.0, 60.0),
        )
        state = v.get_state()
        assert state["id"] == 99
        assert state["position"] == (1.0, 2.0)
        assert state["lane"] == 3
        assert state["speed"] == 15.5
        assert state["destination"] == (50.0, 60.0)

    def test_state_reflects_mutation(self):
        """State should reflect changes made after construction."""
        v = Vehicle(id=1, speed=10.0)
        v.update_position(dt=3.0)
        v.change_lane(2)
        state = v.get_state()
        assert state["position"] == pytest.approx((30.0, 0.0))
        assert state["lane"] == 2
