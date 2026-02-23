from typing import Dict, Any
from controllers.base_controller import BaseController
from controllers.rule_engine import RuleEngine


class AdaptiveController(BaseController):
    """
    Rule-based adaptive signal controller.
    """

    def __init__(self, rule_engine: RuleEngine):
        self.rule_engine = rule_engine
        self.context: Dict[str, Any] = {}

    def reset(self) -> None:
        self.context = {}

    def update(self, state: Dict[str, Any]) -> None:
        self.rule_engine.evaluate(state, self.context)

    def get_signal_command(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Returns phase commands per approach.
        Defaults to existing signals if rules do not modify context.
        """
        self.update(state)
        return self.context.get("signal_command", state["current_signals"])