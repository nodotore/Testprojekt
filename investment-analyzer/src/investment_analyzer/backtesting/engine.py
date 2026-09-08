"""Rebalancing-Engine (Auftrag §9): führt die Top-N-Strategie über eine
Folge von Rebalancing-Stichtagen aus und aggregiert die Ergebnisse zu
einer Portfolio-NAV-Zeitreihe.

Jeder Rebalancing-Schritt verwendet ausschließlich zu diesem Stichtag
bekannte Daten (``as_of``-Parameter durchgereicht bis zu
``fundamentals/series.py``, ADR-6) — derselbe Mechanismus, der isoliert
in ``tests/backtesting/test_universe.py`` nachgewiesen wird, trägt hier
den vollständigen Rebalancing-Ablauf (zweiter Teil des Look-ahead-
Nachweises, siehe ``tests/backtesting/test_engine.py``).

**Bewusste, dokumentierte Vereinfachung:** Gleichgewichtung
(``1 / Anzahl Positionen``) je Rebalancing, kein risikoadjustiertes
Gewichtungsschema (nicht Bestandteil von Auftrag §9). Fehlt für eine
ausgewählte Position der Kurs am Perioden-Start ODER -Ende, wird diese
Position für die betroffene Periode aus der Renditeberechnung
ausgeschlossen (nicht geraten, Auftrag §11) — die Portfoliorendite der
Periode ist dann der Durchschnitt der übrigen, berechenbaren Positionen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from investment_analyzer.backtesting.period_return import (
    compute_period_return,
    estimate_dividends_per_share,
)
from investment_analyzer.backtesting.strategy import select_top_n
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals import series
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.portfolio.assumptions import PortfolioAssumptions


@dataclass(frozen=True)
class RebalancePeriod:
    start: datetime
    end: datetime
    holdings: tuple[str, ...]
    portfolio_return: float | None
    excluded_holdings: tuple[str, ...]


@dataclass(frozen=True)
class BacktestRun:
    rebalance_dates: tuple[datetime, ...]
    periods: tuple[RebalancePeriod, ...]
    nav_series: tuple[tuple[datetime, float], ...]


def _position_return(
    session: Session,
    entity_id: str,
    *,
    period_start: datetime,
    period_end: datetime,
    transaction_cost_pct: float,
) -> float | None:
    entity = session.get(Entity, entity_id)
    if entity is None:
        return None

    price_start_point = series.get_latest_value(session, entity, Metric.PRICE_CLOSE, as_of=period_start)
    price_end_point = series.get_latest_value(session, entity, Metric.PRICE_CLOSE, as_of=period_end)
    if price_start_point is None or price_end_point is None:
        return None
    price_start = price_start_point[1]
    price_end = price_end_point[1]
    if price_start <= 0:
        return None

    dividends_point = series.get_latest_annual_value(
        session, entity, Metric.DIVIDENDS_PAID, as_of=period_end
    )
    shares_point = series.get_latest_annual_value(
        session, entity, Metric.SHARES_DILUTED, as_of=period_end
    )
    dividends_per_share = (
        estimate_dividends_per_share(
            dividends_point[1] if dividends_point else None,
            shares_point[1] if shares_point else None,
        )
        or 0.0
    )

    result = compute_period_return(
        price_start=price_start,
        price_end=price_end,
        dividends_per_share=dividends_per_share,
        transaction_cost_pct=transaction_cost_pct,
    )
    return result.net_return


def run_backtest(
    session: Session,
    rebalance_dates: list[datetime],
    *,
    top_n: int,
    assumptions: PortfolioAssumptions | None = None,
    weights: dict[str, float] | None = None,
) -> BacktestRun:
    """Führt die Top-N-Strategie über ``rebalance_dates`` aus (aufsteigend sortiert).

    Zwischen zwei aufeinanderfolgenden Stichtagen wird das zum FRÜHEREN
    Stichtag ausgewählte, gleichgewichtete Portfolio bis zum nächsten
    Stichtag gehalten — ``rebalance_dates`` mit N Einträgen liefert
    N-1 Halteperioden.
    """

    if len(rebalance_dates) < 2:
        raise ValueError("rebalance_dates muss mindestens zwei Stichtage enthalten.")
    if list(rebalance_dates) != sorted(rebalance_dates):
        raise ValueError("rebalance_dates muss aufsteigend sortiert sein.")

    resolved_assumptions = assumptions or PortfolioAssumptions()

    periods: list[RebalancePeriod] = []
    nav = 1.0
    nav_series: list[tuple[datetime, float]] = [(rebalance_dates[0], nav)]

    # Bewusst kein strict=True: rebalance_dates[1:] ist per Konstruktion um
    # ein Element kürzer als rebalance_dates -- das paart aufeinanderfolgende
    # Stichtage korrekt (Start/Ende jeder Halteperiode).
    for period_start, period_end in zip(rebalance_dates, rebalance_dates[1:], strict=False):
        holdings = tuple(select_top_n(session, as_of=period_start, n=top_n, weights=weights))

        position_returns: list[float] = []
        excluded: list[str] = []
        for entity_id in holdings:
            position_return = _position_return(
                session,
                entity_id,
                period_start=period_start,
                period_end=period_end,
                transaction_cost_pct=resolved_assumptions.transaction_cost_pct,
            )
            if position_return is None:
                excluded.append(entity_id)
            else:
                position_returns.append(position_return)

        portfolio_return = (
            sum(position_returns) / len(position_returns) if position_returns else None
        )
        if portfolio_return is not None:
            nav *= 1 + portfolio_return
        nav_series.append((period_end, nav))

        periods.append(
            RebalancePeriod(
                start=period_start,
                end=period_end,
                holdings=holdings,
                portfolio_return=portfolio_return,
                excluded_holdings=tuple(excluded),
            )
        )

    return BacktestRun(
        rebalance_dates=tuple(rebalance_dates), periods=tuple(periods), nav_series=tuple(nav_series)
    )
