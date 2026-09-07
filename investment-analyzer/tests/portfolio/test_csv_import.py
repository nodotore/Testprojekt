from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.portfolio.csv_import import import_portfolio_csv, import_watchlist_csv
from investment_analyzer.portfolio.models import PortfolioPosition, WatchlistEntry


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'portfolio-csv-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


WATCHLIST_CSV = """id_type,id_value,name,note
isin,DE0001234567,Firma E,Turnaround-Kandidat
cik,0000000002,Firma F,
"""

PORTFOLIO_CSV = """id_type,id_value,name,quantity,average_cost,currency,note
isin,DE0001234567,Firma E,10,42.50,EUR,Kernposition
cik,0000000002,Firma F,5,,USD,
"""


def test_import_watchlist_csv_legt_eintraege_an(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_watchlist_csv(session, WATCHLIST_CSV)
        session.commit()

    assert result.created == 2
    assert result.updated == 0
    assert result.errors == ()

    with session_factory() as session:
        rows = session.scalars(select(WatchlistEntry)).all()
    assert len(rows) == 2


def test_import_watchlist_csv_ist_idempotent_und_aktualisiert(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        import_watchlist_csv(session, WATCHLIST_CSV)
        session.commit()

    updated_csv = WATCHLIST_CSV.replace("Turnaround-Kandidat", "Neue Notiz")
    with session_factory() as session:
        result = import_watchlist_csv(session, updated_csv)
        session.commit()

    assert result.created == 0
    assert result.updated == 2

    with session_factory() as session:
        rows = session.scalars(select(WatchlistEntry)).all()
    assert len(rows) == 2
    assert any(row.note == "Neue Notiz" for row in rows)


def test_import_watchlist_csv_fehlende_kopfzeile(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_watchlist_csv(session, "id_type,name\nisin,Firma X\n")

    assert result.created == 0
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 1
    assert "Kopfzeile" in result.errors[0].message


def test_import_watchlist_csv_meldet_fehlerhafte_zeilen(tmp_path: Path) -> None:
    csv_text = "id_type,id_value,name,note\nticker,IBM,IBM Corp,\nisin,,Ohne Wert,\n"
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_watchlist_csv(session, csv_text)
        session.commit()

    assert result.created == 0
    assert len(result.errors) == 2
    assert result.errors[0].row_number == 2
    assert "id_type" in result.errors[0].message
    assert result.errors[1].row_number == 3
    assert "id_value" in result.errors[1].message


def test_import_portfolio_csv_legt_positionen_an(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_portfolio_csv(session, PORTFOLIO_CSV)
        session.commit()

    assert result.created == 2
    assert result.errors == ()

    with session_factory() as session:
        rows = {row.currency: row for row in session.scalars(select(PortfolioPosition)).all()}
    assert rows["EUR"].quantity == 10.0
    assert rows["EUR"].average_cost == 42.5
    assert rows["USD"].average_cost is None


def test_import_portfolio_csv_ist_idempotent_und_aktualisiert(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        import_portfolio_csv(session, PORTFOLIO_CSV)
        session.commit()

    updated_csv = PORTFOLIO_CSV.replace("10,42.50", "20,45.00")
    with session_factory() as session:
        result = import_portfolio_csv(session, updated_csv)
        session.commit()

    assert result.created == 0
    assert result.updated == 2

    with session_factory() as session:
        rows = {row.currency: row for row in session.scalars(select(PortfolioPosition)).all()}
    assert rows["EUR"].quantity == 20.0
    assert rows["EUR"].average_cost == 45.0


def test_import_portfolio_csv_meldet_ungueltige_quantity(tmp_path: Path) -> None:
    csv_text = "id_type,id_value,name,quantity,average_cost,currency,note\nisin,DE1,Firma X,nicht-numerisch,,EUR,\n"
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_portfolio_csv(session, csv_text)
        session.commit()

    assert result.created == 0
    assert len(result.errors) == 1
    assert "quantity" in result.errors[0].message


def test_import_portfolio_csv_meldet_negative_quantity(tmp_path: Path) -> None:
    csv_text = "id_type,id_value,name,quantity,average_cost,currency,note\nisin,DE1,Firma X,-5,,EUR,\n"
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_portfolio_csv(session, csv_text)
        session.commit()

    assert result.created == 0
    assert "quantity" in result.errors[0].message


def test_import_portfolio_csv_meldet_ungueltige_currency(tmp_path: Path) -> None:
    csv_text = "id_type,id_value,name,quantity,average_cost,currency,note\nisin,DE1,Firma X,5,,EURO,\n"
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_portfolio_csv(session, csv_text)
        session.commit()

    assert result.created == 0
    assert "currency" in result.errors[0].message


def test_import_portfolio_csv_fehlende_pflichtspalten(tmp_path: Path) -> None:
    csv_text = "id_type,id_value,name\nisin,DE1,Firma X\n"
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        result = import_portfolio_csv(session, csv_text)

    assert result.created == 0
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 1
