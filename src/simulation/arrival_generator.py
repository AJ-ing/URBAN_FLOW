"""Arrival-generation module for the URBAN_FLOW traffic simulation.

This module provides the ``ArrivalGenerator`` class, which produces
vehicle-arrival events following a **Poisson process**.  The Poisson
model is a natural fit for traffic arrivals because it assumes
independent, memoryless inter-arrival times — a reasonable first-order
approximation for many real-world traffic streams.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from src.simulation.vehicle import Vehicle


class ArrivalGenerator:
    """Generate vehicle arrivals according to a Poisson distribution.

    The generator is configured with a *rate* parameter ``lambda_rate``
    (expected arrivals per time-step).  On each call to
    :meth:`generate_arrivals` it samples from a Poisson distribution
    and creates the corresponding number of :class:`Vehicle` instances.

    Attributes:
        lambda_rate: Mean number of arrivals per time-step (λ ≥ 0).
        spawn_position: Default ``(x, y)`` position where new vehicles
            appear.
        spawn_lane: Default lane index assigned to newly created
            vehicles.
        default_speed: Initial speed (m/s) assigned to new vehicles.
        seed: Optional RNG seed for reproducibility.

    Example::

        >>> gen = ArrivalGenerator(lambda_rate=2.5, seed=42)
        >>> vehicles = gen.generate_arrivals()
        >>> all(isinstance(v, Vehicle) for v in vehicles)
        True
    """

    def __init__(
        self,
        lambda_rate: float = 1.0,
        spawn_position: Tuple[float, float] = (0.0, 0.0),
        spawn_lane: int = 0,
        default_speed: float = 13.9,
        seed: Optional[int] = None,
    ) -> None:
        """Initialise the arrival generator.

        Args:
            lambda_rate: Expected number of arrivals per time-step
                (Poisson λ).  Must be non-negative.
            spawn_position: ``(x, y)`` coordinate where new vehicles
                will be placed.
            spawn_lane: Lane index assigned to every new vehicle.
            default_speed: Speed (m/s) assigned to every new vehicle.
            seed: Optional integer seed for the internal random-number
                generator, enabling deterministic replays.

        Raises:
            ValueError: If *lambda_rate* is negative.
        """
        if lambda_rate < 0:
            raise ValueError(
                f"lambda_rate must be non-negative, got {lambda_rate}"
            )
        self.lambda_rate: float = lambda_rate
        self.spawn_position: Tuple[float, float] = spawn_position
        self.spawn_lane: int = spawn_lane
        self.default_speed: float = default_speed

        self._rng: random.Random = random.Random(seed)
        self._next_id: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_arrivals(
        self,
        destination: Optional[Tuple[float, float]] = None,
    ) -> List[Vehicle]:
        """Sample the number of arrivals and create new vehicles.

        The count of arrivals is drawn from a Poisson distribution with
        parameter ``self.lambda_rate``.  For each arrival a new
        :class:`Vehicle` is instantiated with a unique *id*.

        Args:
            destination: Optional destination coordinate to assign to
                every vehicle created in this call.

        Returns:
            A list of newly created :class:`Vehicle` instances.  The
            list may be empty when the Poisson sample is zero.
        """
        count = self._poisson_sample(self.lambda_rate)
        vehicles: List[Vehicle] = []
        for _ in range(count):
            vehicle = Vehicle(
                id=self._next_id,
                position=self.spawn_position,
                lane=self.spawn_lane,
                speed=self.default_speed,
                destination=destination,
            )
            vehicles.append(vehicle)
            self._next_id += 1
        return vehicles

    def get_config(self) -> Dict[str, Any]:
        """Return the current configuration of this generator.

        Returns:
            A dictionary with keys ``"lambda_rate"``,
            ``"spawn_position"``, ``"spawn_lane"``, and
            ``"default_speed"``.
        """
        return {
            "lambda_rate": self.lambda_rate,
            "spawn_position": self.spawn_position,
            "spawn_lane": self.spawn_lane,
            "default_speed": self.default_speed,
        }

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset the internal state of the generator.

        This resets the vehicle-ID counter to zero and optionally
        re-seeds the random-number generator.

        Args:
            seed: New seed for the RNG.  If ``None``, the existing
                RNG state is left unchanged.
        """
        self._next_id = 0
        if seed is not None:
            self._rng.seed(seed)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _poisson_sample(self, lam: float) -> int:
        """Return a single sample from Poisson(λ) using inverse-transform.

        This uses Knuth's algorithm, which is efficient for small λ
        values typical of per-time-step arrival rates.

        Args:
            lam: The Poisson rate parameter (λ ≥ 0).

        Returns:
            A non-negative integer sampled from Poisson(λ).
        """
        import math

        L = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= self._rng.random()
            if p < L:
                return k - 1
