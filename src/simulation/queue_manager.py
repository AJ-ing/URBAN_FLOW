"""
Queue manager module — per-lane vehicle queue tracking for intersections.
"""

from collections import defaultdict
from typing import Any


class QueueManager:
    """
    Tracks vehicle queues on a per-lane basis at an intersection.

    Each lane is identified by a unique string key (e.g. ``"NB_lane_1"``).
    Vehicles are represented as opaque objects / IDs stored in FIFO order.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[Any]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, lane_id: str, vehicle: Any) -> None:
        """
        Add a *vehicle* to the back of the queue for *lane_id*.

        Parameters:
            lane_id: Identifier for the lane.
            vehicle: Vehicle object or ID to enqueue.
        """
        self._queues[lane_id].append(vehicle)

    def dequeue(self, lane_id: str) -> Any:
        """
        Remove and return the vehicle at the front of *lane_id*'s queue.

        Returns:
            The vehicle that was at the front of the queue.

        Raises:
            IndexError: If the queue for *lane_id* is empty.
        """
        if not self._queues[lane_id]:
            raise IndexError(f"Queue for lane '{lane_id}' is empty")
        return self._queues[lane_id].pop(0)

    def peek(self, lane_id: str) -> Any | None:
        """
        Return the vehicle at the front of *lane_id*'s queue without
        removing it, or ``None`` if the queue is empty.
        """
        queue = self._queues.get(lane_id, [])
        return queue[0] if queue else None

    def get_queue_length(self, lane_id: str) -> int:
        """Return the number of vehicles currently queued in *lane_id*."""
        return len(self._queues.get(lane_id, []))

    def get_all_queue_lengths(self) -> dict[str, int]:
        """Return a mapping of every lane to its current queue length."""
        return {lane: len(q) for lane, q in self._queues.items()}

    def clear_lane(self, lane_id: str) -> None:
        """Remove all vehicles from *lane_id*'s queue."""
        self._queues[lane_id].clear()

    def clear_all(self) -> None:
        """Remove all vehicles from every lane queue."""
        self._queues.clear()

    def get_lanes(self) -> list[str]:
        """Return a sorted list of all lane IDs that have been registered."""
        return sorted(self._queues.keys())

    def __repr__(self) -> str:
        total = sum(len(q) for q in self._queues.values())
        return f"QueueManager(lanes={len(self._queues)}, total_vehicles={total})"
