from __future__ import annotations

from pathlib import Path

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, EntityIdentifier, IdentifierType
from investment_analyzer.ui.screener import list_entities


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'screener-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_list_entities_ohne_daten_ist_leer(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    assert list_entities(session_factory) == []


def test_list_entities_liefert_alphabetisch_sortiert(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        session.add_all([Entity(name="Zeta AG"), Entity(name="Alpha AG")])
        session.commit()

    names = [e.name for e in list_entities(session_factory)]
    assert names == ["Alpha AG", "Zeta AG"]


def test_list_entities_filtert_nach_suchtext_gross_klein_unabhaengig(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        session.add_all([Entity(name="Apple Inc."), Entity(name="Microsoft Corp")])
        session.commit()

    treffer = list_entities(session_factory, suchtext="apple")
    assert [e.name for e in treffer] == ["Apple Inc."]


def test_list_entities_laedt_identifiers_ohne_detached_instance_error(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = Entity(name="Firma X")
        session.add(entity)
        session.flush()
        session.add(EntityIdentifier(entity_id=entity.id, id_type=IdentifierType.CIK, id_value="0000000001"))
        session.commit()

    treffer = list_entities(session_factory)
    assert len(treffer) == 1
    # Zugriff außerhalb der ursprünglichen Session -- darf keinen
    # DetachedInstanceError auslösen (list_entities lädt die Identifier vorab).
    assert [i.id_value for i in treffer[0].identifiers] == ["0000000001"]
