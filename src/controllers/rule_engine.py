from typing import Dict, Any, List


class Rule:
    """
    Base class for adaptive traffic control rules.
    """

    def apply(self, state: Dict[str, Any], context: Dict[str, Any]) -> None:
        raise NotImplementedError


class RuleEngine:
    """
    Evaluates adaptive rules sequentially.
    """

    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def evaluate(self, state: Dict[str, Any], context: Dict[str, Any]) -> None:
        for rule in self.rules:
            rule.apply(state, context)


# ---------- Rule Skeletons ----------

class QueueBasedExtension(Rule):
    def apply(self, state, context):
        pass


class WaitTimeThreshold(Rule):
    def apply(self, state, context):
        pass


class DemandResponsivePhaseSelection(Rule):
    def apply(self, state, context):
        pass


class PhaseSkipping(Rule):
    def apply(self, state, context):
        pass


class EarlyTermination(Rule):
    def apply(self, state, context):
        pass


class MaximumWaitPrevention(Rule):
    def apply(self, state, context):
        pass