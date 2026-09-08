"""Tests für das Point-in-time-Universum — Teil 1 des Auftrag-§9-
Abnahmekriteriums „dokumentierter Nachweis kein Look-ahead". Teil 2
(Ergebnis-Invarianz einer vollständigen Backtest-Auswahl gegenüber
später eintreffenden Daten) steht in ``tests/backtesting/test_engine.py``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.backtesting.universe import get_point_in_time_universe
from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'backtesting-universe-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(*, entity: Entity, source: Source, retrieved_at_utc: datetime) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=Metric.REVENUE.value,
        period_start=None,
        period_end=date(2023, 12, 31),
        published_at=date(2024, 1, 1),
        retrieved_at_utc=retrieved_at_utc,
        value_raw="100.0",
        value_normalized=100.0,
        unit="USD",
        currency="USD",
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/doc",
        document_type="10-K",
        content_hash=f"hash-{entity.id}-{retrieved_at_utc.isoformat()}",
        document_id=None,
    )


def test_universum_enthaelt_nur_zum_stichtag_bekannte_entities(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_a = find_or_create_entity(
            session, name="Firma A (früh bekannt)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        firma_b = find_or_create_entity(
            session, name="Firma B (erst später bekannt)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        session.add(_dp(entity=firma_a, source=sources["sec_edgar"], retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC)))
        session.add(_dp(entity=firma_b, source=sources["sec_edgar"], retrieved_at_utc=datetime(2024, 3, 15, tzinfo=UTC)))
        session.commit()

        universum_stichtag_februar = get_point_in_time_universe(session, datetime(2024, 2, 1, tzinfo=UTC))
        universum_stichtag_april = get_point_in_time_universe(session, datetime(2024, 4, 1, tzinfo=UTC))

    assert [e.name for e in universum_stichtag_februar] == ["Firma A (früh bekannt)"]
    assert {e.name for e in universum_stichtag_april} == {
        "Firma A (früh bekannt)", "Firma B (erst später bekannt)",
    }


def test_universum_ist_leer_ohne_jegliche_daten(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        find_or_create_entity(
            session, name="Firma ohne Datenpunkte",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000003")],
        )
        session.commit()
        universum = get_point_in_time_universe(session, datetime(2024, 6, 1, tzinfo=UTC))

    assert universum == []


def test_spaeter_eintreffende_daten_veraendern_frueheres_universum_nicht(tmp_path: Path) -> None:
    """Der eigentliche Look-ahead-Nachweis: Dasselbe ``as_of`` liefert vor
    UND nach dem Eintreffen von Firma Bs Daten exakt dasselbe Ergebnis —
    das spätere Bekanntwerden von Firma B kann ein früheres Ergebnis
    strukturell nicht beeinflussen (Auftrag §9)."""

    session_factory = _session_factory(tmp_path)
    stichtag = datetime(2024, 2, 1, tzinfo=UTC)

    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_a = find_or_create_entity(
            session, name="Firma A (früh bekannt)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        session.add(_dp(entity=firma_a, source=sources["sec_edgar"], retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC)))
        session.commit()

        universum_vorher = [e.name for e in get_point_in_time_universe(session, stichtag)]

    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_b = find_or_create_entity(
            session, name="Firma B (erst später bekannt)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        # Firma Bs Datenpunkt trifft NACH dem Stichtag ein.
        session.add(_dp(entity=firma_b, source=sources["sec_edgar"], retrieved_at_utc=datetime(2024, 3, 15, tzinfo=UTC)))
        session.commit()

        universum_nachher = [e.name for e in get_point_in_time_universe(session, stichtag)]

    assert universum_vorher == universum_nachher == ["Firma A (früh bekannt)"]
