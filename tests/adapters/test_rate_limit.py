from regradar.adapters.dip.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_first_call_does_not_wait() -> None:
    clock = FakeClock()

    RateLimiter(1.0, clock=clock, sleep=clock.sleep).wait()

    assert clock.sleeps == []


def test_waits_for_remaining_interval() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1.0, clock=clock, sleep=clock.sleep)

    limiter.wait()
    clock.now += 0.25
    limiter.wait()
    limiter.wait()

    assert clock.sleeps == [0.75, 1.0]


def test_does_not_wait_after_interval_passed() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1.0, clock=clock, sleep=clock.sleep)

    limiter.wait()
    clock.now += 1.5
    limiter.wait()

    assert clock.sleeps == []
