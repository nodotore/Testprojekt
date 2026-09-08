from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from investment_analyzer.backtesting.report import build_backtest_report
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
    engine = create_db_engine(f"sqlite:///{tmp_path / 'backtesting-report-test.db'}")
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
    insert_full_fundamentals(session, firma_a, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT, include_dividends=False)
    insert_full_fundamentals(session, firma_b, sources["sec_edgar"], retrieved_at_utc=RETRIEVED_AT, include_dividends=False)

    for moment, price in ((JAN, 100.0), (FEB, 110.0), (MAR, 121.0)):
        session.add(make_datapoint(entity=firma_a, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=moment.date(), value=price, retrieved_at_utc=moment))
    for moment, price in ((JAN, 100.0), (FEB, 90.0), (MAR, 99.0)):
        session.add(make_datapoint(entity=firma_b, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=moment.date(), value=price, retrieved_at_utc=moment))

    session.commit()
    return firma_a, firma_b


def test_build_backtest_report_berechnet_gesamtrendite_und_cagr(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(
            session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS,
        )

    # Periode 1: (+10% + -10%)/2 = 0%; Periode 2: (+10% + +10%)/2 = +10%
    # Gesamtrendite: 1.0 * 1.10 - 1 = 0.10
    assert report.total_return == pytest.approx(0.10)
    assert report.cagr is not None
    assert report.years > 0


def test_build_backtest_report_dokumentiert_fehlenden_benchmark(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS)

    assert report.benchmark_total_return is None
    assert "benchmark_kursreihe" in report.gaps


def test_build_backtest_report_mit_benchmark_entfernt_die_luecke(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(
            session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS,
            benchmark_period_returns=[0.01, 0.02],
        )

    assert report.benchmark_total_return == pytest.approx(1.01 * 1.02 - 1)
    assert "benchmark_kursreihe" not in report.gaps


def test_build_backtest_report_max_drawdown_wird_wiederverwendet(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS)

    assert report.max_drawdown.computable is True


def test_build_backtest_report_hat_immer_survivorship_und_fx_luecken(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS)

    assert "waehrungsumrechnung" in report.gaps
    assert "vollstaendiges_survivorship_universum" in report.gaps


def test_build_backtest_report_durchschnittlicher_turnover(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        _setup_two_companies(session)
        report = build_backtest_report(session, [JAN, FEB, MAR], top_n=2, assumptions=NO_COST_ASSUMPTIONS)

    # Dieselben zwei Positionen in beiden Perioden -> Turnover 0.
    assert report.average_turnover == pytest.approx(0.0)
