from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseController(ABC):
    """
    Abstract base class for all traffic signal controllers.
    Used by the simulation engine.
    """

    @abstractmethod
    def get_signal_command(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Compute signal commands for the current timestep.

        Input state:
            {
                "current_signals": dict[str, str],   # green/yellow/red
                "queue_lengths": dict[str, int],
                "wait_times": dict[str, float]
            }

        Output:
            {
                "approach_id": "green|yellow|red",
                ...
            }
        """
        pass

    @abstractmethod
    def update(self, state: Dict[str, Any]) -> None:
        """
        Update internal controller state using simulation feedback.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset controller to initial state.
        """
        pass