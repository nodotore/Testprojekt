"""Einfacher Sliding-Window-Rate-Limiter (Auftrag §4: „Rate Limiting").

Uhr und Sleep-Funktion sind injizierbar, damit Tests das Verhalten bei
Überschreitung des Limits prüfen können, ohne tatsächlich zu warten.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    """Erlaubt höchstens ``max_calls`` Aufrufe innerhalb von ``period_seconds``."""

    def __init__(
        self,
        max_calls: int,
        period_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_calls < 1:
            raise ValueError("max_calls muss mindestens 1 sein.")
        if period_seconds <= 0:
            raise ValueError("period_seconds muss positiv sein.")
        self._max_calls = max_calls
        self._period = period_seconds
        self._clock = clock
        self._sleep = sleep
        self._call_times: deque[float] = deque()

    def _evict_expired(self, now: float) -> None:
        while self._call_times and now - self._call_times[0] >= self._period:
            self._call_times.popleft()

    def acquire(self) -> None:
        """Blockiert (per ``sleep``) so lange, bis ein weiterer Aufruf erlaubt ist."""

        now = self._clock()
        self._evict_expired(now)

        if len(self._call_times) >= self._max_calls:
            wait_seconds = self._period - (now - self._call_times[0])
            if wait_seconds > 0:
                self._sleep(wait_seconds)
            now = self._clock()
            self._evict_expired(now)

        self._call_times.append(self._clock())

    @property
    def current_load(self) -> int:
        """Anzahl der Aufrufe im aktuellen Zeitfenster (für Diagnose/Tests)."""

        now = self._clock()
        self._evict_expired(now)
        return len(self._call_times)

    @property
    def max_calls(self) -> int:
        return self._max_calls

    @property
    def period_seconds(self) -> float:
        return self._period
