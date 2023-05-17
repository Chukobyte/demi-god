class Timer:
    def __init__(self, time: float):
        self.time = time
        self.time_remaining = time

    def tick(self, delta_time: float) -> "Timer":
        self.time_remaining = max(self.time_remaining - delta_time, 0.0)
        return self

    def reset(self) -> None:
        self.time_remaining = self.time

    def has_stopped(self) -> bool:
        return self.time_remaining <= 0.0
