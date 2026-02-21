"""
Intersection module — signal phase state machine for traffic intersections.
"""

from enum import Enum
from typing import Optional

from src.simulation.conflict_matrix import ConflictMatrix


class Phase(Enum):
    """Enumeration of signal phases at an intersection."""
    NORTH_SOUTH_GREEN = "NS_GREEN"
    NORTH_SOUTH_YELLOW = "NS_YELLOW"
    EAST_WEST_GREEN = "EW_GREEN"
    EAST_WEST_YELLOW = "EW_YELLOW"
    ALL_RED = "ALL_RED"


# Define valid phase transitions
_PHASE_TRANSITIONS = {
    Phase.NORTH_SOUTH_GREEN: Phase.NORTH_SOUTH_YELLOW,
    Phase.NORTH_SOUTH_YELLOW: Phase.ALL_RED,
    Phase.ALL_RED: Phase.EAST_WEST_GREEN,  # default; can also go to NS_GREEN
    Phase.EAST_WEST_GREEN: Phase.EAST_WEST_YELLOW,
    Phase.EAST_WEST_YELLOW: Phase.ALL_RED,
}


class Intersection:
    """
    Represents a traffic intersection with a signal phase state machine.

    Attributes:
        intersection_id: Unique identifier for this intersection.
        current_phase: The active signal phase.
    """

    def __init__(self, intersection_id: str, initial_phase: Phase = Phase.ALL_RED) -> None:
        self.intersection_id = intersection_id
        self._current_phase = initial_phase
        self._conflict_matrix = ConflictMatrix()
        self._phase_history: list[Phase] = [initial_phase]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_phase(self) -> Phase:
        """Return the current signal phase."""
        return self._current_phase

    def change_phase(self, target_phase: Optional[Phase] = None) -> Phase:
        """
        Advance the signal to the next phase (or to *target_phase* if given).

        Parameters:
            target_phase: An explicit phase to transition to.  When ``None``
                          the next phase in the default cycle is used.

        Returns:
            The new current phase after the transition.

        Raises:
            ValueError: If *target_phase* is not a valid successor of the
                        current phase.
        """
        if target_phase is None:
            # Follow the default cycle
            next_phase = _PHASE_TRANSITIONS.get(self._current_phase)
            if next_phase is None:
                raise ValueError(
                    f"No default transition from {self._current_phase}"
                )
        else:
            # Validate explicit transition
            if not self._is_valid_transition(self._current_phase, target_phase):
                raise ValueError(
                    f"Invalid transition: {self._current_phase} -> {target_phase}"
                )
            next_phase = target_phase

        self._current_phase = next_phase
        self._phase_history.append(next_phase)
        return self._current_phase

    def is_conflicting(self, movement_a: str, movement_b: str) -> bool:
        """
        Check whether two movements conflict with each other.

        Parameters:
            movement_a: Identifier for the first movement (e.g. ``"NB_THROUGH"``).
            movement_b: Identifier for the second movement (e.g. ``"EB_THROUGH"``).

        Returns:
            ``True`` if the movements conflict, ``False`` otherwise.
        """
        return self._conflict_matrix.are_conflicting(movement_a, movement_b)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_transition(current: Phase, target: Phase) -> bool:
        """Return ``True`` if transitioning from *current* to *target* is allowed."""
        # ALL_RED can go to either green phase
        if current == Phase.ALL_RED and target in (
            Phase.NORTH_SOUTH_GREEN,
            Phase.EAST_WEST_GREEN,
        ):
            return True
        return _PHASE_TRANSITIONS.get(current) == target

    def __repr__(self) -> str:
        return (
            f"Intersection(id={self.intersection_id!r}, "
            f"phase={self._current_phase})"
        )
