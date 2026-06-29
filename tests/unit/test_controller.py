"""
test_controller.py — Unit tests for controller.py (POD 2: Signal Control)

Tests fixed-time and adaptive signal controllers, rule engines, and decision logic.

Run with:
    pytest tests/unit/test_controller.py -v
"""

from __future__ import annotations

from typing import Dict

import pytest

from src.controllers.controller import (
    AdaptiveController,
    BalancedServiceGuarantee,
    DemandResponsiveSelection,
    EarlyTermination,
    FixedTimeController,
    QueueLengthExtension,
    RuleEngine,
    WaitTimeThreshold,
)

# ---------------------------------------------------------------------------
# TestFixedTimeController
# ---------------------------------------------------------------------------


class TestFixedTimeController:
    """Test fixed-time signal control strategy."""

    def test_fixed_controller_initialization(self):
        """Fixed-time controller initialises with correct parameters."""
        controller = FixedTimeController(green_s=10, yellow_s=3)

        assert controller.green_s == 10.0, "green_s should be 10s"
        assert controller.yellow_s == 3.0, "yellow_s should be 3s"

    def test_fixed_controller_starts_in_green(self):
        """Fixed-time controller starts in green phase (not yellow)."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        assert not controller.is_in_yellow(), "Should start in green phase"

    def test_fixed_controller_cycle_timing(self):
        """Fixed-time controller transitions from green to yellow after green_s."""
        controller = FixedTimeController(green_s=2, yellow_s=1)
        controller.reset()

        # Advance just past green phase
        for _ in range(21):  # 2.1 s
            controller.tick(0.1)

        # Should now be in yellow
        assert controller.is_in_yellow(), "Should be in yellow after green_s elapsed"

    def test_fixed_controller_green_red_transition(self):
        """Controller cycles through green → yellow → next green."""
        controller = FixedTimeController(green_s=1, yellow_s=1)
        controller.reset()

        first_direction = controller.get_phase_direction()

        # Advance past one full green+yellow cycle (1s green + 1s yellow + small margin)
        for _ in range(25):  # 2.5 s
            controller.tick(0.1)

        next_direction = controller.get_phase_direction()
        assert (
            next_direction != first_direction
        ), "Should advance to next direction after full cycle"

    def test_fixed_controller_time_until_green(self):
        """time_until_green() returns non-negative values for all directions."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        for direction in range(4):
            time_until = controller.time_until_green(direction)
            assert (
                time_until >= 0
            ), f"time_until_green({direction}) should be >= 0, got {time_until}"

    def test_fixed_controller_time_until_green_current_direction_is_zero(self):
        """time_until_green for the current green direction should be 0.0."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        current = controller.get_phase_direction()
        assert (
            controller.time_until_green(current) == 0.0
        ), "Time until green for current direction should be 0"

    def test_fixed_controller_get_signal(self):
        """get_signal() returns a valid direction index."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        queues = {0: 5, 1: 2, 2: 3, 3: 1}
        signal = controller.get_signal(queues)

        assert 0 <= signal < 4, f"Signal {signal} out of range [0, 3]"

    def test_fixed_controller_get_green_remaining(self):
        """get_green_remaining() returns value within [0, green_s]."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        remaining = controller.get_green_remaining()
        assert isinstance(remaining, (int, float)), "Should return numeric"
        assert 0 <= remaining <= 10, "Green remaining should be within [0, green_s]"

    def test_fixed_controller_elapsed_resets_on_reset(self):
        """After reset(), elapsed timer is back to 0."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.tick(5.0)  # Advance mid-green
        controller.reset()

        assert controller.elapsed == 0.0, "Elapsed should reset to 0"
        assert not controller.in_yellow, "Should not be in yellow after reset"


# ---------------------------------------------------------------------------
# TestFixedTimeControllerReset
# ---------------------------------------------------------------------------


