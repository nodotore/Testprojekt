"""Historischer Max-Drawdown und Korrelation (Auftrag §8: „Korrelation und
maximale historische Drawdowns darstellen").

Reine Funktionen ohne Datenbankzugriff — dieselbe Trennung wie in
``concentration.py``. Beide Kennzahlen benötigen eine Mindestanzahl an
Kurspunkten; bei zu wenigen Punkten wird explizit „Datenlage
unzureichend" zurückgegeben statt eines aus zu wenigen Punkten
erfundenen Werts (Auftrag §11).

**Realistische Erwartung in dieser Umgebung:** Alpha Vantage
``GLOBAL_QUOTE`` (Kostenlos-Paket, siehe ``DATA_SOURCES.md``) liefert
nur den jeweils aktuellen Kurs je Abruf, keine Historie. Eine
aussagekräftige Kursreihe entsteht erst durch wiederholte Abrufe über
die Zeit — bis genug Punkte akkumuliert sind, liefern diese Funktionen
für die meisten Positionen ``computable=False``. Das ist der ehrliche
Normalfall, kein Implementierungsfehler.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

#: Ein Drawdown braucht mindestens zwei Kurspunkte (Höchststand + Folgepunkt).
MIN_POINTS_FOR_DRAWDOWN = 2

#: Eine Korrelation aus zu wenigen Renditepunkten wäre statistisch bedeutungslos.
MIN_OVERLAPPING_POINTS_FOR_CORRELATION = 3


@dataclass(frozen=True)
class DrawdownResult:
    computable: bool
    note: str | None
    max_drawdown_pct: float | None
    peak_date: date | None
    trough_date: date | None


def max_drawdown(price_series: Sequence[tuple[date, float]]) -> DrawdownResult:
    """Größter beobachteter Rückgang vom letzten Höchststand (negativ oder 0)."""

    if len(price_series) < MIN_POINTS_FOR_DRAWDOWN:
        return DrawdownResult(
            computable=False,
            note=(
                f"Mindestens {MIN_POINTS_FOR_DRAWDOWN} Kurspunkte nötig, "
                f"{len(price_series)} vorhanden."
            ),
            max_drawdown_pct=None,
            peak_date=None,
            trough_date=None,
        )

    sorted_series = sorted(price_series, key=lambda point: point[0])
    peak_date, peak_price = sorted_series[0]
    worst_drawdown = 0.0
    worst_peak_date = peak_date
    worst_trough_date = peak_date

    for current_date, price in sorted_series:
        if price > peak_price:
            peak_price = price
            peak_date = current_date
        drawdown = (price - peak_price) / peak_price if peak_price > 0 else 0.0
        if drawdown < worst_drawdown:
            worst_drawdown = drawdown
            worst_peak_date = peak_date
            worst_trough_date = current_date

    return DrawdownResult(
        computable=True,
        note=None,
        max_drawdown_pct=worst_drawdown,
        peak_date=worst_peak_date,
        trough_date=worst_trough_date,
    )


@dataclass(frozen=True)
class CorrelationResult:
    computable: bool
    note: str | None
    correlation: float | None
    overlapping_points: int


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    variance_x = sum((x - mean_x) ** 2 for x in xs)
    variance_y = sum((y - mean_y) ** 2 for y in ys)
    denominator = (variance_x * variance_y) ** 0.5
    if denominator == 0:
        return None
    return covariance / denominator


def pairwise_correlation(
    series_a: Sequence[tuple[date, float]], series_b: Sequence[tuple[date, float]]
) -> CorrelationResult:
    """Pearson-Korrelation der TAGESRENDITEN an überlappenden Handelstagen.

    Bewusst nicht die Korrelation der Kursniveaus selbst — die wäre wegen
    eines gemeinsamen Zeittrends (beide Kurse steigen z. B. einfach über
    die Zeit) irreführend hoch, unabhängig vom tatsächlichen
    Gleichlaufrisiko.
    """

    prices_by_date_a = dict(series_a)
    prices_by_date_b = dict(series_b)
    common_dates = sorted(set(prices_by_date_a) & set(prices_by_date_b))

    if len(common_dates) < MIN_OVERLAPPING_POINTS_FOR_CORRELATION:
        return CorrelationResult(
            computable=False,
            note=(
                f"Mindestens {MIN_OVERLAPPING_POINTS_FOR_CORRELATION} überlappende "
                f"Kurspunkte nötig, {len(common_dates)} vorhanden."
            ),
            correlation=None,
            overlapping_points=len(common_dates),
        )

    prices_a = [prices_by_date_a[d] for d in common_dates]
    prices_b = [prices_by_date_b[d] for d in common_dates]
    if any(p <= 0 for p in prices_a) or any(p <= 0 for p in prices_b):
        return CorrelationResult(
            computable=False,
            note="Nicht-positive Kurswerte in mindestens einer Reihe.",
            correlation=None,
            overlapping_points=len(common_dates),
        )

    returns_a = [(prices_a[i] / prices_a[i - 1]) - 1 for i in range(1, len(prices_a))]
    returns_b = [(prices_b[i] / prices_b[i - 1]) - 1 for i in range(1, len(prices_b))]

    correlation = _pearson(returns_a, returns_b)
    if correlation is None:
        return CorrelationResult(
            computable=False,
            note="Keine Streuung in mindestens einer Renditereihe (Varianz 0).",
            correlation=None,
            overlapping_points=len(common_dates),
        )

    return CorrelationResult(
        computable=True, note=None, correlation=correlation, overlapping_points=len(common_dates)
    )


def correlation_matrix(
    price_series_by_entity: Mapping[str, Sequence[tuple[date, float]]],
) -> dict[tuple[str, str], CorrelationResult]:
    """Paarweise Korrelationen aller Entities — nur das obere Dreieck (a, b) mit a < b."""

    entity_ids = sorted(price_series_by_entity)
    result: dict[tuple[str, str], CorrelationResult] = {}
    for i, entity_a in enumerate(entity_ids):
        for entity_b in entity_ids[i + 1 :]:
            result[(entity_a, entity_b)] = pairwise_correlation(
                price_series_by_entity[entity_a], price_series_by_entity[entity_b]
            )
    return result
