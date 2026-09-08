"""Tests für die Rebalancing-Engine — inkl. Teil 2 des Auftrag-§9-
Abnahmekriteriums „dokumentierter Nachweis kein Look-ahead" (Teil 1
in ``tests/backtesting/test_universe.py``): ein vollständiger
Backtest-Lauf bis zu einem Stichtag liefert exakt dasselbe Ergebnis,
bevor und nachdem ein erst später bekannt gewordener Kandidat in die
Datenbank aufgenommen wurde.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from investment_analyzer.backtesting.engine import run_backtest
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.portfolio.assumptions import PortfolioAssumptions

from ._fixtures import insert_full_fundamentals, make_datapoint

RETRIEVED_AT = datetime(2024, 1, 1, tzinfo=UTC)
JAN = datetime(2024, 1, 15, tzinfo=UTC)
FEB = datetime(2024, 2, 15, tzinfo=UTC)
MAR = datetime(2024, 3, 15, tzinfo=UTC)
NO_COST_ASSUMPTIONS = PortfolioAssumptions(transaction_cost_pct=0.0)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'backtesting-engine-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _setup_two_companies(session):
    sources = ensure_default_sources(session)
    firma_a = find_or_create_entity(
        session, name="Firma A",
        identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
    )
    firma_b = find_or_create_entity(
        session, name="Firma B",
        identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
    )
    session.flush()
    # include_dividends=False, damit die Perioden-Rendite exakt der reinen
    # Kursänderung entspricht (von Hand nachrechenbar, siehe Testfälle unten).
    insert_full_fundamentals(session, firma_a, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT, include_dividends=False)
    insert_full_fundamentals(session, firma_b, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT, include_dividends=False)

    # Firma A: 100 -> 110 (+10 %) -> 121 (+10 %)
    for moment, price in ((JAN, 100.0), (FEB, 110.0), (MAR, 121.0)):
        session.add(make_datapoint(entity=firma_a, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=moment.date(), value=price, retrieved_at_utc=moment))
    # Firma B: 50 -> 45 (-10 %) -> 49.5 (+10 %)
    for moment, price in ((JAN, 50.0), (FEB, 45.0), (MAR, 49.5)):
        session.add(make_datapoint(entity=firma_b, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=moment.date(), value=price, retrieved_at_utc=moment))

    session.commit()
    return firma_a, firma_b


def test_run_backtest_berechnet_gleichgewichtete_portfoliorendite_exakt(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        firma_a, firma_b = _setup_two_companies(session)

        run = run_backtest(
            session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS,
        )

    assert len(run.periods) == 2
    # Periode 1 (Jan->Feb): (+10 % + -10 %) / 2 = 0 %
    assert run.periods[0].portfolio_return == pytest.approx(0.0)
    # Periode 2 (Feb->Mar): (+10 % + +10 %) / 2 = +10 %
    assert run.periods[1].portfolio_return == pytest.approx(0.10)

    assert run.nav_series[0] == (JAN, 1.0)
    assert run.nav_series[1][1] == pytest.approx(1.0)
    assert run.nav_series[2][1] == pytest.approx(1.10)

    assert set(run.periods[0].holdings) == {firma_a.id, firma_b.id}


def test_run_backtest_schliesst_positionen_ohne_kurs_aus(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_a = find_or_create_entity(
            session, name="Firma A",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        insert_full_fundamentals(session, firma_a, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT)
        # Kein einziger Kurspunkt -- Rendite für diese Position ist mangels
        # Kursdaten nicht berechenbar (weder Start- noch Endkurs bekannt).
        session.commit()

        run = run_backtest(session, [JAN, FEB], top_n=1, assumptions=NO_COST_ASSUMPTIONS)

    assert run.periods[0].portfolio_return is None
    assert run.periods[0].excluded_holdings == (firma_a.id,)
    assert run.nav_series[-1][1] == pytest.approx(1.0)  # unveränderter NAV mangels Rendite


def test_run_backtest_zu_wenig_stichtage(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session, pytest.raises(ValueError, match="mindestens zwei"):
        run_backtest(session, [JAN], top_n=1)


def test_run_backtest_unsortierte_stichtage(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session, pytest.raises(ValueError, match="aufsteigend sortiert"):
        run_backtest(session, [FEB, JAN], top_n=1)


def test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_backtest_ergebnis_nicht(
    tmp_path: Path,
) -> None:
    """Der zentrale Auftrag-§9-Nachweis auf Ebene der vollständigen Engine:
    ein Backtest bis Februar liefert VOR und NACH dem Eintreffen von
    Firma Cs (erst im März bekannt gewordenen) Daten exakt dasselbe
    Ergebnis — ein späterer Kandidat kann ein früheres Ergebnis
    strukturell nicht beeinflussen."""

    session_factory = _session_factory(tmp_path)

    with session_factory() as session:
        _setup_two_companies(session)
        lauf_vorher = run_backtest(session, [JAN, FEB], top_n=5, assumptions=NO_COST_ASSUMPTIONS)

    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_c = find_or_create_entity(
            session, name="Firma C (erst im März bekannt)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000003")],
        )
        session.flush()
        insert_full_fundamentals(session, firma_c, sources["sec_edgar"], retrieved_at_utc=MAR)
        session.add(make_datapoint(entity=firma_c, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=MAR.date(), value=1000.0, retrieved_at_utc=MAR))
        session.commit()

        lauf_nachher = run_backtest(session, [JAN, FEB], top_n=5, assumptions=NO_COST_ASSUMPTIONS)

    assert lauf_vorher.periods[0].holdings == lauf_nachher.periods[0].holdings
    assert lauf_vorher.periods[0].portfolio_return == lauf_nachher.periods[0].portfolio_return
    assert lauf_vorher.nav_series == lauf_nachher.nav_series
    assert firma_c.id not in lauf_nachher.periods[0].holdings
