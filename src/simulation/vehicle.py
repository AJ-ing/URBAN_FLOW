"""Vehicle module for the URBAN_FLOW traffic simulation.

This module defines the ``Vehicle`` class, which represents an individual
vehicle travelling through the simulated road network.  Each vehicle
tracks its own kinematic state (position, speed, lane) and exposes
methods that the simulation engine calls on every tick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class Vehicle:
    """Represents a single vehicle in the traffic simulation.

    A ``Vehicle`` encapsulates all per-vehicle state required by the
    simulation engine, including spatial coordinates, current lane,
    speed, and the intended destination.  The simulation advances each
    vehicle by calling :meth:`update_position` once per time-step.

    Attributes:
        id: A unique identifier for this vehicle (e.g. an integer or UUID
            string).
        position: The current ``(x, y)`` coordinates of the vehicle on
            the road network, expressed in the network's coordinate
            system.
        lane: Zero-based index of the lane the vehicle currently
            occupies.
        speed: The vehicle's current forward speed in metres per second.
        destination: An ``(x, y)`` coordinate pair representing the
            vehicle's target location.  May be ``None`` when the
            destination is not yet assigned.

    Example::

        >>> v = Vehicle(
        ...     id=1,
        ...     position=(0.0, 0.0),
        ...     lane=0,
        ...     speed=13.9,
        ...     destination=(100.0, 200.0),
        ... )
        >>> v.update_position(dt=1.0)
        >>> v.get_state()["speed"]
        13.9
    """

    id: Any
    position: Tuple[float, float] = (0.0, 0.0)
    lane: int = 0
    speed: float = 0.0
    destination: Optional[Tuple[float, float]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_position(self, dt: float = 1.0) -> None:
        """Advance the vehicle's position based on its current speed.

        The vehicle moves along the *x*-axis by ``speed * dt`` each
        time-step.  Subclasses or the simulation controller can override
        or extend this method to account for acceleration, curvature,
        or interactions with other vehicles.

        Args:
            dt: Duration of the time-step in seconds.  Defaults to
                ``1.0``.

        Raises:
            ValueError: If *dt* is negative.
        """
        if dt < 0:
            raise ValueError(f"Time-step dt must be non-negative, got {dt}")
        x, y = self.position
        self.position = (x + self.speed * dt, y)

    def change_lane(self, target_lane: int) -> bool:
        """Attempt to move the vehicle to *target_lane*.

        In this base implementation the lane change always succeeds.
        Override this method to add collision-avoidance or gap-acceptance
        logic.

        Args:
            target_lane: Zero-based index of the desired lane.

        Returns:
            ``True`` if the lane change was successful, ``False``
            otherwise.

        Raises:
            ValueError: If *target_lane* is negative.
        """
        if target_lane < 0:
            raise ValueError(
                f"target_lane must be non-negative, got {target_lane}"
            )
        self.lane = target_lane
        return True

    def get_state(self) -> Dict[str, Any]:
        """Return a snapshot of the vehicle's current state.

        The returned dictionary is a *plain-data* representation
        suitable for logging, serialisation, or passing to analytics
        modules.

        Returns:
            A dictionary with keys ``"id"``, ``"position"``, ``"lane"``,
            ``"speed"``, and ``"destination"``.
        """
        return {
            "id": self.id,
            "position": self.position,
            "lane": self.lane,
            "speed": self.speed,
            "destination": self.destination,
        }
