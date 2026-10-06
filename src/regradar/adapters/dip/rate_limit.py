"""Building block (DIP adapter): minimum interval between API requests."""

import time
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            delay = self._last + self._min_interval - self._clock()
            if delay > 0:
                self._sleep(delay)
        self._last = self._clock()
