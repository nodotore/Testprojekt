from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.portfolio.models import PortfolioPosition
from investment_analyzer.portfolio.report import build_portfolio_report


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'portfolio-report-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _price_point(
    *, entity: Entity, source: Source, day: date, value: float
) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=Metric.PRICE_CLOSE.value,
        period_start=None,
        period_end=day,
        published_at=day,
        retrieved_at_utc=datetime.combine(day, datetime.min.time(), tzinfo=UTC),
        value_raw=str(value),
        value_normalized=value,
        unit="price_per_share",
        currency=None,
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/quote",
        document_type="market_data_snapshot",
        content_hash=f"hash-{entity.id}-{day.isoformat()}",
        document_id=None,
    )


def test_build_portfolio_report_ohne_positionen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        report = build_portfolio_report(session, NutzerProfil())

    assert report.positions == ()
    assert report.total_market_value is None
    assert report.sector_concentration.computable is True
    assert report.sector_concentration.by_key == {}


def test_build_portfolio_report_mit_einer_position_und_kurs(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        entity.sic_description = "Software"
        entity.country = "US"
        session.flush()

        session.add(PortfolioPosition(entity_id=entity.id, quantity=10.0, currency="EUR"))
        session.add(_price_point(entity=entity, source=sources["alpha_vantage"], day=date(2026, 3, 1), value=50.0))
        session.commit()

        report = build_portfolio_report(session, NutzerProfil())

    assert len(report.positions) == 1
    position = report.positions[0]
    assert position.latest_price == 50.0
    assert position.market_value == 500.0
    assert report.total_market_value == 500.0
    assert report.sector_concentration.by_key == {"Software": 1.0}
    assert report.country_concentration.by_key == {"US": 1.0}
    assert report.currency_exposure.value_by_currency == {"EUR": 500.0}


def test_build_portfolio_report_ohne_kurs_dokumentiert_luecke(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma Ohne Kurs", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000002")]
        )
        session.flush()
        session.add(PortfolioPosition(entity_id=entity.id, quantity=5.0, currency="EUR"))
        session.commit()

        report = build_portfolio_report(session, NutzerProfil())

    assert report.positions[0].market_value is None
    assert report.total_market_value is None
    assert any("Kurs" in gap for gap in report.gaps)


def test_build_portfolio_report_berechnet_positionsgroessen_bandbreite(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(PortfolioPosition(entity_id=entity.id, quantity=10.0, currency="EUR"))
        session.add(_price_point(entity=entity, source=sources["alpha_vantage"], day=date(2026, 3, 1), value=50.0))
        session.commit()

        profile = NutzerProfil(positionsgroesse_max_prozent=10.0)
        report = build_portfolio_report(session, profile)

    band = report.position_size_bands[entity.id]
    # Gesamtwert = 500, 10% Limit = 50 -> bereits ueber dem Limit (500 > 50)
    assert band.max_position_value == 50.0
    assert band.max_additional_value == 0.0


def test_build_portfolio_report_drawdown_ueber_mehrere_kurspunkte(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(PortfolioPosition(entity_id=entity.id, quantity=1.0, currency="EUR"))
        session.add(_price_point(entity=entity, source=sources["alpha_vantage"], day=date(2026, 1, 1), value=100.0))
        session.add(_price_point(entity=entity, source=sources["alpha_vantage"], day=date(2026, 1, 2), value=80.0))
        session.commit()

        report = build_portfolio_report(session, NutzerProfil())

    drawdown = report.drawdowns[entity.id]
    assert drawdown.computable is True
    assert drawdown.max_drawdown_pct == -0.2


def test_build_portfolio_report_gemischte_waehrungen_dokumentiert_luecke(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity_a = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        entity_b = find_or_create_entity(
            session, name="Firma F", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000002")]
        )
        session.flush()
        session.add(PortfolioPosition(entity_id=entity_a.id, quantity=1.0, currency="EUR"))
        session.add(PortfolioPosition(entity_id=entity_b.id, quantity=1.0, currency="USD"))
        session.add(_price_point(entity=entity_a, source=sources["alpha_vantage"], day=date(2026, 3, 1), value=50.0))
        session.add(_price_point(entity=entity_b, source=sources["alpha_vantage"], day=date(2026, 3, 1), value=50.0))
        session.commit()

        report = build_portfolio_report(session, NutzerProfil())

    assert report.sector_concentration.computable is False
    assert report.total_market_value is None
    assert report.position_size_bands == {}
    assert len(report.gaps) >= 2
