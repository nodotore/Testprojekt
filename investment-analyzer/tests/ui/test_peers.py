from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.fundamentals.peers import find_peers
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.ui.peers import _vergleichstabelle

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'peers-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(entity, source, metric: Metric, period_end: date, value: float) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=metric.value,
        period_start=None,
        period_end=period_end,
        published_at=period_end,
        retrieved_at_utc=FETCHED_AT,
        value_raw=str(value),
        value_normalized=value,
        unit="USD",
        currency="USD",
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/doc",
        document_type="10-K",
        content_hash="x" * 64,
        document_id=f"acc-{entity.id}-{metric.value}-{period_end.isoformat()}",
    )


def _seed_firma_mit_daten(session, source, name: str, cik: str, sic_code: str) -> None:
    entity = find_or_create_entity(
        session, name=name, identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value=cik)]
    )
    entity.sic_code = sic_code
    session.flush()

    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
    for jahr, u in zip(jahre, umsatz, strict=True):
        session.add(_dp(entity, source, Metric.REVENUE, jahr, u))
        session.add(_dp(entity, source, Metric.OPERATING_CASH_FLOW, jahr, u * 0.15))
        session.add(_dp(entity, source, Metric.CAPEX, jahr, -u * 0.05))
        session.add(_dp(entity, source, Metric.NET_INCOME, jahr, u * 0.1))

    letztes_jahr = date(2023, 12, 31)
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
        session.add(_dp(entity, source, metric, letztes_jahr, value))
    session.add(_dp(entity, source, Metric.PRICE_CLOSE, date(2024, 1, 15), 20.0))
    return entity


def test_find_peers_findet_nur_gleichen_sic_code(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = _seed_firma_mit_daten(session, sources["sec_edgar"], "Firma G", "0000000007", "7372")
        _seed_firma_mit_daten(session, sources["sec_edgar"], "Firma H (Peer)", "0000000008", "7372")
        _seed_firma_mit_daten(session, sources["sec_edgar"], "Firma I (andere Branche)", "0000000009", "1000")
        session.commit()

        peers = find_peers(session, entity)
        assert [p.name for p in peers] == ["Firma H (Peer)"]


def test_vergleichstabelle_enthaelt_ausgewaehltes_unternehmen_und_peers(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = _seed_firma_mit_daten(session, sources["sec_edgar"], "Firma G", "0000000007", "7372")
        _seed_firma_mit_daten(session, sources["sec_edgar"], "Firma H (Peer)", "0000000008", "7372")
        session.commit()

        peers = find_peers(session, entity)
        df = _vergleichstabelle(session, entity, peers)

    assert len(df) == 2
    assert df.loc[0, "Unternehmen"] == "Firma G (ausgewählt)"
    assert df.loc[1, "Unternehmen"] == "Firma H (Peer)"
    assert df.loc[0, "Score (0–100)"] > 0
    assert df.loc[1, "Score (0–100)"] > 0
