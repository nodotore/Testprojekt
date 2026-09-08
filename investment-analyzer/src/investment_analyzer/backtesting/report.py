"""Orchestrierung: ``BacktestReport`` (Auftrag §9).

Führt die Rebalancing-Engine über eine Folge von Stichtagen aus,
berechnet die in Auftrag §9 geforderten Kennzahlen (CAGR, Volatilität,
Sharpe/Sortino, maximaler Drawdown — wiederverwendet aus
``portfolio/risk_metrics.py``, Turnover) und dokumentiert offene Lücken
explizit statt sie wegzulassen.

**Bewusste, dokumentierte Lücke — kein Index-Vergleich:** Auftrag §9
verlangt „Ergebnisse gegen einfache Indizes vergleichen". In der
Kostenlos-Datenquellen-Variante (siehe ``DATA_SOURCES.md``) ist keine
Index-/Benchmark-Kursquelle angebunden (Alpha Vantage Free liefert nur
Einzelwerte je Symbol). ``build_backtest_report`` akzeptiert daher
optional eine bereits vorliegende Benchmark-Renditereihe
(``benchmark_period_returns``) — wird sie nicht übergeben, bleibt der
Vergleich explizit ``None`` statt eines erfundenen Werts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from investment_analyzer.backtesting.engine import BacktestRun, run_backtest
from investment_analyzer.backtesting.metrics import (
    DEFAULT_PERIODS_PER_YEAR,
    annualized_volatility,
    cagr,
    sharpe_ratio,
    sortino_ratio,
)
from investment_analyzer.backtesting.metrics import turnover as compute_turnover
from investment_analyzer.db.types import utc_now
from investment_analyzer.portfolio.assumptions import PortfolioAssumptions
from investment_analyzer.portfolio.risk_metrics import DrawdownResult, max_drawdown

#: Aus Auftrag §9 (noch) nicht umgesetzte Bausteine — explizit benannt statt
#: stillschweigend wegzulassen (dasselbe Muster wie
#: ``risk/warning_signals.py::NOT_YET_IMPLEMENTABLE_SIGNALS`` und
#: ``scoring/score.py::NOT_YET_IMPLEMENTABLE_COMPONENTS``).
NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES: tuple[str, ...] = (
    "benchmark_kursreihe",
    "waehrungsumrechnung",
    "vollstaendiges_survivorship_universum",
)


@dataclass(frozen=True)
class BacktestReport:
    generated_at_utc: datetime
    run: BacktestRun
    total_return: float | None
    years: float
    cagr: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: DrawdownResult
    average_turnover: float | None
    benchmark_total_return: float | None
    gaps: tuple[str, ...]


def _compound(period_returns: list[float]) -> float:
    nav = 1.0
    for r in period_returns:
        nav *= 1 + r
    return nav - 1


def build_backtest_report(
    session: Session,
    rebalance_dates: list[datetime],
    *,
    top_n: int,
    assumptions: PortfolioAssumptions | None = None,
    weights: dict[str, float] | None = None,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    risk_free_rate_per_period: float = 0.0,
    benchmark_period_returns: list[float] | None = None,
) -> BacktestReport:
    """Baut einen vollständigen Backtest-Bericht (Auftrag §9)."""

    run = run_backtest(session, rebalance_dates, top_n=top_n, assumptions=assumptions, weights=weights)

    period_returns = [p.portfolio_return for p in run.periods if p.portfolio_return is not None]
    gaps: list[str] = list(NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES)

    total_return: float | None = None
    if run.periods and len(period_returns) == len(run.periods):
        total_return = _compound(period_returns)
    else:
        missing = len(run.periods) - len(period_returns)
        if missing:
            gaps.append(
                f"{missing} von {len(run.periods)} Perioden ohne berechenbare "
                "Portfoliorendite (fehlende Kursdaten) — Gesamtrendite nicht berechenbar."
            )

    years = (rebalance_dates[-1] - rebalance_dates[0]).days / 365.25

    nav_points = [(moment.date(), nav) for moment, nav in run.nav_series]
    drawdown = max_drawdown(nav_points)

    turnovers = [
        compute_turnover(run.periods[i - 1].holdings, run.periods[i].holdings)
        for i in range(1, len(run.periods))
    ]
    average_turnover = sum(turnovers) / len(turnovers) if turnovers else None

    benchmark_total_return: float | None = None
    if benchmark_period_returns:
        benchmark_total_return = _compound(benchmark_period_returns)
        gaps = [g for g in gaps if g != "benchmark_kursreihe"]

    return BacktestReport(
        generated_at_utc=utc_now(),
        run=run,
        total_return=total_return,
        years=years,
        cagr=cagr(total_return, years=years) if total_return is not None else None,
        annualized_volatility=annualized_volatility(period_returns, periods_per_year=periods_per_year),
        sharpe_ratio=sharpe_ratio(
            period_returns, risk_free_rate_per_period=risk_free_rate_per_period,
            periods_per_year=periods_per_year,
        ),
        sortino_ratio=sortino_ratio(
            period_returns, risk_free_rate_per_period=risk_free_rate_per_period,
            periods_per_year=periods_per_year,
        ),
        max_drawdown=drawdown,
        average_turnover=average_turnover,
        benchmark_total_return=benchmark_total_return,
        gaps=tuple(gaps),
    )
