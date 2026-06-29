from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict

import simulation
from controller import AdaptiveController, FixedTimeController

defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 3

noOfSignals = 4
currentGreen = 0
nextGreen = 1
currentYellow = 0

signalCoods = [(810, 230), (810, 570), (530, 570), (530, 230)]
signalTimerCoods = [(810, 210), (810, 550), (530, 550), (530, 210)]
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(880, 210), (880, 550), (480, 550), (480, 210)]


class TrafficSignal:
    def __init__(self, red: float, yellow: float, green: float):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


signals = [
    TrafficSignal(defaultRed, defaultYellow, defaultGreen[index])
    for index in range(noOfSignals)
]


def _load_adaptive_params() -> Dict:
    """Load and validate adaptive controller parameters from JSON config."""
    _config_path = Path(__file__).resolve().parent / "configs" / "adaptive_params.json"

    if not _config_path.exists():
        print(f"[WARN] Config file not found at {_config_path}, using defaults")
        return {}

    try:
        with _config_path.open("r", encoding="utf-8") as config_file:
            params = json.load(config_file)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Config file is invalid JSON: {e}")
        raise ValueError(f"Invalid adaptive_params.json: {e}")
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        raise

    # Validate parameter ranges
    PARAM_BOUNDS = {
        "max_wait_s": (1.0, 300.0),
        "queue_threshold": (1, 100),
        "extension_s": (1.0, 60.0),
        "max_extensions": (0, 10),
        "min_green_s": (2.0, 90.0),
        "peak_start_s": (0.0, 3600.0),
        "peak_end_s": (0.0, 3600.0),
        "boost_factor": (1.0, 5.0),
        "peak_min_queue": (0, 100),
        "imbalance_ratio": (1.0, 10.0),
        "min_service_s": (1.0, 60.0),
    }

    for key, (min_val, max_val) in PARAM_BOUNDS.items():
        if key in params:
            value = params[key]
            if not isinstance(value, (int, float)):
                print(f"[WARN] {key} must be numeric, got {type(value)}, using default")
                del params[key]
                continue

            if value < min_val or value > max_val:
                print(
                    f"[WARN] {key}={value} out of bounds [{min_val}, {max_val}], using default"
                )
                del params[key]

    return params


_adaptive_params = _load_adaptive_params()

fixed_controller = FixedTimeController(green_s=10, yellow_s=3)
adaptive_controller = AdaptiveController(_adaptive_params)
active_controller: FixedTimeController | AdaptiveController = fixed_controller
controller_mode = "fixed"


def _get_phase_direction() -> int:
    if hasattr(active_controller, "get_phase_direction"):
        return active_controller.get_phase_direction()
    return active_controller.get_signal({})


def _get_pending_direction() -> int:
    if hasattr(active_controller, "get_pending_direction"):
        return active_controller.get_pending_direction()
    return (_get_phase_direction() + 1) % noOfSignals


def _sync_signal_values() -> None:
    for index, signal in enumerate(signals):
        if index == currentGreen:
            if currentYellow:
                signal.yellow = math.ceil(active_controller.get_yellow_remaining())
                signal.green = 0
                signal.red = 0
                signal.signalText = str(signal.yellow)
            else:
                signal.green = math.ceil(active_controller.get_green_remaining())
                signal.yellow = defaultYellow
                signal.red = 0
                signal.signalText = str(signal.green)
        else:
            signal.green = defaultGreen[index]
            signal.yellow = defaultYellow
            if controller_mode == "fixed":
                signal.red = math.ceil(fixed_controller.time_until_green(index))
                signal.signalText = str(signal.red) if signal.red <= 10 else "---"
            else:
                signal.red = math.ceil(adaptive_controller.red_timers.get(index, 0.0))
                signal.signalText = "---"


def update_signals_tick(dt: float, queues: Dict[int, int]) -> None:
    """Advance controller state and sync legacy globals each frame."""

    global currentGreen, currentYellow, nextGreen

    was_in_yellow = bool(currentYellow)
    previous_green = currentGreen

    active_controller.tick(dt)
    active_controller.get_signal(queues)

    in_yellow = active_controller.is_in_yellow()
    display_green = _get_phase_direction()
    pending_green = _get_pending_direction()

    if in_yellow and not was_in_yellow:
        simulation.reset_direction_stops(previous_green)

    currentGreen = display_green
    currentYellow = 1 if in_yellow else 0
    nextGreen = pending_green if in_yellow else (display_green + 1) % noOfSignals

    # Validate signal state to prevent deadlock conditions
    assert (
        0 <= currentGreen < noOfSignals
    ), f"Invalid currentGreen={currentGreen}, must be in [0, {noOfSignals-1}]"
    assert currentYellow in (
        0,
        1,
    ), f"Invalid currentYellow={currentYellow}, must be 0 or 1"
    assert (
        0 <= nextGreen < noOfSignals
    ), f"Invalid nextGreen={nextGreen}, must be in [0, {noOfSignals-1}]"

    simulation.set_signal_state(currentGreen, currentYellow)
    _sync_signal_values()


def sync_controller_state(queues: Dict[int, int] | None = None) -> None:
    update_signals_tick(0.0, queues or {0: 0, 1: 0, 2: 0, 3: 0})


def set_controller_mode(mode: str, queues: Dict[int, int] | None = None) -> None:
    global active_controller, controller_mode

    if mode == "adaptive":
        active_controller = adaptive_controller
        controller_mode = "adaptive"
        adaptive_controller.reset()
    else:
        active_controller = fixed_controller
        controller_mode = "fixed"
        fixed_controller.reset()

    sync_controller_state(queues)
