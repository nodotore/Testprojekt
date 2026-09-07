from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.portfolio.models import PortfolioPosition, WatchlistEntry


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'portfolio-model-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_watchlist_entry_kann_gespeichert_werden(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(WatchlistEntry(entity_id=entity.id, note="Beobachten wegen Turnaround"))
        session.commit()

    with session_factory() as session:
        rows = session.scalars(select(WatchlistEntry)).all()
    assert len(rows) == 1
    assert rows[0].note == "Beobachten wegen Turnaround"


def test_watchlist_entry_pro_entity_nur_einmal(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(WatchlistEntry(entity_id=entity.id))
        session.commit()

        session.add(WatchlistEntry(entity_id=entity.id))
        with pytest.raises(IntegrityError):
            session.commit()


def test_portfolio_position_kann_gespeichert_werden(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(
            PortfolioPosition(
                entity_id=entity.id, quantity=10.0, average_cost=42.5, currency="EUR"
            )
        )
        session.commit()

    with session_factory() as session:
        rows = session.scalars(select(PortfolioPosition)).all()
    assert len(rows) == 1
    assert rows[0].quantity == 10.0
    assert rows[0].currency == "EUR"


def test_portfolio_position_pro_entity_nur_einmal(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        session.add(PortfolioPosition(entity_id=entity.id, quantity=1.0, currency="EUR"))
        session.commit()

        session.add(PortfolioPosition(entity_id=entity.id, quantity=2.0, currency="EUR"))
        with pytest.raises(IntegrityError):
            session.commit()
