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
from investment_analyzer.risk.warning_signals import (
    check_cashflow_divergence,
    check_high_stock_based_compensation,
    check_late_filing,
    check_strong_dilution,
    check_unusual_inventory_growth,
    check_unusual_receivables_growth,
    run_all_checks,
)

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'warnsignale-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(
    *,
    entity: Entity,
    source: Source,
    metric: Metric,
    period_end: date,
    value: float,
    published_at: date | None = None,
    retrieved_at_utc: datetime = FETCHED_AT,
) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=metric.value,
        period_start=None,
        period_end=period_end,
        published_at=published_at or period_end,
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


def _setup_entity(tmp_path: Path):
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        entity_id = entity.id
        source = sources["sec_edgar"]
        session.commit()
    return session_factory, entity_id, source


def test_cashflow_divergence_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2023, 12, 31), value=120.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2022, 12, 31), value=150.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2023, 12, 31), value=100.0),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_cashflow_divergence(session, entity)

    assert signal is not None
    assert signal.code == "cashflow_divergence"
    assert "steigendem Nettogewinn" in signal.description


def test_cashflow_divergence_ohne_divergenz_liefert_none(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2023, 12, 31), value=120.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2023, 12, 31), value=130.0),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert check_cashflow_divergence(session, entity) is None


def test_cashflow_divergence_ohne_daten_liefert_none(tmp_path: Path) -> None:
    session_factory, entity_id, _source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert check_cashflow_divergence(session, entity) is None


def test_strong_dilution_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        # 1,157625 = 1,05^3 -> 5 %/Jahr Verwässerung über 3 Jahre (Schwelle 3 %)
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=1157.625),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_strong_dilution(session, entity)

    assert signal is not None
    assert signal.code == "strong_dilution"


def test_strong_dilution_unterhalb_schwelle_liefert_none(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        # 1 % p.a. -> unterhalb der 3 %-Schwelle
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=1030.301),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert check_strong_dilution(session, entity) is None


def test_high_stock_based_compensation_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        # 60 / 1000 = 6 % > Schwelle 5 %
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.STOCK_BASED_COMPENSATION, period_end=date(2023, 12, 31), value=60.0),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_high_stock_based_compensation(session, entity)

    assert signal is not None
    assert signal.code == "high_stock_based_compensation"


def test_unusual_receivables_growth_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2022, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1050.0),  # +5 %
                _dp(entity=entity, source=source, metric=Metric.ACCOUNTS_RECEIVABLE, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.ACCOUNTS_RECEIVABLE, period_end=date(2023, 12, 31), value=140.0),  # +40 %
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_unusual_receivables_growth(session, entity)

    assert signal is not None
    assert signal.code == "unusual_receivables_growth"


def test_unusual_inventory_growth_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2022, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1020.0),  # +2 %
                _dp(entity=entity, source=source, metric=Metric.INVENTORY, period_end=date(2022, 12, 31), value=200.0),
                _dp(entity=entity, source=source, metric=Metric.INVENTORY, period_end=date(2023, 12, 31), value=260.0),  # +30 %
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_unusual_inventory_growth(session, entity)

    assert signal is not None
    assert signal.code == "unusual_inventory_growth"


def test_late_filing_wird_erkannt(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add(
            _dp(
                entity=entity, source=source, metric=Metric.REVENUE,
                period_end=date(2023, 12, 31), value=1000.0,
                published_at=date(2024, 6, 1),  # 183 Tage nach Periodenende
            )
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signal = check_late_filing(session, entity)

    assert signal is not None
    assert signal.code == "late_filing"


def test_late_filing_bei_normaler_frist_liefert_none(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add(
            _dp(
                entity=entity, source=source, metric=Metric.REVENUE,
                period_end=date(2023, 12, 31), value=1000.0,
                published_at=date(2024, 2, 15),  # 46 Tage — üblich
            )
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert check_late_filing(session, entity) is None


def test_run_all_checks_ohne_auffaelligkeiten_ist_leer(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1000.0, published_at=date(2024, 2, 1)),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert run_all_checks(session, entity) == []


def test_run_all_checks_sammelt_mehrere_signale(tmp_path: Path) -> None:
    session_factory, entity_id, source = _setup_entity(tmp_path)
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add_all(
            [
                # Cashflow-Divergenz
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2023, 12, 31), value=120.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2022, 12, 31), value=150.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2023, 12, 31), value=100.0),
                # Starke Verwässerung
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=1157.625),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        signale = run_all_checks(session, entity)

    codes = {s.code for s in signale}
    assert codes == {"cashflow_divergence", "strong_dilution"}


def test_run_all_checks_ignoriert_zum_stichtag_noch_unbekannte_daten(tmp_path: Path) -> None:
    """Regressionstest für einen vom unabhängigen Milestone-8-Review gefundenen
    Look-ahead-Bias (siehe DECISIONS.md ADR-25): ``run_all_checks`` (und jeder
    einzelne Check) muss ``as_of`` konsequent durchreichen. Vorher griff jeder
    Check ohne ``as_of``-Parameter intern auf den AKTUELLEN Zeitpunkt zurück
    (``series.get_*``-Default), sodass ein Warnsignal-Ausschlag von einem
    Datenpunkt abhing, der zum eigentlichen Analysestichtag noch gar nicht
    bekannt war -- genau das Szenario, das Auftrag §9 (kein Look-ahead)
    verbietet, hier aber nicht über eine neue Entity (wie im bereits
    bestehenden Backtest-Test), sondern über eine SPÄTER eintreffende
    Zeile für eine bereits bekannte Entity."""

    session_factory, entity_id, source = _setup_entity(tmp_path)
    stichtag = datetime(2024, 3, 1, tzinfo=UTC)

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        # Zum Stichtag bereits bekannt: unauffällige Verwässerung (1 %/Jahr).
        session.add_all(
            [
                _dp(
                    entity=entity, source=source, metric=Metric.SHARES_DILUTED,
                    period_end=date(2020, 12, 31), value=1000.0, retrieved_at_utc=FETCHED_AT,
                ),
                _dp(
                    entity=entity, source=source, metric=Metric.SHARES_DILUTED,
                    period_end=date(2023, 12, 31), value=1030.301, retrieved_at_utc=FETCHED_AT,
                ),
            ]
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        vor_restatement = run_all_checks(session, entity, as_of=stichtag)

    assert vor_restatement == []  # unauffällig -- unterhalb der Verwässerungsschwelle

    # Erst NACH dem Analysestichtag trifft eine Korrektur ein (z. B. 10-K/A),
    # die dieselbe Periode auf eine starke Verwässerung revidiert.
    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        session.add(
            _dp(
                entity=entity, source=source, metric=Metric.SHARES_DILUTED,
                period_end=date(2023, 12, 31), value=1157.625,
                retrieved_at_utc=datetime(2024, 6, 1, tzinfo=UTC),
            )
        )
        session.commit()

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        nach_restatement_alter_stichtag = run_all_checks(session, entity, as_of=stichtag)
        nach_restatement_neuer_stichtag = run_all_checks(session, entity, as_of=datetime(2024, 7, 1, tzinfo=UTC))

    # Derselbe (frühere) Stichtag liefert weiterhin dasselbe Ergebnis --
    # die später eingetroffene Korrektur darf ihn nicht rückwirkend verändern.
    assert nach_restatement_alter_stichtag == vor_restatement == []
    # Zu einem Stichtag NACH der Korrektur ist das Signal dagegen sichtbar.
    assert {s.code for s in nach_restatement_neuer_stichtag} == {"strong_dilution"}
