from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from investment_analyzer.backtesting.strategy import select_top_n
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric

from ._fixtures import insert_full_fundamentals, insert_weak_fundamentals, make_datapoint

RETRIEVED_AT = datetime(2024, 1, 1, tzinfo=UTC)
STICHTAG = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'backtesting-strategy-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_select_top_n_bevorzugt_die_staerkere_firma(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        stark = find_or_create_entity(
            session, name="Firma Stark",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        schwach = find_or_create_entity(
            session, name="Firma Schwach",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        insert_full_fundamentals(session, stark, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT)
        insert_weak_fundamentals(session, schwach, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT)
        session.add(make_datapoint(entity=stark, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0, retrieved_at_utc=RETRIEVED_AT))
        session.add(make_datapoint(entity=schwach, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0, retrieved_at_utc=RETRIEVED_AT))
        session.commit()

        top1 = select_top_n(session, as_of=STICHTAG, n=1)
        top2 = select_top_n(session, as_of=STICHTAG, n=2)

    assert top1 == [stark.id]
    assert set(top2) == {stark.id, schwach.id}


def test_select_top_n_schliesst_nicht_berechenbare_kandidaten_aus(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        vollstaendig = find_or_create_entity(
            session, name="Firma mit vollen Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        nur_kurs = find_or_create_entity(
            session, name="Firma nur mit Kurs",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        insert_full_fundamentals(session, vollstaendig, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT)
        session.add(make_datapoint(entity=vollstaendig, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0, retrieved_at_utc=RETRIEVED_AT))
        # "nur_kurs" hat NUR einen Kurspunkt -- ist im Punkt-in-Zeit-Universum,
        # aber mangels Fundamentaldaten nicht scorebar.
        session.add(make_datapoint(entity=nur_kurs, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0, retrieved_at_utc=RETRIEVED_AT))
        session.commit()

        result = select_top_n(session, as_of=STICHTAG, n=5)

    assert result == [vollstaendig.id]


def test_select_top_n_ist_deterministisch(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma = find_or_create_entity(
            session, name="Firma",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        insert_full_fundamentals(session, firma, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT)
        session.add(make_datapoint(entity=firma, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15), value=20.0, retrieved_at_utc=RETRIEVED_AT))
        session.commit()

        erster_lauf = select_top_n(session, as_of=STICHTAG, n=3)
        zweiter_lauf = select_top_n(session, as_of=STICHTAG, n=3)

    assert erster_lauf == zweiter_lauf


def test_select_top_n_ungueltiges_n(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session, pytest.raises(ValueError, match="n muss"):
        select_top_n(session, as_of=STICHTAG, n=0)
