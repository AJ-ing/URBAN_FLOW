from controllers.adaptive_controller import AdaptiveController
from controllers.rule_engine import RuleEngine


def test_deterministic_behavior():
    engine = RuleEngine(rules=[])
    controller = AdaptiveController(engine)

    state = {
        "current_signals": {"N": "red"},
        "queue_lengths": {"N": 3},
        "wait_times": {"N": 10.0}
    }

    out1 = controller.get_signal_command(state)
    out2 = controller.get_signal_command(state)

    assert out1 == out2


def test_safety_signal_values():
    engine = RuleEngine(rules=[])
    controller = AdaptiveController(engine)

    state = {
        "current_signals": {"N": "green"},
        "queue_lengths": {},
        "wait_times": {}
    }

    output = controller.get_signal_command(state)
    assert output["N"] in {"green", "yellow", "red"}