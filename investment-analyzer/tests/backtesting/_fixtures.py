"""Gemeinsame Testdaten-Hilfsfunktionen für die Backtesting-Tests.

Baut ein synthetisches, vollständiges Fundamentaldaten-Profil (analog zu
den bereits etablierten „Firma E/G"-Fixtures in ``tests/valuation``/
``tests/reports``), damit ``score_entity`` zuverlässig einen
berechenbaren Score liefert — notwendig, damit
``backtesting.strategy.select_top_n`` die Entity nicht mangels
Datenlage ausschließt.
"""

from __future__ import annotations

from datetime import date, datetime

from investment_analyzer.connectors.models import Source
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind


def make_datapoint(
    *,
    entity: Entity,
    source: Source,
    metric: Metric,
    period_end: date,
    value: float,
    retrieved_at_utc: datetime,
) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=metric.value,
        period_start=None,
        period_end=period_end,
        published_at=period_end,
        retrieved_at_utc=retrieved_at_utc,
        value_raw=str(value),
        value_normalized=value,
        unit="USD",
        currency="USD",
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/doc",
        document_type="10-K",
        content_hash=f"hash-{entity.id}-{metric.value}-{period_end.isoformat()}-{retrieved_at_utc.isoformat()}",
        document_id=None,
    )


def insert_full_fundamentals(
    session,
    entity: Entity,
    source: Source,
    *,
    retrieved_at_utc: datetime,
    revenue_base: float = 1000.0,
    include_dividends: bool = True,
) -> None:
    """Vollständiges, hand-plausibles Fundamentaldatenprofil über vier Jahre
    (10 % Umsatzwachstum/Jahr) — ausreichend für einen berechenbaren
    ``ScoreResult`` (Finanzqualität, Bewertung via DCF, Wachstum,
    Bilanzstärke, Datenqualität).

    ``include_dividends=False`` lässt ``Metric.DIVIDENDS_PAID`` weg —
    für Backtest-Engine-Tests, die eine Perioden-Rendite ohne den
    Dividenden-Schätzungs-Einfluss (``estimate_dividends_per_share``)
    von Hand nachrechnen wollen.
    """

    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [revenue_base * (1.1**i) for i in range(4)]
    for d, u in zip(jahre, umsatz, strict=True):
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.1, retrieved_at_utc=retrieved_at_utc))

    last = jahre[-1]
    fields: list[tuple[Metric, float]] = [
        (Metric.OPERATING_INCOME, revenue_base * 0.18),
        (Metric.DEPRECIATION_AND_AMORTIZATION, revenue_base * 0.04),
        (Metric.TOTAL_EQUITY, revenue_base * 1.0),
        (Metric.LONG_TERM_DEBT, revenue_base * 0.3),
        (Metric.SHORT_TERM_DEBT, revenue_base * 0.1),
        (Metric.CASH_AND_EQUIVALENTS, revenue_base * 0.2),
        (Metric.SHARES_DILUTED, 100.0),
        (Metric.EPS_DILUTED, 2.0),
        (Metric.INTEREST_EXPENSE, revenue_base * 0.02),
        (Metric.CURRENT_ASSETS, revenue_base * 0.5),
        (Metric.CURRENT_LIABILITIES, revenue_base * 0.25),
        (Metric.GROSS_PROFIT, revenue_base * 0.5),
    ]
    if include_dividends:
        fields.append((Metric.DIVIDENDS_PAID, revenue_base * 0.03))
    for metric, value in fields:
        session.add(make_datapoint(entity=entity, source=source, metric=metric, period_end=last, value=value, retrieved_at_utc=retrieved_at_utc))


def insert_weak_fundamentals(
    session,
    entity: Entity,
    source: Source,
    *,
    retrieved_at_utc: datetime,
    revenue_base: float = 1000.0,
) -> None:
    """Gegenstück zu ``insert_full_fundamentals``: schrumpfender Umsatz, dünne
    Margen, hohe Verschuldung — ein deutlich schwächeres, aber ebenfalls
    vollständig berechenbares Profil (für Ranking-Tests in
    ``test_strategy.py``)."""

    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [revenue_base * (0.95**i) for i in range(4)]
    for d, u in zip(jahre, umsatz, strict=True):
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.02, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05, retrieved_at_utc=retrieved_at_utc))
        session.add(make_datapoint(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.01, retrieved_at_utc=retrieved_at_utc))

    last = jahre[-1]
    for metric, value in (
        (Metric.OPERATING_INCOME, revenue_base * 0.02),
        (Metric.DEPRECIATION_AND_AMORTIZATION, revenue_base * 0.04),
        (Metric.TOTAL_EQUITY, revenue_base * 0.3),
        (Metric.LONG_TERM_DEBT, revenue_base * 1.5),
        (Metric.SHORT_TERM_DEBT, revenue_base * 0.5),
        (Metric.CASH_AND_EQUIVALENTS, revenue_base * 0.05),
        (Metric.SHARES_DILUTED, 100.0),
        (Metric.EPS_DILUTED, 0.1),
        (Metric.INTEREST_EXPENSE, revenue_base * 0.1),
        (Metric.CURRENT_ASSETS, revenue_base * 0.2),
        (Metric.CURRENT_LIABILITIES, revenue_base * 0.3),
        (Metric.GROSS_PROFIT, revenue_base * 0.15),
    ):
        session.add(make_datapoint(entity=entity, source=source, metric=metric, period_end=last, value=value, retrieved_at_utc=retrieved_at_utc))
