class FixedTimeController:
    PLAN_A = (25, 3)
    PLAN_B = (39, 3)
    PLAN_C = (54, 3)

    def __init__(self, green_s: int = 30, yellow_s: int = 3):
        self.green_s = max(4, green_s)   # safety: min 4s
        self.yellow_s = max(2, min(5, yellow_s))
        self.cycle = ['N', 'S', 'E', 'W']
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False

    def update(self, dt: float) -> None:
        self.elapsed += dt

        # switch to yellow
        if not self.in_yellow and self.elapsed >= self.green_s:
            self.in_yellow = True
            self.elapsed = 0.0

        # switch to next green
        elif self.in_yellow and self.elapsed >= self.yellow_s:
            self.in_yellow = False
            self.elapsed = 0.0
            self.current_idx = (self.current_idx + 1) % len(self.cycle)

    def get_signal_command(self, state=None) -> str:
        # safety fallback
        if self.in_yellow:
            return self.cycle[(self.current_idx + 1) % len(self.cycle)]
        return self.cycle[self.current_idx]

    def reset(self):
        self.current_idx = 0
        self.elapsed = 0.0
        self.in_yellow = False

    @classmethod
    def plan_60s(cls):
        return cls(green_s=15, yellow_s=3)

    @classmethod
    def plan_90s(cls):
        return cls(green_s=22, yellow_s=3)

    @classmethod
    def plan_120s(cls):
        return cls(green_s=30, yellow_s=3)
