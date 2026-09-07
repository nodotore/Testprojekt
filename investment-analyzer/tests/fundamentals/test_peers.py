from __future__ import annotations

from pathlib import Path

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.peers import find_peers


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'peers-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_find_peers_ohne_sic_liefert_leere_liste(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma ohne Branche",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert find_peers(session, entity) == []


def test_find_peers_findet_gleiche_branche(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        apple = find_or_create_entity(
            session, name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        apple.sic_code = "3571"
        apple.sic_description = "Electronic Computers"

        dell = find_or_create_entity(
            session, name="Dell Technologies",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000826083")],
        )
        dell.sic_code = "3571"

        pharma = find_or_create_entity(
            session, name="Beispiel Pharma AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000042")],
        )
        pharma.sic_code = "2834"

        session.commit()
        apple_id = apple.id

    with session_factory() as session:
        apple = session.get(Entity, apple_id)
        assert apple is not None
        peers = find_peers(session, apple)

    assert [p.name for p in peers] == ["Dell Technologies"]


def test_find_peers_respektiert_limit(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ziel = find_or_create_entity(
            session, name="Ziel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        ziel.sic_code = "1000"
        for i in range(5):
            peer = find_or_create_entity(
                session, name=f"Peer {i}",
                identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value=f"000000{10 + i}")],
            )
            peer.sic_code = "1000"
        session.commit()
        ziel_id = ziel.id

    with session_factory() as session:
        ziel = session.get(Entity, ziel_id)
        assert ziel is not None
        peers = find_peers(session, ziel, limit=3)

    assert len(peers) == 3


def test_find_peers_schliesst_sich_selbst_aus(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        solo = find_or_create_entity(
            session, name="Solo AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        solo.sic_code = "9999"
        session.commit()
        solo_id = solo.id

    with session_factory() as session:
        solo = session.get(Entity, solo_id)
        assert solo is not None
        assert find_peers(session, solo) == []
