from __future__ import annotations

import pytest

from investment_analyzer.connectors.rate_limiter import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_erlaubt_aufrufe_bis_zum_limit_ohne_warten() -> None:
    clock = FakeClock()
    sleeps: list[float] = []
    limiter = RateLimiter(3, 60.0, clock=clock, sleep=sleeps.append)

    for _ in range(3):
        limiter.acquire()

    assert sleeps == []
    assert limiter.current_load == 3


def test_wartet_bei_ueberschreitung_des_limits() -> None:
    clock = FakeClock()

    def fake_sleep(seconds: float) -> None:
        clock.advance(seconds)

    limiter = RateLimiter(2, 60.0, clock=clock, sleep=fake_sleep)

    limiter.acquire()
    limiter.acquire()
    limiter.acquire()  # muss warten, bis der erste Aufruf aus dem Fenster fällt

    assert clock.now >= 60.0


def test_alte_aufrufe_fallen_nach_ablauf_des_fensters_heraus() -> None:
    clock = FakeClock()
    sleeps: list[float] = []
    limiter = RateLimiter(1, 10.0, clock=clock, sleep=sleeps.append)

    limiter.acquire()
    clock.advance(11.0)
    limiter.acquire()

    assert sleeps == []  # kein Warten nötig, das Fenster ist bereits abgelaufen


@pytest.mark.parametrize("max_calls,period", [(0, 10.0), (-1, 10.0)])
def test_ungueltige_max_calls_wirft(max_calls: int, period: float) -> None:
    with pytest.raises(ValueError):
        RateLimiter(max_calls, period)


def test_ungueltige_period_wirft() -> None:
    with pytest.raises(ValueError):
        RateLimiter(5, 0.0)
