"""Integrationstests für ``ReportBundle`` (Auftrag §10).

Synthetische, klar gekennzeichnete Beispieldaten — wie bei den bereits
bestehenden Integrationstests in ``tests/fundamentals``/``tests/valuation``/
``tests/scoring`` (kein Internetzugang in dieser Sandbox für echte
Marktdaten, siehe PROGRESS.md).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.reports.bundle import MANDATORY_DISCLAIMER, build_report_bundle
from investment_analyzer.scoring.score import compute_score

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'reports-bundle-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(
    *, entity: Entity, source: Source, metric: Metric, period_end: date, value: float,
    retrieved_at_utc: datetime = FETCHED_AT,
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
        content_hash="x" * 64,
        document_id=f"acc-{metric.value}-{period_end.isoformat()}",
    )


def _insert_firma_g(session, entity: Entity, source: Source) -> None:
    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
    for d, u in zip(jahre, umsatz, strict=True):
        session.add(_dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u))
        session.add(
            _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15)
        )
        session.add(_dp(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05))
        session.add(_dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.1))

    last = date(2023, 12, 31)
    for metric, value in (
        (Metric.OPERATING_INCOME, 180.0),
        (Metric.DEPRECIATION_AND_AMORTIZATION, 40.0),
        (Metric.TOTAL_EQUITY, 1000.0),
        (Metric.LONG_TERM_DEBT, 300.0),
        (Metric.SHORT_TERM_DEBT, 100.0),
        (Metric.CASH_AND_EQUIVALENTS, 200.0),
        (Metric.SHARES_DILUTED, 100.0),
        (Metric.EPS_DILUTED, 2.0),
        (Metric.INTEREST_EXPENSE, 20.0),
        (Metric.CURRENT_ASSETS, 500.0),
        (Metric.CURRENT_LIABILITIES, 250.0),
        (Metric.DIVIDENDS_PAID, 30.0),
        (Metric.GROSS_PROFIT, 500.0),
    ):
        session.add(_dp(entity=entity, source=source, metric=metric, period_end=last, value=value))

    session.add(
        _dp(
            entity=entity, source=source, metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0,
            retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
        )
    )


def test_build_report_bundle_liefert_konsistenten_header(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()
        _insert_firma_g(session, entity, sources["sec_edgar"])
        session.commit()

        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))

    assert bundle.header.entity_id == entity.id
    assert bundle.header.entity_name == entity.name
    assert bundle.header.data_completeness == bundle.fundamentals.data_completeness
    assert bundle.header.score_coverage == bundle.score.coverage
    assert bundle.header.score_classification == bundle.score.classification
    assert "Streaming" in bundle.header.market_data_delay_note


def test_build_report_bundle_enthaelt_pflichthinweis(tmp_path: Path) -> None:
    """Auftrag §12: der Hinweis muss an JEDER Berichtsausgabe sichtbar sein,
    nicht nur in der UI (siehe SECURITY.md, Milestone-8-Sicherheitsreview)."""

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000010")],
        )
        session.commit()

        bundle = build_report_bundle(session, entity)

    assert bundle.header.disclaimer == MANDATORY_DISCLAIMER
    assert "keine Anlageberatung" in bundle.header.disclaimer
    assert "Totalverlust" in bundle.header.disclaimer


def test_build_report_bundle_score_konsistent_mit_eigenstaendiger_berechnung(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()
        _insert_firma_g(session, entity, sources["sec_edgar"])
        session.commit()

        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        independent_score = compute_score(bundle.fundamentals, bundle.valuation)

    assert bundle.score.total_score == independent_score.total_score
    assert bundle.score.classification == independent_score.classification


def test_build_report_bundle_enthaelt_alle_registrierten_quellen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000008")],
        )
        session.commit()

        bundle = build_report_bundle(session, entity)

    keys = {s.key for s in bundle.sources}
    assert keys == {"sec_edgar", "alpha_vantage", "gdelt", "ir_rss"}


def test_build_report_bundle_sammelt_annahmen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()
        _insert_firma_g(session, entity, sources["sec_edgar"])
        session.commit()

        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))

    assert any("ROIC-Steuersatz" in note for note in bundle.assumptions)
    assert any("DCF-Szenario 'Basis'" in note for note in bundle.assumptions)


def test_build_report_bundle_ohne_jegliche_daten(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000009")],
        )
        session.commit()

        bundle = build_report_bundle(session, entity)

    assert bundle.fundamentals.data_completeness == 0.0
    assert bundle.score.classification == "Datenlage unzureichend"
    assert bundle.news.total_items == 0
