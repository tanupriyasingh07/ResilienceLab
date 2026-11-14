import time
import threading
from enum import Enum
from typing import Callable


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")

        if reset_timeout <= 0:
            raise ValueError("reset_timeout must be positive")

        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.clock = clock

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = None
        self.probe_in_progress = False

        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                elapsed = self.clock() - self.opened_at

                if elapsed < self.reset_timeout:
                    return False

                self.state = CircuitState.HALF_OPEN
                self.probe_in_progress = False

            if self.state == CircuitState.HALF_OPEN:
                if self.probe_in_progress:
                    return False

                self.probe_in_progress = True
                return True

            return False

    def record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.opened_at = None
            self.probe_in_progress = False

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1

            if self.state == CircuitState.HALF_OPEN:
                self._open()
                return

            if self.failure_count >= self.failure_threshold:
                self._open()

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = self.clock()
        self.probe_in_progress = False