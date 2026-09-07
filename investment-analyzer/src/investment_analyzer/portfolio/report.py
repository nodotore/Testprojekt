"""Orchestrierung: Portfolio-Positionen aus der DB → ``PortfolioReport``
(Auftrag §8 „Portfolio- und Vergleichsfunktionen").

Analog zu ``fundamentals/report.py``, ``valuation/report.py``,
``news/report.py``: liest die aktuellen Bestände samt jeweils jüngstem
bekannten Kurs (``fundamentals/series.py``) und Entity-Klassifikation
(SIC-Branche, Land), wendet die reinen Berechnungsfunktionen an
(Konzentration, Korrelation, Drawdown, Positionsgrößen-Bandbreite) und
liefert einen typisierten, sofort UI-/Export-fähigen Bericht — inkl.
expliziter Auflistung dessen, was mangels Daten NICHT berechnet werden
konnte (``gaps``), statt es stillschweigend weg­zulassen (Auftrag §11).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals import series
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.portfolio.assumptions import PortfolioAssumptions
from investment_analyzer.portfolio.concentration import (
    ConcentrationBreakdown,
    CurrencyExposure,
    PositionValue,
    country_concentration,
    currency_exposure,
    sector_concentration,
)
from investment_analyzer.portfolio.models import PortfolioPosition
from investment_analyzer.portfolio.position_sizing import PositionSizeBand, position_size_band
from investment_analyzer.portfolio.risk_metrics import (
    CorrelationResult,
    DrawdownResult,
    correlation_matrix,
    max_drawdown,
)


@dataclass(frozen=True)
class PortfolioPositionSnapshot:
    entity_id: str
    entity_name: str
    quantity: float
    currency: str
    latest_price: float | None
    market_value: float | None


@dataclass(frozen=True)
class PortfolioReport:
    generated_at: datetime
    positions: tuple[PortfolioPositionSnapshot, ...]
    total_market_value: float | None
    sector_concentration: ConcentrationBreakdown
    country_concentration: ConcentrationBreakdown
    currency_exposure: CurrencyExposure
    drawdowns: dict[str, DrawdownResult]
    correlations: dict[tuple[str, str], CorrelationResult]
    position_size_bands: dict[str, PositionSizeBand]
    assumptions: PortfolioAssumptions
    gaps: tuple[str, ...]


def build_portfolio_report(
    session: Session,
    profile: NutzerProfil,
    *,
    assumptions: PortfolioAssumptions | None = None,
) -> PortfolioReport:
    resolved_assumptions = assumptions or PortfolioAssumptions()
    gaps: list[str] = []

    rows = session.scalars(select(PortfolioPosition)).all()

    snapshots: list[PortfolioPositionSnapshot] = []
    concentration_values: list[PositionValue] = []
    price_series_by_entity: dict[str, list[tuple[date, float]]] = {}

    for row in rows:
        entity = session.get(Entity, row.entity_id)
        assert entity is not None  # Fremdschlüssel garantiert Existenz.

        latest = series.get_latest_value(session, entity, Metric.PRICE_CLOSE)
        latest_price = latest[1] if latest is not None else None
        market_value = latest_price * row.quantity if latest_price is not None else None

        snapshots.append(
            PortfolioPositionSnapshot(
                entity_id=entity.id,
                entity_name=entity.name,
                quantity=row.quantity,
                currency=row.currency,
                latest_price=latest_price,
                market_value=market_value,
            )
        )

        if market_value is not None:
            concentration_values.append(
                PositionValue(
                    entity_id=entity.id,
                    market_value=market_value,
                    currency=row.currency,
                    sector=entity.sic_description,
                    country=entity.country,
                )
            )
        else:
            gaps.append(
                f"Kein aktueller Kurs für {entity.name!r} bekannt — fließt nicht in "
                "Konzentrations-/Gesamtwertberechnung ein."
            )

        price_series_by_entity[entity.id] = series.get_series(session, entity, Metric.PRICE_CLOSE)

    sector_result = sector_concentration(concentration_values)
    country_result = country_concentration(concentration_values)
    currency_result = currency_exposure(concentration_values)

    total_market_value: float | None = None
    if sector_result.computable and concentration_values:
        total_market_value = sector_result.total_value
    elif not sector_result.computable:
        gaps.append(sector_result.note or "Gesamtmarktwert nicht berechenbar.")

    drawdowns = {
        entity_id: max_drawdown(price_series)
        for entity_id, price_series in price_series_by_entity.items()
    }
    correlations = correlation_matrix(price_series_by_entity)

    position_size_bands: dict[str, PositionSizeBand] = {}
    if total_market_value is not None and total_market_value > 0:
        for snapshot in snapshots:
            if snapshot.market_value is None:
                continue
            position_size_bands[snapshot.entity_id] = position_size_band(
                portfolio_value=total_market_value,
                max_position_pct=profile.positionsgroesse_max_prozent,
                current_position_value=snapshot.market_value,
                latest_price=snapshot.latest_price,
            )
    else:
        gaps.append(
            "Positionsgrößen-Bandbreiten nicht berechenbar: Gesamtmarktwert unbekannt "
            "(siehe vorherige Lücke)."
        )

    return PortfolioReport(
        generated_at=utc_now(),
        positions=tuple(snapshots),
        total_market_value=total_market_value,
        sector_concentration=sector_result,
        country_concentration=country_result,
        currency_exposure=currency_result,
        drawdowns=drawdowns,
        correlations=correlations,
        position_size_bands=position_size_bands,
        assumptions=resolved_assumptions,
        gaps=tuple(gaps),
    )
