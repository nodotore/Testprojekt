"""Integrationstests für ``ValuationReport`` (Auftrag §15).

Wie bei ``tests/fundamentals/test_report.py``: synthetische, klar
gekennzeichnete Beispieldaten (kein Internetzugang in dieser Sandbox
für echte Marktdaten, siehe PROGRESS.md/NEXT_STEPS.md). Die Kern-DCF-
Arithmetik ist bereits in ``tests/valuation/test_dcf.py`` exakt von
Hand nachgerechnet; hier wird zusätzlich geprüft, dass die
Standardszenarien korrekt aus der historischen Umsatz-/Cashflow-Serie
abgeleitet werden und dass Multiples/Sicherheitsmarge/Peer-Vergleich
konsistent ineinandergreifen.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.valuation.dcf import safety_margin
from investment_analyzer.valuation.report import (
    DEFAULT_TERMINAL_GROWTH_RATE,
    DEFAULT_WACC,
    build_valuation_report,
)

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'valuation-report-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(
    *,
    entity: Entity,
    source: Source,
    metric: Metric,
    period_end: date,
    value: float,
    published_at: date | None = None,
    retrieved_at_utc: datetime = FETCHED_AT,
) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=metric.value,
        period_start=None,
        period_end=period_end,
        published_at=published_at or period_end,
        retrieved_at_utc=retrieved_at_utc,
        value_raw=str(value),
        value_normalized=value,
        unit="USD",
        currency="USD",
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/doc",
        document_type="10-K",
        content_hash="x" * 64,
        document_id=f"acc-{metric.value}-{period_end.isoformat()}",
    )


def _insert_firma_e(session, entity: Entity, source: Source) -> None:
    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [1000.0, 1100.0, 1210.0, 1331.0]  # exakt 10 %/Jahr
    for d, u in zip(jahre, umsatz, strict=True):
        session.add(_dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u))
        session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15))
        session.add(_dp(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05))

    session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_INCOME, period_end=date(2023, 12, 31), value=180.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.DEPRECIATION_AND_AMORTIZATION, period_end=date(2023, 12, 31), value=40.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2023, 12, 31), value=1000.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.LONG_TERM_DEBT, period_end=date(2023, 12, 31), value=300.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.SHORT_TERM_DEBT, period_end=date(2023, 12, 31), value=100.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.CASH_AND_EQUIVALENTS, period_end=date(2023, 12, 31), value=200.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=100.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.EPS_DILUTED, period_end=date(2023, 12, 31), value=2.0))
    session.add(
        _dp(
            entity=entity, source=source, metric=Metric.PRICE_CLOSE,
            period_end=date(2024, 1, 15), value=20.0,
            retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
        )
    )


def test_valuation_report_firma_e_vollstaendige_daten(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_e = find_or_create_entity(
            session, name="Firma E (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000005")],
        )
        firma_e.sic_code = "3571"
        firma_f = find_or_create_entity(
            session, name="Firma F (Branchenkollege, ohne Daten)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000006")],
        )
        firma_f.sic_code = "3571"
        session.flush()
        _insert_firma_e(session, firma_e, sources["sec_edgar"])
        session.commit()
        firma_e_id = firma_e.id

    with session_factory() as session:
        firma_e = session.get(Entity, firma_e_id)
        assert firma_e is not None
        report = build_valuation_report(session, firma_e)

    # --- Multiples (Handrechnung) ---
    assert report.multiples.price_per_share == pytest.approx(20.0)
    assert report.multiples.market_cap == pytest.approx(2000.0)  # 20 * 100
    assert report.multiples.enterprise_value == pytest.approx(2200.0)  # 2000 + 400 - 200
    assert report.multiples.price_earnings_ratio == pytest.approx(10.0)  # 20 / 2,0
    assert report.multiples.ev_to_ebitda == pytest.approx(10.0)  # 2200 / (180+40)
    assert report.multiples.ev_to_ebit == pytest.approx(2200.0 / 180.0)
    assert report.multiples.price_to_book == pytest.approx(2.0)  # 2000 / 1000
    assert report.multiples.price_to_free_cash_flow == pytest.approx(2000.0 / 133.1)  # FCF = 199,65 - 66,55
    assert report.multiples.free_cash_flow_yield == pytest.approx(133.1 / 2000.0)

    # --- Peer-Vergleich: Firma F erscheint, aber ohne erfundene Zahlen ---
    assert len(report.peer_multiples) == 1
    assert report.peer_multiples[0].entity_name == "Firma F (Branchenkollege, ohne Daten)"
    assert report.peer_multiples[0].price_earnings_ratio is None
    assert report.peer_multiples[0].ev_to_ebitda is None

    # --- DCF-Standardszenarien korrekt aus der Historie abgeleitet ---
    assert set(report.dcf_scenarios) == {"Basis", "Optimistisch", "Pessimistisch"}
    basis = report.dcf_scenarios["Basis"].assumptions
    assert basis.revenue_growth_rate == pytest.approx(0.10, abs=1e-9)  # 3-Jahres-CAGR
    assert basis.fcf_margin == pytest.approx(0.10, abs=1e-9)  # FCF 133,1 / Umsatz 1331
    assert basis.wacc == pytest.approx(DEFAULT_WACC)
    assert basis.terminal_growth_rate == pytest.approx(DEFAULT_TERMINAL_GROWTH_RATE)

    optimistisch = report.dcf_scenarios["Optimistisch"].assumptions
    pessimistisch = report.dcf_scenarios["Pessimistisch"].assumptions
    assert optimistisch.revenue_growth_rate == pytest.approx(0.13)
    assert pessimistisch.revenue_growth_rate == pytest.approx(0.07)

    # --- Bewertungsspanne statt Einzelkurs (Auftrag §6) ---
    assert report.fair_value_lower_band is not None
    assert report.fair_value_upper_band is not None
    assert report.fair_value_lower_band < report.fair_value_upper_band
    assert report.fair_value_lower_band == pytest.approx(
        report.dcf_scenarios["Pessimistisch"].fair_value_per_share
    )
    assert report.fair_value_upper_band == pytest.approx(
        report.dcf_scenarios["Optimistisch"].fair_value_per_share
    )

    # --- Sicherheitsmarge konsistent mit der reinen Formel ---
    erwartete_marge = safety_margin(report.fair_value_lower_band, report.multiples.price_per_share)
    assert report.safety_margin == pytest.approx(erwartete_marge)

    # --- Sensitivitätsmatrizen vorhanden (Wachstum×WACC, Marge×Terminalwachstum) ---
    assert report.sensitivity_growth_wacc is not None
    assert report.sensitivity_growth_wacc.fair_value_per_share[2][2] == pytest.approx(
        report.dcf_scenarios["Basis"].fair_value_per_share
    )
    assert report.sensitivity_margin_terminal_growth is not None

    assert report.missing_data_notes == ()


def test_valuation_report_bei_datenluecken_dokumentiert_offene_punkte(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (nur Umsatz, keine weiteren Daten)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()
        session.add(_dp(entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE, period_end=date(2022, 12, 31), value=500.0))
        session.add(_dp(entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=550.0))
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        report = build_valuation_report(session, entity)

    assert report.multiples.price_per_share is None
    assert report.multiples.price_earnings_ratio is None
    assert report.dcf_scenarios == {}
    assert report.fair_value_lower_band is None
    assert report.safety_margin is None
    assert any("Kein aktueller Kurs" in note for note in report.missing_data_notes)
    assert any("DCF nicht berechenbar" in note for note in report.missing_data_notes)
