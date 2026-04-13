from typing import Dict

class FixedTimeController:
    PLAN_A = (25, 3)
    PLAN_B = (39, 3)
    PLAN_C = (54, 3)

    def __init__(self, green_s: int = 30, yellow_s: int = 3):
        self.green_s = green_s
        self.yellow_s = yellow_s
        self.cycle = ['N', 'S', 'E', 'W']
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False

    def tick(self, dt: float) -> None:
        self.elapsed += dt

        if self.elapsed >= self.green_s:
            self.elapsed = 0.0
            self.current_idx = (self.current_idx + 1) % len(self.cycle)

    def get_signal(self, queue_lengths: Dict[str, int]) -> str:
        return self.cycle[self.current_idx]