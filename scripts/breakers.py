import time
from dataclasses import dataclass

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_seconds: int = 30
    fail_count: int = 0
    opened_at: float | None = None

    def call(self, fn, *args, **kwargs):
        if self.opened_at and time.time() - self.opened_at < self.recovery_seconds:
            raise RuntimeError("Circuit open — downstream provavelmente fora")
        try:
            result = fn(*args, **kwargs)
            self.fail_count = 0
            self.opened_at = None
            return result
        except Exception:
            self.fail_count += 1
            if self.fail_count >= self.failure_threshold:
                self.opened_at = time.time()
            raise
