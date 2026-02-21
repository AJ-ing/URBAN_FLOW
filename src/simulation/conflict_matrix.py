"""
Conflict matrix module — defines which traffic movements conflict with each other.

A *movement* represents a directional flow of traffic, e.g. northbound through
(``NB_THROUGH``), eastbound left-turn (``EB_LEFT``), etc.  Two movements
conflict when they cannot safely proceed at the same time.
"""

from typing import FrozenSet, Set, Tuple, cast


# ── Standard movement identifiers ─────────────────────────────────────
MOVEMENTS = [
    "NB_THROUGH",  # Northbound through
    "NB_LEFT",     # Northbound left-turn
    "SB_THROUGH",  # Southbound through
    "SB_LEFT",     # Southbound left-turn
    "EB_THROUGH",  # Eastbound through
    "EB_LEFT",     # Eastbound left-turn
    "WB_THROUGH",  # Westbound through
    "WB_LEFT",     # Westbound left-turn
]

# ── Default conflicting movement pairs ────────────────────────────────
# Each tuple (A, B) means movement A and movement B cannot run at the
# same time.  The matrix is symmetric — if (A, B) conflicts, so does
# (B, A).
_DEFAULT_CONFLICTS: Set[FrozenSet[str]] = {
    # North-South vs East-West through movements
    frozenset({"NB_THROUGH", "EB_THROUGH"}),
    frozenset({"NB_THROUGH", "WB_THROUGH"}),
    frozenset({"SB_THROUGH", "EB_THROUGH"}),
    frozenset({"SB_THROUGH", "WB_THROUGH"}),

    # North-South vs East-West left-turn movements
    frozenset({"NB_LEFT", "EB_LEFT"}),
    frozenset({"NB_LEFT", "WB_LEFT"}),
    frozenset({"SB_LEFT", "EB_LEFT"}),
    frozenset({"SB_LEFT", "WB_LEFT"}),

    # Through vs opposing left-turn (same axis)
    frozenset({"NB_THROUGH", "SB_LEFT"}),
    frozenset({"SB_THROUGH", "NB_LEFT"}),
    frozenset({"EB_THROUGH", "WB_LEFT"}),
    frozenset({"WB_THROUGH", "EB_LEFT"}),

    # Left-turn vs crossing through
    frozenset({"NB_LEFT", "EB_THROUGH"}),
    frozenset({"NB_LEFT", "WB_THROUGH"}),
    frozenset({"SB_LEFT", "EB_THROUGH"}),
    frozenset({"SB_LEFT", "WB_THROUGH"}),
    frozenset({"EB_LEFT", "NB_THROUGH"}),
    frozenset({"EB_LEFT", "SB_THROUGH"}),
    frozenset({"WB_LEFT", "NB_THROUGH"}),
    frozenset({"WB_LEFT", "SB_THROUGH"}),
}


class ConflictMatrix:
    """
    Stores and queries conflicting movement pairs for an intersection.

    By default, the standard four-way intersection conflict set is used.
    Custom conflicts can be added via :meth:`add_conflict` or supplied at
    construction time.
    """

    def __init__(
        self,
        conflicts: Set[FrozenSet[str]] | None = None,
    ) -> None:
        self._conflicts: Set[FrozenSet[str]] = (
            set(conflicts) if conflicts is not None else set(_DEFAULT_CONFLICTS)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def are_conflicting(self, movement_a: str, movement_b: str) -> bool:
        """Return ``True`` if *movement_a* and *movement_b* conflict."""
        return frozenset({movement_a, movement_b}) in self._conflicts

    def add_conflict(self, movement_a: str, movement_b: str) -> None:
        """Register an additional conflicting pair."""
        self._conflicts.add(frozenset({movement_a, movement_b}))

    def remove_conflict(self, movement_a: str, movement_b: str) -> None:
        """Remove a conflict pair.  No-op if the pair is not present."""
        self._conflicts.discard(frozenset({movement_a, movement_b}))

    def get_all_conflicts(self) -> list[tuple[str, str]]:
        """Return all conflicting pairs as a sorted list of 2-tuples."""
        return sorted(
            (cast(Tuple[str, str], tuple(sorted(pair))) for pair in self._conflicts),
            key=lambda p: (p[0], p[1]),
        )

    def __repr__(self) -> str:
        return f"ConflictMatrix(num_conflicts={len(self._conflicts)})"