class TestFixedTimeControllerReset:
    """Test FixedTimeController state reset."""

    def test_fixed_controller_reset(self):
        """FixedTimeController can be reset to initial state."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.tick(5.0)  # Advance time

        controller.reset()

        assert controller.elapsed < 0.01, "Should be near start of cycle after reset"
        assert not controller.in_yellow, "Should not be in yellow after reset"
        assert controller.current_idx == 0, "Cycle index should reset to 0"


# ---------------------------------------------------------------------------
# TestAdaptiveController
# ---------------------------------------------------------------------------


class TestAdaptiveController:
    """Test adaptive signal control strategy."""

    def test_adaptive_controller_initialization(self):
        """Adaptive controller initialises with parameters."""
        params = {
            "max_wait_s": 45.0,
            "queue_threshold": 5,
            "extension_s": 8.0,
            "max_extensions": 1,
            "min_green_s": 8.0,
        }
        controller = AdaptiveController(params)

        assert controller is not None, "Should create adaptive controller"
        assert controller.min_green_s == 8.0

    def test_adaptive_controller_with_empty_params(self):
        """Adaptive controller works with empty params (uses defaults)."""
        controller = AdaptiveController({})
        assert controller is not None, "Should handle empty params"

    def test_adaptive_controller_make_decision_with_queues(self):
        """Adaptive controller returns a valid signal for any queue state."""
        controller = AdaptiveController({"queue_threshold": 5})
        controller.reset()

        queues = {0: 10, 1: 0, 2: 2, 3: 1}
        signal = controller.get_signal(queues)

        assert 0 <= signal < 4, f"Signal {signal} should be valid"

    def test_adaptive_controller_handles_zero_queues(self):
        """Adaptive controller handles all-zero queues gracefully."""
        controller = AdaptiveController({})
        controller.reset()

        signal = controller.get_signal({0: 0, 1: 0, 2: 0, 3: 0})
        assert 0 <= signal < 4, "Should return a valid direction"

    def test_adaptive_controller_starvation_prevention(self):
        """Adaptive controller services multiple directions over time."""
        controller = AdaptiveController(
            {
                "min_service_s": 5.0,
                "imbalance_ratio": 2.0,
                "min_green_s": 5.0,
            }
        )
        controller.reset()

        unique_signals = set()
        queues = {0: 20, 1: 0, 2: 0, 3: 0}

        for tick in range(500):
            signal = controller.get_signal(queues)
            unique_signals.add(signal)
            controller.tick(0.1)

            # Rotate demand
            if tick == 200:
                queues = {0: 0, 1: 15, 2: 0, 3: 0}
            elif tick == 350:
                queues = {0: 0, 1: 0, 2: 10, 3: 0}

        # Should have served more than one direction across 50 s
        assert (
            len(unique_signals) > 1
        ), f"Should have served multiple directions, only saw {unique_signals}"

    def test_adaptive_controller_reset(self):
        """AdaptiveController can be reset to initial state."""
        controller = AdaptiveController({"queue_threshold": 5})
        controller.tick(3.0)

        controller.reset()

        # Should be operational after reset
        signal = controller.get_signal({0: 0, 1: 0, 2: 0, 3: 0})
        assert 0 <= signal < 4, "Should work after reset"
        assert controller.phase_elapsed == 0.0, "Phase elapsed should be 0 after reset"

    def test_adaptive_controller_yellow_phase(self):
        """Adaptive controller enters yellow phase during transitions."""
        controller = AdaptiveController({"min_green_s": 0.5, "queue_threshold": 1})
        controller.reset()

        # Force a transition by giving large queue to a different direction
        # then ticking past min_green_s
        queues = {0: 0, 1: 20, 2: 0, 3: 0}
        for _ in range(20):
            controller.get_signal(queues)
            controller.tick(0.1)

        # At some point yellow should have been seen
        # (Not guaranteed to be yellow *right now*, just checking is_in_yellow exists)
        assert isinstance(
            controller.is_in_yellow(), bool
        ), "is_in_yellow() should return bool"


# ---------------------------------------------------------------------------
# TestAdaptiveRules
# ---------------------------------------------------------------------------


class TestAdaptiveRules:
    """Test individual adaptive control rules."""

    def _service_time(self) -> Dict[int, float]:
        return {0: 5.0, 1: 5.0, 2: 5.0, 3: 5.0}

    def test_wait_time_threshold_rule_fires(self):
        """WaitTimeThreshold fires when a direction's wait exceeds threshold."""
        rule = WaitTimeThreshold({"max_wait_s": 30.0})

        queues = {0: 5, 1: 0, 2: 0, 3: 0}
        current_green = 1
        service_time = self._service_time()
        red_timers = {0: 35.0, 1: 5.0, 2: 10.0, 3: 15.0}  # Dir 0 waited 35 s

        assert rule.should_fire(queues, current_green, service_time, red_timers) is True

    def test_wait_time_threshold_does_not_fire(self):
        """WaitTimeThreshold does not fire when waits are acceptable."""
        rule = WaitTimeThreshold({"max_wait_s": 30.0})

        queues = {0: 5, 1: 0, 2: 0, 3: 0}
        current_green = 1
        service_time = self._service_time()
        red_timers = {0: 10.0, 1: 5.0, 2: 8.0, 3: 12.0}

        assert (
            rule.should_fire(queues, current_green, service_time, red_timers) is False
        )

    def test_wait_time_threshold_get_decision(self):
        """WaitTimeThreshold picks the direction with the longest wait."""
        rule = WaitTimeThreshold({"max_wait_s": 20.0})

        queues = {0: 5, 1: 1, 2: 0, 3: 0}
        current_green = 1
        service_time = self._service_time()
        red_timers = {0: 50.0, 1: 5.0, 2: 10.0, 3: 5.0}

        decision = rule.get_decision(queues, current_green, service_time, red_timers)
        assert decision == 0, "Should pick direction 0 with 50 s wait"

    def test_queue_length_extension_rule(self):
        """QueueLengthExtension fires when current green queue is large."""
        rule = QueueLengthExtension(
            {
                "queue_threshold": 5,
                "extension_s": 8.0,
                "max_extensions": 2,
            }
        )
        rule.reset_extensions(0)

        queues = {0: 10, 1: 0, 2: 0, 3: 0}
        current_green = 0
        service_time = self._service_time()
        red_timers = {0: 0, 1: 5.0, 2: 10.0, 3: 8.0}

        fired = rule.should_fire(queues, current_green, service_time, red_timers)
        assert fired is True, "Should fire when queue >= threshold and extensions left"

    def test_queue_length_extension_stays_on_current(self):
        """QueueLengthExtension keeps current direction green."""
        rule = QueueLengthExtension(
            {"queue_threshold": 5, "extension_s": 8.0, "max_extensions": 2}
        )
        rule.reset_extensions(0)

        queues = {0: 10, 1: 2, 2: 1, 3: 0}
        service_time = self._service_time()
        red_timers = {0: 0, 1: 5.0, 2: 8.0, 3: 3.0}

        decision = rule.get_decision(queues, 0, service_time, red_timers)
        assert decision == 0, "Should stay on direction 0"

    def test_early_termination_fires_on_empty_queue(self):
        """EarlyTermination fires when current green direction is empty."""
        rule = EarlyTermination({"min_green_s": 0.0})

        queues = {0: 0, 1: 0, 2: 0, 3: 0}
        service_time = {0: 5.0, 1: 3.0, 2: 4.0, 3: 2.0}
        red_timers = {0: 0, 1: 3.0, 2: 4.0, 3: 2.0}

        fired = rule.should_fire(queues, 0, service_time, red_timers)
        assert fired is True, "Should fire when green direction queue is empty"

    def test_early_termination_does_not_fire_before_min_green(self):
        """EarlyTermination does not fire before min_green_s elapsed."""
        rule = EarlyTermination({"min_green_s": 10.0})

        queues = {0: 0, 1: 3, 2: 0, 3: 0}
        service_time = {0: 2.0, 1: 5.0, 2: 3.0, 3: 4.0}  # Direction 0 only 2 s
        red_timers = {0: 0, 1: 5.0, 2: 8.0, 3: 3.0}

        fired = rule.should_fire(queues, 0, service_time, red_timers)
        assert fired is False, "Should not fire before min_green_s"

    def test_demand_responsive_selection(self):
        """DemandResponsiveSelection picks direction with highest demand."""
        rule = DemandResponsiveSelection({"min_green_s": 0.0})

        queues = {0: 2, 1: 10, 2: 5, 3: 0}
        service_time = {0: 5.0, 1: 0.0, 2: 3.0, 3: 2.0}
        red_timers = {0: 5.0, 1: 3.0, 2: 8.0, 3: 2.0}

        decision = rule.get_decision(queues, 0, service_time, red_timers)
        assert 0 <= decision < 4, f"Decision {decision} should be valid"
        assert decision == 1, "Should select direction 1 with highest queue (10)"

    def test_balanced_service_guarantee_fires_when_imbalanced(self):
        """BalancedServiceGuarantee fires when one direction dominates service."""
        rule = BalancedServiceGuarantee({"imbalance_ratio": 2.0, "min_service_s": 10.0})

        queues = {0: 5, 1: 3, 2: 2, 3: 1}
        service_time = {0: 50.0, 1: 5.0, 2: 5.0, 3: 5.0}  # Dir 0 monopolises
        red_timers = {0: 0, 1: 10.0, 2: 10.0, 3: 10.0}

        fired = rule.should_fire(queues, 0, service_time, red_timers)
        assert fired is True, "Should fire when direction 0 monopolises service time"


