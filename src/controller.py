"""
Traffic signal controllers for UrbanFlow.

Implements the frozen interface contract from docs/api/interfaces.md:
  - FixedTimeController.tick(dt) + get_signal(queue_lengths: Dict[str,int]) -> str
  - AdaptiveController.tick(dt)  + get_signal(queue_lengths: Dict[str,int]) -> str

Direction mapping (internal int ↔ public str):
    0 = 'N', 1 = 'S', 2 = 'E', 3 = 'W'

Original logic by Dev Mangal (POD 2).
Interface adapter by Aayush Jain (POD 0) — migration from prototype.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ── Direction constants ────────────────────────────────────────────────
# Internal: ints (used by all rule arithmetic)
# External: str keys matching interfaces.md contract
DIRECTIONS = (0, 1, 2, 3)

_INT_TO_STR: Dict[int, str] = {0: "N", 1: "S", 2: "E", 3: "W"}
_STR_TO_INT: Dict[str, int] = {"N": 0, "S": 1, "E": 2, "W": 3}


def _queues_to_int(queues: Dict[str, int]) -> Dict[int, int]:
    """Convert external str-keyed queues to internal int-keyed queues."""
    result = {d: 0 for d in DIRECTIONS}
    for key, val in queues.items():
        if key in _STR_TO_INT:
            result[_STR_TO_INT[key]] = max(0, int(val))
    return result


def _normalize_queues(queues: Dict[int, int] | None) -> Dict[int, int]:
    source = queues or {}
    return {direction: max(0, int(source.get(direction, 0))) for direction in DIRECTIONS}


# ── Adaptive rule base & implementations ──────────────────────────────
# All rule logic is Dev's original prototype code, unchanged.

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
    """Priority 100 — switch to longest-waiting direction when any red > max_wait_s."""
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
            key=lambda direction: (candidates[direction], queues.get(direction, 0), -direction),
        )


class QueueLengthExtension(AdaptiveRule):
    """Priority 90 — extend green when current queue > threshold. Max 1 extension per phase."""
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
        return queues.get(current_green, 0) >= self.queue_threshold and used < self.max_extensions

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        self._extensions_used[current_green] = self._extensions_used.get(current_green, 0) + 1
        return current_green


class EarlyTermination(AdaptiveRule):
    """Priority 80 — switch when current queue = 0 and min_green_s elapsed."""
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
            key=lambda direction: (candidates[direction], red_timers.get(direction, 0.0), -direction),
        )


class DemandResponsiveSelection(AdaptiveRule):
    """Priority 70 — switch to highest-queue direction when current queue = 0."""
    name = "DemandResponsiveSelection"
    priority = 70

    def __init__(self, params: dict):
        self.min_green_s = float(params.get("min_green_s", 8.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        elapsed = service_time.get(current_green, 0.0)
        others_have_queue = any(
            queue > 0 for direction, queue in queues.items() if direction != current_green
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
            key=lambda direction: (candidates[direction], red_timers.get(direction, 0.0), -direction),
        )


class PeakHourBoost(AdaptiveRule):
    """Priority 60 — extend green by boost_factor during peak hours."""
    name = "PeakHourBoost"
    priority = 60

    def __init__(self, params: dict):
        self.peak_start_s = float(params.get("peak_start_s", 0.0))
        self.peak_end_s = float(params.get("peak_end_s", 120.0))
        self.boost_factor = float(params.get("boost_factor", 1.3))
        self.min_queue = int(params.get("peak_min_queue", 3))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        # NOTE: PeakHourBoost acts via get_boost() in AdaptiveController.tick(),
        # not as a phase-switch rule. should_fire stays False intentionally.
        # To activate as a switch rule, implement sim_time injection here.
        return False

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        return current_green

    def get_boost(self, sim_time: float, current_green: int, queues: Dict[int, int]) -> float:
        in_peak = self.peak_start_s <= sim_time <= self.peak_end_s
        has_queue = queues.get(current_green, 0) >= self.min_queue
        return self.boost_factor if in_peak and has_queue else 1.0


class BalancedServiceGuarantee(AdaptiveRule):
    """Priority 50 — switch to under-served direction if imbalance > ratio."""
    name = "BalancedServiceGuarantee"
    priority = 50

    def __init__(self, params: dict):
        self.imbalance_ratio = float(params.get("imbalance_ratio", 2.0))
        self.min_service_s = float(params.get("min_service_s", 12.0))

    def should_fire(self, queues, current_green, service_time, red_timers) -> bool:
        current_service = service_time.get(current_green, 0.0)
        if current_service < self.min_service_s:
            return False
        others = [s for d, s in service_time.items() if d != current_green]
        if not others:
            return False
        return current_service > self.imbalance_ratio * (min(others) + 1.0)

    def get_decision(self, queues, current_green, service_time, red_timers) -> int:
        candidates = {
            direction: service
            for direction, service in service_time.items()
            if direction != current_green
        }
        return min(
            candidates,
            key=lambda direction: (candidates[direction], -queues.get(direction, 0), direction),
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
                return rule.get_decision(queues, current_green, service_time, red_timers)
        return current_green


# ── Controllers ───────────────────────────────────────────────────────

class FixedTimeController:
    """
    Configurable pre-timed signal controller.

    Public interface (interfaces.md):
        tick(dt: float) -> None          # advance internal timer
        get_signal(queue_lengths: Dict[str, int]) -> str  # returns 'N','S','E','W'

    Preset timing plans (class-level constants):
        PLAN_A: green_s=25, yellow_s=3  — light traffic, 112s cycle
        PLAN_B: green_s=39, yellow_s=3  — moderate traffic, 168s cycle (35% benchmark baseline)
        PLAN_C: green_s=54, yellow_s=3  — heavy traffic, 228s cycle
    """

    PLAN_A = {"green_s": 25, "yellow_s": 3}
    PLAN_B = {"green_s": 39, "yellow_s": 3}
    PLAN_C = {"green_s": 54, "yellow_s": 3}

    def __init__(self, green_s: int = 30, yellow_s: int = 3):
        self.green_s = float(green_s)
        self.yellow_s = float(yellow_s)
        self.cycle = [0, 1, 2, 3]   # internal int directions
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False

    def tick(self, dt: float) -> None:
        """Advance internal timer. MUST be called every frame before get_signal()."""
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

    def get_signal(self, queue_lengths: Dict[str, int]) -> str:
        """Return current green direction as 'N', 'S', 'E', or 'W'. queue_lengths unused."""
        if self.in_yellow:
            return _INT_TO_STR[self.cycle[(self.current_idx + 1) % len(self.cycle)]]
        return _INT_TO_STR[self.cycle[self.current_idx]]

    # ── Helpers used by signals.py (preserved for prototype compatibility) ──

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
        remaining = self.get_yellow_remaining() if self.in_yellow else self.get_green_remaining()
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
    """
    Queue-aware adaptive signal controller with 6 heuristic rules.

    Public interface (interfaces.md):
        tick(dt: float) -> None          # advance all internal timers
        get_signal(queue_lengths: Dict[str, int]) -> str  # returns 'N','S','E','W'

    Rules (in priority order):
        100  WaitTimeThreshold      — prevents starvation
         90  QueueLengthExtension   — extends green for long queues
         80  EarlyTermination       — skips green if queue cleared
         70  DemandResponsiveSelection — switches to highest demand
         60  PeakHourBoost          — boosts via tick() service_time
         50  BalancedServiceGuarantee  — prevents chronic imbalance
    """

    MIN_GREEN_S = 8.0
    MAX_GREEN_S = 90.0
    YELLOW_S = 3.0

    def __init__(self, params_path: str):
        import json
        with open(params_path, "r", encoding="utf-8") as f:
            params = json.load(f)

        self.min_green_s = max(self.MIN_GREEN_S, float(params.get("min_green_s", self.MIN_GREEN_S)))
        self.max_green_s = self.MAX_GREEN_S

        rules: List[AdaptiveRule] = [
            WaitTimeThreshold(params),
            QueueLengthExtension(params),
            EarlyTermination(params),
            DemandResponsiveSelection(params),
            PeakHourBoost(params),
            BalancedServiceGuarantee(params),
        ]
        self.engine = RuleEngine(rules)
        self.queue_ext: QueueLengthExtension = rules[1]   # type: ignore[assignment]
        self.peak_rule: PeakHourBoost = rules[4]           # type: ignore[assignment]

        self.current_green = 0          # internal int
        self.in_yellow = False
        self.yellow_timer = 0.0
        self.pending_green: Optional[int] = None
        self.phase_elapsed = 0.0
        self.phase_limit = self.min_green_s

        self.service_time = {d: 0.0 for d in DIRECTIONS}
        self.red_timers = {d: 0.0 for d in DIRECTIONS}
        self.sim_time = 0.0
        self._last_queues = _normalize_queues({})
        self.queue_ext.reset_extensions(self.current_green)

    def tick(self, dt: float) -> None:
        """Advance all internal timers. MUST be called every frame before get_signal()."""
        if dt <= 0:
            return

        self.sim_time += dt

        if self.in_yellow:
            self.yellow_timer += dt
            if self.yellow_timer >= self.YELLOW_S:
                self._finish_transition()
            return

        boost = self.peak_rule.get_boost(self.sim_time, self.current_green, self._last_queues)
        self.phase_elapsed += dt
        self.service_time[self.current_green] += dt * boost

        for direction in DIRECTIONS:
            if direction == self.current_green:
                self.red_timers[direction] = 0.0
            else:
                self.red_timers[direction] += dt

    def get_signal(self, queue_lengths: Dict[str, int]) -> str:
        """Evaluate rules and return current green direction as 'N','S','E','W'."""
        self._last_queues = _queues_to_int(queue_lengths)

        if self.in_yellow:
            return _INT_TO_STR[self.current_green]

        if self.phase_elapsed >= self.max_green_s:
            self._start_transition(self._default_next_direction())
            return _INT_TO_STR[self.current_green]

        if self.phase_elapsed < self.min_green_s:
            return _INT_TO_STR[self.current_green]

        decision = self.engine.evaluate(
            self._last_queues,
            self.current_green,
            self.service_time,
            self.red_timers,
        )

        if isinstance(self.engine.last_rule, QueueLengthExtension):
            self.phase_limit = min(self.max_green_s, self.phase_limit + self.queue_ext.extension_s)
            return _INT_TO_STR[self.current_green]

        if decision != self.current_green:
            self._start_transition(decision)
            return _INT_TO_STR[self.current_green]

        if self.phase_elapsed >= self.phase_limit and self._should_rotate_after_hold():
            self._start_transition(self._highest_demand_direction())

        return _INT_TO_STR[self.current_green]

    # ── Internal state machine (Dev's original logic, unchanged) ──────

    def _should_rotate_after_hold(self) -> bool:
        other_queues = [
            queue for direction, queue in self._last_queues.items()
            if direction != self.current_green
        ]
        return any(queue > self._last_queues.get(self.current_green, 0) for queue in other_queues)

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
            key=lambda direction: (candidates[direction], self.red_timers.get(direction, 0.0), -direction),
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
            self.pending_green if self.pending_green is not None
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

    # ── Helpers used by signals.py (preserved for prototype compatibility) ──

    def get_phase_direction(self) -> int:
        return self.current_green

    def get_pending_direction(self) -> int:
        return self.pending_green if self.pending_green is not None else self._default_next_direction()

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
        self.service_time = {d: 0.0 for d in DIRECTIONS}
        self.red_timers = {d: 0.0 for d in DIRECTIONS}
        self.sim_time = 0.0
        self._last_queues = _normalize_queues({})
        for direction in DIRECTIONS:
            self.queue_ext.reset_extensions(direction)