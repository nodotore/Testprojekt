"""Backtest-Kennzahlen (Auftrag §9: „CAGR, Volatilität, Sharpe/Sortino,
maximalen Drawdown und Turnover zeigen").

Reine Funktionen über eine periodische Renditereihe. Der maximale
Drawdown wird bewusst NICHT hier neu implementiert, sondern aus
``portfolio/risk_metrics.py::max_drawdown`` wiederverwendet (dieselbe
Kennzahl, ein einziger Berechnungsweg, siehe ``backtesting/report.py``).

**Annahme (Auftrag §1: deutlich zu kennzeichnen):** Sharpe/Sortino
benötigen einen risikofreien Zins — Standardwert ``0.0`` je Periode
(keine Rendite-Bereinigung), explizit über ``risk_free_rate_per_period``
überschreibbar. Kein stiller Default tief im Code, sondern ein
sichtbarer Funktionsparameter.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt
from statistics import pstdev

#: Standardannahme: monatliches Rebalancing. Wird von jeder Kennzahl als
#: expliziter Parameter durchgereicht, nie stillschweigend vorausgesetzt.
DEFAULT_PERIODS_PER_YEAR = 12


def cagr(total_return: float, *, years: float) -> float | None:
    """Compound Annual Growth Rate aus einer Gesamtrendite über ``years`` Jahre.

    Liefert ``None`` bei nicht-positiver Basis (Totalverlust oder mehr) —
    CAGR ist dafür mathematisch nicht definiert (keine reelle Wurzel bei
    ungerader Wurzelordnung aus einer negativen Zahl garantiert).
    """

    if years <= 0:
        return None
    base = 1 + total_return
    if base <= 0:
        return None
    return base ** (1 / years) - 1


def annualized_volatility(
    period_returns: Sequence[float], *, periods_per_year: int = DEFAULT_PERIODS_PER_YEAR
) -> float | None:
    """Annualisierte Standardabweichung periodischer Renditen. ``None`` bei < 2 Perioden."""

    if len(period_returns) < 2:
        return None
    return pstdev(period_returns) * sqrt(periods_per_year)


def sharpe_ratio(
    period_returns: Sequence[float],
    *,
    risk_free_rate_per_period: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float | None:
    """Sharpe Ratio auf Basis periodischer Überschussrenditen (annualisiert).

    ``None`` bei < 2 Perioden oder einer Volatilität von 0 (Division
    durch 0 wird vermieden statt einen unendlichen Wert vorzutäuschen).
    """

    if len(period_returns) < 2:
        return None
    excess_returns = [r - risk_free_rate_per_period for r in period_returns]
    mean_excess = sum(excess_returns) / len(excess_returns)
    volatility = pstdev(excess_returns)
    if volatility == 0:
        return None
    return (mean_excess / volatility) * sqrt(periods_per_year)


def sortino_ratio(
    period_returns: Sequence[float],
    *,
    risk_free_rate_per_period: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> float | None:
    """Wie ``sharpe_ratio``, aber nur mit Abwärtsvolatilität (Semi-Deviation
    relativ zu 0 über periodische Überschussrenditen)."""

    if len(period_returns) < 2:
        return None
    excess_returns = [r - risk_free_rate_per_period for r in period_returns]
    mean_excess = sum(excess_returns) / len(excess_returns)
    downside = [min(r, 0.0) for r in excess_returns]
    downside_deviation = pstdev(downside)
    if downside_deviation == 0:
        return None
    return (mean_excess / downside_deviation) * sqrt(periods_per_year)


def turnover(previous_holdings: Sequence[str], new_holdings: Sequence[str]) -> float:
    """Anteil der Portfoliopositionen, die bei einem Rebalancing wechseln.

    Standarddefinition: (hinzugekommene + weggefallene Positionen) /
    (2 × durchschnittliche Positionsanzahl) — 0.0 bei unveränderten
    Positionen, 1.0 bei komplett neuem Portfolio.
    """

    previous_set = set(previous_holdings)
    new_set = set(new_holdings)
    if not previous_set and not new_set:
        return 0.0
    added = len(new_set - previous_set)
    removed = len(previous_set - new_set)
    average_size = (len(previous_set) + len(new_set)) / 2
    if average_size == 0:
        return 0.0
    return (added + removed) / (2 * average_size)


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    cagr: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    average_turnover: float | None