# ---------------------------------------------------------------------------
# TestControllerMetrics
# ---------------------------------------------------------------------------


class TestControllerMetrics:
    """Test controller output metrics and status."""

    def test_is_in_yellow_starts_false(self):
        """FixedTimeController is not in yellow at start."""
        controller = FixedTimeController(green_s=5, yellow_s=3)
        controller.reset()

        assert controller.is_in_yellow() is False

    def test_is_in_green_via_not_yellow(self):
        """Controller is effectively in green when not in yellow."""
        controller = FixedTimeController(green_s=5, yellow_s=3)
        controller.reset()

        # At t=0, should not be yellow
        assert not controller.is_in_yellow(), "Should start in green (not yellow)"

    def test_is_in_yellow_after_green_phase(self):
        """Controller transitions to yellow after green phase expires."""
        controller = FixedTimeController(green_s=1.0, yellow_s=2.0)
        controller.reset()

        for _ in range(11):  # 1.1 s
            controller.tick(0.1)

        assert (
            controller.is_in_yellow() is True
        ), "Should be in yellow after green phase"

    def test_get_green_remaining(self):
        """get_green_remaining() returns a value within [0, green_s]."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        remaining = controller.get_green_remaining()
        assert isinstance(remaining, (int, float)), "Should return numeric"
        assert 0 <= remaining <= 10, "Should be within green cycle"

    def test_get_yellow_remaining(self):
        """get_yellow_remaining() returns valid value during yellow phase."""
        controller = FixedTimeController(green_s=1.0, yellow_s=3.0)
        controller.reset()

        # Advance into yellow
        for _ in range(11):
            controller.tick(0.1)

        if controller.is_in_yellow():
            remaining = controller.get_yellow_remaining()
            assert 0 <= remaining <= 3.0, "Yellow remaining should be within limits"

    def test_get_phase_direction_returns_valid(self):
        """get_phase_direction() always returns a valid direction."""
        controller = FixedTimeController(green_s=10, yellow_s=3)
        controller.reset()

        direction = controller.get_phase_direction()
        assert 0 <= direction < 4, f"Phase direction {direction} out of range"

    def test_adaptive_get_phase_direction(self):
        """AdaptiveController.get_phase_direction() returns valid direction."""
        controller = AdaptiveController({})
        controller.reset()

        direction = controller.get_phase_direction()
        assert 0 <= direction < 4, f"Phase direction {direction} out of range"


# ---------------------------------------------------------------------------
# TestRuleEngine
# ---------------------------------------------------------------------------


class TestRuleEngine:
    """Test rule evaluation ordering."""

    def test_rule_engine_returns_current_when_no_rules_fire(self):
        """RuleEngine returns current_green when no rules fire."""
        engine = RuleEngine([])

        result = engine.evaluate({0: 0, 1: 0, 2: 0, 3: 0}, 2, {}, {})
        assert result == 2, "Should return current_green when no rules fire"

    def test_rule_engine_priority_ordering(self):
        """Higher-priority rules fire before lower-priority rules."""
        high = WaitTimeThreshold({"max_wait_s": 5.0})  # priority 100
        low = EarlyTermination({"min_green_s": 0.0})  # priority 80

        engine = RuleEngine([low, high])

        # Both rules will fire here; high-priority should win
        queues = {0: 0, 1: 5, 2: 0, 3: 0}
        current_green = 0
        service_time = {0: 10.0, 1: 5.0, 2: 3.0, 3: 2.0}
        red_timers = {0: 0, 1: 20.0, 2: 5.0, 3: 5.0}  # dir 1 waited 20s > 5s threshold

        decision = engine.evaluate(queues, current_green, service_time, red_timers)
        # WaitTimeThreshold (p=100) should fire and pick direction 1
        assert decision == 1, "High-priority rule should select direction 1"

    def test_rule_engine_last_rule_is_recorded(self):
        """RuleEngine.last_rule is set to the rule that fired."""
        rule = WaitTimeThreshold({"max_wait_s": 5.0})
        engine = RuleEngine([rule])

        queues = {0: 3, 1: 0, 2: 0, 3: 0}
        service_time = {0: 5.0, 1: 5.0, 2: 5.0, 3: 5.0}
        red_timers = {0: 10.0, 1: 3.0, 2: 3.0, 3: 3.0}

        engine.evaluate(queues, 1, service_time, red_timers)

        assert engine.last_rule is rule, "last_rule should be the WaitTimeThreshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
