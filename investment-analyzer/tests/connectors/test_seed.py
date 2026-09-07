from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'seed-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_ensure_default_sources_legt_alle_quellen_an(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        session.commit()

    assert set(sources) == {"sec_edgar", "alpha_vantage", "gdelt", "ir_rss"}
    assert sources["sec_edgar"].display_name == "SEC EDGAR"
    assert "Public Domain" in sources["sec_edgar"].license_note

    with session_factory() as session:
        alle = session.scalars(select(Source)).all()
    assert len(alle) == 4


def test_ensure_default_sources_ist_idempotent(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ensure_default_sources(session)
        session.commit()

    with session_factory() as session:
        ensure_default_sources(session)
        session.commit()

    with session_factory() as session:
        alle = session.scalars(select(Source)).all()
    assert len(alle) == 4  # keine Duplikate beim zweiten Aufruf


def test_ensure_default_sources_aktualisiert_bestehende_zeile(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        session.add(
            Source(
                key="sec_edgar",
                display_name="Alter Name",
                base_url="https://alt.invalid",
                license_note="alter Hinweis",
            )
        )
        session.commit()

    with session_factory() as session:
        sources = ensure_default_sources(session)
        session.commit()

    assert sources["sec_edgar"].display_name == "SEC EDGAR"
    assert sources["sec_edgar"].base_url == "https://data.sec.gov"
