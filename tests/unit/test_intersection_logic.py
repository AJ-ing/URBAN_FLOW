"""
Unit tests for Task 3.3 — Intersection Logic Skeleton.

Covers:
  • Intersection (signal phase state machine)
  • ConflictMatrix (conflicting movement pairs)
  • QueueManager (per-lane queue tracking)
"""

import pytest

from src.simulation.intersection import Intersection, Phase
from src.simulation.conflict_matrix import ConflictMatrix, MOVEMENTS
from src.simulation.queue_manager import QueueManager


# =====================================================================
# Intersection tests
# =====================================================================

class TestIntersection:
    """Tests for the Intersection signal phase state machine."""

    def test_initial_phase_is_all_red(self):
        ix = Intersection("int_1")
        assert ix.get_current_phase() == Phase.ALL_RED

    def test_custom_initial_phase(self):
        ix = Intersection("int_2", initial_phase=Phase.NORTH_SOUTH_GREEN)
        assert ix.get_current_phase() == Phase.NORTH_SOUTH_GREEN

    def test_change_phase_default_cycle(self):
        """ALL_RED → EW_GREEN → EW_YELLOW → ALL_RED (default transitions)."""
        ix = Intersection("int_3")
        assert ix.change_phase() == Phase.EAST_WEST_GREEN
        assert ix.change_phase() == Phase.EAST_WEST_YELLOW
        assert ix.change_phase() == Phase.ALL_RED

    def test_change_phase_explicit_valid(self):
        ix = Intersection("int_4")
        # ALL_RED can explicitly go to NS_GREEN
        ix.change_phase(Phase.NORTH_SOUTH_GREEN)
        assert ix.get_current_phase() == Phase.NORTH_SOUTH_GREEN

    def test_change_phase_invalid_raises(self):
        ix = Intersection("int_5")
        with pytest.raises(ValueError):
            ix.change_phase(Phase.EAST_WEST_YELLOW)  # can't jump straight here

    def test_full_ns_cycle(self):
        """ALL_RED → NS_GREEN → NS_YELLOW → ALL_RED."""
        ix = Intersection("int_6")
        ix.change_phase(Phase.NORTH_SOUTH_GREEN)
        assert ix.change_phase() == Phase.NORTH_SOUTH_YELLOW
        assert ix.change_phase() == Phase.ALL_RED

    def test_is_conflicting_delegates_to_matrix(self):
        ix = Intersection("int_7")
        assert ix.is_conflicting("NB_THROUGH", "EB_THROUGH") is True
        assert ix.is_conflicting("NB_THROUGH", "SB_THROUGH") is False

    def test_repr(self):
        ix = Intersection("int_8")
        assert "int_8" in repr(ix)


# =====================================================================
# ConflictMatrix tests
# =====================================================================

class TestConflictMatrix:
    """Tests for the ConflictMatrix."""

    def test_default_conflicts_exist(self):
        cm = ConflictMatrix()
        assert cm.are_conflicting("NB_THROUGH", "EB_THROUGH")
        assert cm.are_conflicting("SB_THROUGH", "WB_THROUGH")

    def test_symmetry(self):
        cm = ConflictMatrix()
        assert cm.are_conflicting("NB_THROUGH", "EB_THROUGH") == \
               cm.are_conflicting("EB_THROUGH", "NB_THROUGH")

    def test_non_conflicting_pair(self):
        cm = ConflictMatrix()
        # Same-direction movements do not conflict
        assert cm.are_conflicting("NB_THROUGH", "SB_THROUGH") is False

    def test_add_conflict(self):
        cm = ConflictMatrix()
        cm.add_conflict("NB_THROUGH", "SB_THROUGH")
        assert cm.are_conflicting("NB_THROUGH", "SB_THROUGH") is True

    def test_remove_conflict(self):
        cm = ConflictMatrix()
        cm.remove_conflict("NB_THROUGH", "EB_THROUGH")
        assert cm.are_conflicting("NB_THROUGH", "EB_THROUGH") is False

    def test_remove_nonexistent_no_error(self):
        cm = ConflictMatrix()
        cm.remove_conflict("FAKE_A", "FAKE_B")  # should not raise

    def test_get_all_conflicts_returns_sorted(self):
        cm = ConflictMatrix(conflicts=set())
        cm.add_conflict("B_MOV", "A_MOV")
        result = cm.get_all_conflicts()
        assert result == [("A_MOV", "B_MOV")]

    def test_custom_conflicts(self):
        custom = {frozenset({"X", "Y"})}
        cm = ConflictMatrix(conflicts=custom)
        assert cm.are_conflicting("X", "Y") is True
        assert cm.are_conflicting("NB_THROUGH", "EB_THROUGH") is False

    def test_repr(self):
        cm = ConflictMatrix()
        assert "num_conflicts=" in repr(cm)


# =====================================================================
# QueueManager tests
# =====================================================================

class TestQueueManager:
    """Tests for the QueueManager per-lane queue tracking."""

    def test_enqueue_and_dequeue(self):
        qm = QueueManager()
        qm.enqueue("NB_lane_1", "car_A")
        qm.enqueue("NB_lane_1", "car_B")
        assert qm.dequeue("NB_lane_1") == "car_A"
        assert qm.dequeue("NB_lane_1") == "car_B"

    def test_dequeue_empty_raises(self):
        qm = QueueManager()
        with pytest.raises(IndexError):
            qm.dequeue("empty_lane")

    def test_peek_returns_front(self):
        qm = QueueManager()
        qm.enqueue("lane_1", "v1")
        qm.enqueue("lane_1", "v2")
        assert qm.peek("lane_1") == "v1"
        # peek should not remove the item
        assert qm.get_queue_length("lane_1") == 2

    def test_peek_empty_returns_none(self):
        qm = QueueManager()
        assert qm.peek("no_lane") is None

    def test_get_queue_length(self):
        qm = QueueManager()
        assert qm.get_queue_length("lane_x") == 0
        qm.enqueue("lane_x", "v1")
        assert qm.get_queue_length("lane_x") == 1

    def test_get_all_queue_lengths(self):
        qm = QueueManager()
        qm.enqueue("A", 1)
        qm.enqueue("A", 2)
        qm.enqueue("B", 3)
        lengths = qm.get_all_queue_lengths()
        assert lengths == {"A": 2, "B": 1}

    def test_clear_lane(self):
        qm = QueueManager()
        qm.enqueue("lane_1", "v1")
        qm.clear_lane("lane_1")
        assert qm.get_queue_length("lane_1") == 0

    def test_clear_all(self):
        qm = QueueManager()
        qm.enqueue("A", 1)
        qm.enqueue("B", 2)
        qm.clear_all()
        assert qm.get_all_queue_lengths() == {}

    def test_get_lanes(self):
        qm = QueueManager()
        qm.enqueue("B_lane", 1)
        qm.enqueue("A_lane", 2)
        assert qm.get_lanes() == ["A_lane", "B_lane"]

    def test_repr(self):
        qm = QueueManager()
        qm.enqueue("L1", "v")
        assert "total_vehicles=1" in repr(qm)
