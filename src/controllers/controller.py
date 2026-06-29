"""
Adaptive and fixed-time traffic signal controllers.

Direction mapping:
    0 = North, 1 = East, 2 = South, 3 = West
"""

from __future__ import annotations

from typing import Dict, List, Optional

DIRECTIONS = (0, 1, 2, 3)


def _normalize_queues(queues: Dict[int, int] | None) -> Dict[int, int]:
    source = queues or {}
    return {
        direction: max(0, int(source.get(direction, 0))) for direction in DIRECTIONS
    }


class AdaptiveRule:
    """Abstract base for all adaptive signal rules."""

    name: str = "base"
    priority: int = 0

    def should_fire(
        self,
        queues: Dict[int, int],
        current_green: int,
        service_time: Dict[int, float],
        red_timers: Dict[int, float],
    ) -> bool:
        raise NotImplementedError

    def get_decision(
        self,
        queues: Dict[int, int],
        current_green: int,
        service_time: Dict[int, float],
        red_timers: Dict[int, float],
    ) -> int:
        raise NotImplementedError


class WaitTimeThreshold(AdaptiveRule):
    name = "WaitTimeThreshold"
    priority = 100

    def __init__(self, params: dict):
        self.max_wait_s = float(params.get("max_wait_s", 45.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        return any(
            wait_time > self.max_wait_s
            for direction, wait_time in red_timers.items()
            if direction != current_green
        )

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        candidates = {
            direction: wait_time
            for direction, wait_time in red_timers.items()
            if direction != current_green
        }
        return max(
            candidates,
            key=lambda direction: (
                candidates[direction],
                queues.get(direction, 0),
                -direction,
            ),
        )


class QueueLengthExtension(AdaptiveRule):
    name = "QueueLengthExtension"
    priority = 90

    def __init__(self, params: dict):
        self.queue_threshold = int(params.get("queue_threshold", 5))
        self.extension_s = float(params.get("extension_s", 8.0))
        self.max_extensions = int(params.get("max_extensions", 1))
        self._extensions_used = {direction: 0 for direction in DIRECTIONS}

    def reset_extensions(self, direction: int) -> None:
        self._extensions_used[direction] = 0

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        used = self._extensions_used.get(current_green, 0)
        return (
            queues.get(current_green, 0) >= self.queue_threshold
            and used < self.max_extensions
        )

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        self._extensions_used[current_green] = (
            self._extensions_used.get(current_green, 0) + 1
        )
        return current_green


class EarlyTermination(AdaptiveRule):
    name = "EarlyTermination"
    priority = 80

    def __init__(self, params: dict):
        self.min_green_s = float(params.get("min_green_s", 8.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        elapsed = service_time.get(current_green, 0.0)
        return queues.get(current_green, 0) == 0 and elapsed >= self.min_green_s

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        candidates = {
            direction: queue
            for direction, queue in queues.items()
            if direction != current_green
        }
        if not candidates or max(candidates.values()) == 0:
            return (current_green + 1) % 4
        return max(
            candidates,
            key=lambda direction: (
                candidates[direction],
                red_timers.get(direction, 0.0),
                -direction,
            ),
        )


class DemandResponsiveSelection(AdaptiveRule):
    name = "DemandResponsiveSelection"
    priority = 70

    def __init__(self, params: dict):
        self.min_green_s = float(params.get("min_green_s", 8.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        elapsed = service_time.get(current_green, 0.0)
        others_have_queue = any(
            queue > 0
            for direction, queue in queues.items()
            if direction != current_green
        )
        return (
            queues.get(current_green, 0) == 0
            and elapsed >= self.min_green_s
            and others_have_queue
        )

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        candidates = {
            direction: queue
            for direction, queue in queues.items()
            if direction != current_green
        }
        return max(
            candidates,
            key=lambda direction: (
                candidates[direction],
                red_timers.get(direction, 0.0),
                -direction,
            ),
        )


class PeakHourBoost(AdaptiveRule):
    name = "PeakHourBoost"
    priority = 60

    def __init__(self, params: dict):
        self.peak_start_s = float(params.get("peak_start_s", 0.0))
        self.peak_end_s = float(params.get("peak_end_s", 120.0))
        self.boost_factor = float(params.get("boost_factor", 1.3))
        self.min_queue = int(params.get("peak_min_queue", 3))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        return False

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        return current_green

    def get_boost(
        self, sim_time: float, current_green: int, queues: Dict[int, int]
    ) -> float:
        in_peak = self.peak_start_s <= sim_time <= self.peak_end_s
        has_queue = queues.get(current_green, 0) >= self.min_queue
        return self.boost_factor if in_peak and has_queue else 1.0


class BalancedServiceGuarantee(AdaptiveRule):
    name = "BalancedServiceGuarantee"
    priority = 50

    def __init__(self, params: dict):
        self.imbalance_ratio = float(params.get("imbalance_ratio", 2.0))
        self.min_service_s = float(params.get("min_service_s", 12.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        current_service = service_time.get(current_green, 0.0)
        if current_service < self.min_service_s:
            return False

        others = [
            service
            for direction, service in service_time.items()
            if direction != current_green
        ]
        if not others:
            return False

        min_other = min(others)
        return current_service > self.imbalance_ratio * (min_other + 1.0)

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        candidates = {
            direction: service
            for direction, service in service_time.items()
            if direction != current_green
        }
        return min(
            candidates,
            key=lambda direction: (
                candidates[direction],
                -queues.get(direction, 0),
                direction,
            ),
        )


class RuleEngine:
    """Evaluates rules in descending priority order. First match wins."""

    def __init__(self, rules: List[AdaptiveRule]):
        self.rules = sorted(rules, key=lambda rule: rule.priority, reverse=True)
        self.last_rule: Optional[AdaptiveRule] = None

    def evaluate(
        self,
        queues: Dict[int, int],
        current_green: int,
        service_time: Dict[int, float],
        red_timers: Dict[int, float],
    ) -> int:
        self.last_rule = None
        for rule in self.rules:
            if rule.should_fire(queues, current_green, service_time, red_timers):
                self.last_rule = rule
                return rule.get_decision(
                    queues, current_green, service_time, red_timers
                )
        return current_green


class FixedTimeController:
    """Configurable pre-timed signal controller."""

    PLAN_A = {"green_s": 10, "yellow_s": 3}
    PLAN_B = {"green_s": 25, "yellow_s": 3}
    PLAN_C = {"green_s": 39, "yellow_s": 3}

    def __init__(self, green_s: int = 10, yellow_s: int = 3):
        self.green_s = float(green_s)
        self.yellow_s = float(yellow_s)
        self.cycle = [0, 1, 2, 3]
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False

    def tick(self, dt: float) -> None:
        if dt <= 0:
            return

        self.elapsed += dt
        if not self.in_yellow and self.elapsed >= self.green_s:
            self.in_yellow = True
            self.elapsed -= self.green_s
        elif self.in_yellow and self.elapsed >= self.yellow_s:
            self.in_yellow = False
            self.elapsed -= self.yellow_s
            self.current_idx = (self.current_idx + 1) % len(self.cycle)

    def get_signal(self, queues: Dict[int, int]) -> int:
        if self.in_yellow:
            return self.cycle[(self.current_idx + 1) % len(self.cycle)]
        return self.cycle[self.current_idx]

    def get_phase_direction(self) -> int:
        return self.cycle[self.current_idx]

    def get_pending_direction(self) -> int:
        return self.cycle[(self.current_idx + 1) % len(self.cycle)]

    def get_green_remaining(self) -> float:
        if self.in_yellow:
            return 0.0
        return max(0.0, self.green_s - self.elapsed)

    def get_yellow_remaining(self) -> float:
        if not self.in_yellow:
            return 0.0
        return max(0.0, self.yellow_s - self.elapsed)

    def time_until_green(self, direction: int) -> float:
        if direction == self.get_phase_direction() and not self.in_yellow:
            return 0.0

        remaining = (
            self.get_yellow_remaining()
            if self.in_yellow
            else self.get_green_remaining()
        )
        probe_idx = (self.current_idx + 1) % len(self.cycle)
        while self.cycle[probe_idx] != direction:
            remaining += self.green_s + self.yellow_s
            probe_idx = (probe_idx + 1) % len(self.cycle)
        return remaining

    def is_in_yellow(self) -> bool:
        return self.in_yellow

    def reset(self) -> None:
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False


class AdaptiveController:
    """Queue-aware adaptive signal controller with safety constraints."""

    MIN_GREEN_S = 8.0
    MAX_GREEN_S = 90.0
    YELLOW_S = 3.0

    def __init__(self, params: dict):
        self.min_green_s = max(
            self.MIN_GREEN_S, float(params.get("min_green_s", self.MIN_GREEN_S))
        )
        self.max_green_s = self.MAX_GREEN_S

        self.queue_ext = QueueLengthExtension(params)
        self.peak_rule = PeakHourBoost(params)

        rules: List[AdaptiveRule] = [
            WaitTimeThreshold(params),
            self.queue_ext,
            EarlyTermination(params),
            DemandResponsiveSelection(params),
            self.peak_rule,
            BalancedServiceGuarantee(params),
        ]
        self.engine = RuleEngine(rules)

        self.current_green = 0
        self.in_yellow = False
        self.yellow_timer = 0.0
        self.pending_green: Optional[int] = None
        self.phase_elapsed = 0.0
        self.phase_limit = self.min_green_s

        self.service_time = {direction: 0.0 for direction in DIRECTIONS}
        self.red_timers = {direction: 0.0 for direction in DIRECTIONS}
        self.sim_time = 0.0
        self._last_queues = _normalize_queues({})
        self.queue_ext.reset_extensions(self.current_green)

    def tick(self, dt: float) -> None:
        if dt <= 0:
            return

        self.sim_time += dt

        if self.in_yellow:
            self.yellow_timer += dt
            if self.yellow_timer >= self.YELLOW_S:
                self._finish_transition()
            return

        boost = self.peak_rule.get_boost(
            self.sim_time, self.current_green, self._last_queues
        )
        self.phase_elapsed += dt
        self.service_time[self.current_green] += dt * boost

        for direction in DIRECTIONS:
            if direction == self.current_green:
                self.red_timers[direction] = 0.0
            else:
                self.red_timers[direction] += dt

    def get_signal(self, queues: Dict[int, int]) -> int:
        self._last_queues = _normalize_queues(queues)

        if self.in_yellow:
            return self.current_green

        if self.phase_elapsed >= self.max_green_s:
            self._start_transition(self._default_next_direction())
            return self.current_green

        if self.phase_elapsed < self.min_green_s:
            return self.current_green

        decision = self.engine.evaluate(
            self._last_queues,
            self.current_green,
            self.service_time,
            self.red_timers,
        )

        if isinstance(self.engine.last_rule, QueueLengthExtension):
            self.phase_limit = min(
                self.max_green_s, self.phase_limit + self.queue_ext.extension_s
            )
            return self.current_green

        if decision != self.current_green:
            self._start_transition(decision)
            return self.current_green

        if self.phase_elapsed >= self.phase_limit and self._should_rotate_after_hold():
            self._start_transition(self._highest_demand_direction())

        return self.current_green

    def _should_rotate_after_hold(self) -> bool:
        other_queues = [
            queue
            for direction, queue in self._last_queues.items()
            if direction != self.current_green
        ]
        return any(
            queue > self._last_queues.get(self.current_green, 0)
            for queue in other_queues
        )

    def _highest_demand_direction(self) -> int:
        candidates = {
            direction: queue
            for direction, queue in self._last_queues.items()
            if direction != self.current_green
        }
        if not candidates:
            return self._default_next_direction()
        best_queue = max(candidates.values())
        if best_queue == 0:
            return self._default_next_direction()
        return max(
            candidates,
            key=lambda direction: (
                candidates[direction],
                self.red_timers.get(direction, 0.0),
                -direction,
            ),
        )

    def _default_next_direction(self) -> int:
        return (self.current_green + 1) % 4

    def _start_transition(self, next_direction: int) -> None:
        if next_direction == self.current_green:
            return

        self.in_yellow = True
        self.yellow_timer = 0.0
        self.pending_green = next_direction

    def _finish_transition(self) -> None:
        next_direction = (
            self.pending_green
            if self.pending_green is not None
            else self._default_next_direction()
        )
        self.in_yellow = False
        self.yellow_timer = 0.0
        self.current_green = next_direction
        self.pending_green = None
        self.phase_elapsed = 0.0
        self.phase_limit = self.min_green_s
        self.service_time[self.current_green] = 0.0
        self.red_timers[self.current_green] = 0.0
        self.queue_ext.reset_extensions(self.current_green)

    def get_phase_direction(self) -> int:
        return self.current_green

    def get_pending_direction(self) -> int:
        if self.pending_green is not None:
            return self.pending_green
        return self._default_next_direction()

    def get_green_remaining(self) -> float:
        remaining_to_limit = max(0.0, self.phase_limit - self.phase_elapsed)
        remaining_to_max = max(0.0, self.max_green_s - self.phase_elapsed)
        return min(remaining_to_limit, remaining_to_max)

    def get_yellow_remaining(self) -> float:
        if not self.in_yellow:
            return 0.0
        return max(0.0, self.YELLOW_S - self.yellow_timer)

    def is_in_yellow(self) -> bool:
        return self.in_yellow

    def reset(self) -> None:
        self.current_green = 0
        self.in_yellow = False
        self.yellow_timer = 0.0
        self.pending_green = None
        self.phase_elapsed = 0.0
        self.phase_limit = self.min_green_s
        self.service_time = {direction: 0.0 for direction in DIRECTIONS}
        self.red_timers = {direction: 0.0 for direction in DIRECTIONS}
        self.sim_time = 0.0
        self._last_queues = _normalize_queues({})
        for direction in DIRECTIONS:
            self.queue_ext.reset_extensions(direction)
