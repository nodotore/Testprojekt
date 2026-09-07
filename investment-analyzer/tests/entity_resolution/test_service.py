from __future__ import annotations

from pathlib import Path

import pytest

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import (
    IdentifierSpec,
    find_entity_by_identifier,
    find_or_create_entity,
)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'entity-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_ticker_allein_wird_abgelehnt(tmp_path: Path) -> None:
    with _session_factory(tmp_path)() as session, pytest.raises(ValueError, match="stabile Kennung"):
        find_or_create_entity(
            session,
            name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.TICKER, id_value="BSP")],
        )


def test_ohne_identifier_wird_abgelehnt(tmp_path: Path) -> None:
    with _session_factory(tmp_path)() as session, pytest.raises(ValueError):
        find_or_create_entity(session, name="Beispiel AG", identifiers=[])


def test_legt_neue_entity_mit_cik_und_ticker_an(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            country="US",
            primary_exchange="NASDAQ",
            identifiers=[
                IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193"),
                IdentifierSpec(id_type=IdentifierType.TICKER, id_value="AAPL", exchange="NASDAQ"),
            ],
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        geladen = session.get(Entity, entity_id)
        assert geladen is not None
        assert geladen.name == "Apple Inc."
        id_types = {i.id_type for i in geladen.identifiers}
        assert id_types == {IdentifierType.CIK, IdentifierType.TICKER}


def test_zweiter_aufruf_mit_gleicher_cik_findet_dieselbe_entity(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        erste = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.commit()
        erste_id = erste.id

    with session_factory() as session:
        zweite = find_or_create_entity(
            session,
            name="Apple Inc. (aktualisierter Name-Feed)",
            identifiers=[
                IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193"),
                IdentifierSpec(id_type=IdentifierType.ISIN, id_value="US0378331005"),
            ],
        )
        session.commit()
        assert zweite.id == erste_id

    with session_factory() as session:
        geladen = session.get(Entity, erste_id)
        assert geladen is not None
        id_values = {(i.id_type, i.id_value) for i in geladen.identifiers}
        assert (IdentifierType.CIK, "0000320193") in id_values
        assert (IdentifierType.ISIN, "US0378331005") in id_values
        # Der ursprüngliche Name bleibt erhalten — find_or_create_entity überschreibt
        # bei einem Treffer bewusst nicht den Namen (kein stiller Datenverlust).
        assert geladen.name == "Apple Inc."


def test_zwei_unternehmen_koennen_denselben_ticker_an_verschiedenen_boersen_haben(
    tmp_path: Path,
) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        a = find_or_create_entity(
            session,
            name="Firma A (US)",
            identifiers=[
                IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001"),
                IdentifierSpec(id_type=IdentifierType.TICKER, id_value="ABC", exchange="NASDAQ"),
            ],
        )
        b = find_or_create_entity(
            session,
            name="Firma B (DE)",
            identifiers=[
                IdentifierSpec(id_type=IdentifierType.ISIN, id_value="DE0000000002"),
                IdentifierSpec(id_type=IdentifierType.TICKER, id_value="ABC", exchange="XETRA"),
            ],
        )
        session.commit()

    assert a.id != b.id


def test_find_entity_by_identifier_liefert_none_wenn_unbekannt(tmp_path: Path) -> None:
    with _session_factory(tmp_path)() as session:
        assert find_entity_by_identifier(session, IdentifierType.ISIN, "US0000000000") is None
