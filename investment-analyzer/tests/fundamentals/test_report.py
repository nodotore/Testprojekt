"""Handrechnungs-Tests für ``FundamentalsReport`` (Auftrag §15).

**Wichtiger Hinweis:** Alle drei Testfälle verwenden bewusst einfache,
synthetische Finanzkennzahlen (keine echten Unternehmensdaten). Das vom
Auftrag geforderte Abnahmekriterium „mind. 3 reale Unternehmen,
Handrechnung vs. Code" konnte in dieser Sandbox mangels Internetzugang
nicht mit echten SEC-Filings durchgeführt werden (siehe PROGRESS.md,
NEXT_STEPS.md — dieselbe Einschränkung wie bei den Connector-Tests in
Milestone 2). Diese Tests verifizieren stattdessen, dass der
Berechnungscode für klar nachvollziehbare, von Hand nachrechenbare
Eingaben exakt das erwartete Ergebnis liefert — das bestätigt die
Korrektheit der Formeln, ersetzt aber nicht die noch ausstehende
Verifikation an echten, veröffentlichten Geschäftszahlen.
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
from investment_analyzer.fundamentals.report import build_fundamentals_report
from investment_analyzer.normalization.models import DataPoint, ValueKind

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'report-test.db'}")
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


def _insert_firma_a(session, entity: Entity, source: Source) -> None:
    """Sauberes, gleichmäßig um 10 %/Jahr wachsendes Beispielunternehmen (2020–2023)."""

    jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
    umsatz = [1000.0, 1100.0, 1210.0, 1331.0]  # exakt 10 %/Jahr (1,1^n)
    for d, u in zip(jahre, umsatz, strict=True):
        session.add(_dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u))
        session.add(_dp(entity=entity, source=source, metric=Metric.GROSS_PROFIT, period_end=d, value=u * 0.4))
        session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_INCOME, period_end=d, value=u * 0.2))
        session.add(_dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.1))
        session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.1 * 1.2))
        session.add(_dp(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05))

    session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2022, 12, 31), value=800.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2023, 12, 31), value=900.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.LONG_TERM_DEBT, period_end=date(2023, 12, 31), value=300.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.SHORT_TERM_DEBT, period_end=date(2023, 12, 31), value=50.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.CASH_AND_EQUIVALENTS, period_end=date(2023, 12, 31), value=150.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_ASSETS, period_end=date(2023, 12, 31), value=500.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_LIABILITIES, period_end=date(2023, 12, 31), value=300.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.DEPRECIATION_AND_AMORTIZATION, period_end=date(2023, 12, 31), value=40.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.INTEREST_EXPENSE, period_end=date(2023, 12, 31), value=20.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.DIVIDENDS_PAID, period_end=date(2023, 12, 31), value=-40.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0))
    session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=1000.0))


def test_fundamentals_report_firma_a_sauberes_unternehmen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma A (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        entity.sic_code = "3571"
        session.flush()
        _insert_firma_a(session, entity, sources["sec_edgar"])
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        report = build_fundamentals_report(session, entity)

    # --- Wachstum: 1,1^3 = 1,331 exakt -> 10 % über 1 und über 3 Jahre ---
    assert report.revenue_growth.horizon_1y == pytest.approx(0.10, abs=1e-9)
    assert report.revenue_growth.horizon_3y == pytest.approx(0.10, abs=1e-9)
    assert report.revenue_growth.horizon_5y is None
    assert report.revenue_growth.horizon_10y is None
    assert report.net_income_growth.horizon_1y == pytest.approx(0.10, abs=1e-9)
    assert report.net_income_growth.horizon_3y == pytest.approx(0.10, abs=1e-9)
    # Freier Cashflow skaliert 1:1 mit Umsatz/Gewinn (OCF und Capex beide *10 % p. a.):
    assert report.free_cash_flow_growth.horizon_1y == pytest.approx(0.10, abs=1e-9)
    assert report.free_cash_flow_growth.horizon_3y == pytest.approx(0.10, abs=1e-9)
    # Keine EPS-Daten geliefert -> ehrlich None statt geschätzt:
    assert report.eps_diluted_growth.horizon_1y is None

    # --- Margen: konstant 40 % / 20 % / 10 %, daher Stabilität (Stdev) = 0 ---
    assert report.margins.gross_margin == pytest.approx(0.40)
    assert report.margins.operating_margin == pytest.approx(0.20)
    assert report.margins.net_margin == pytest.approx(0.10)
    assert report.margins.gross_margin_stability == pytest.approx(0.0, abs=1e-9)
    assert report.margins.operating_margin_stability == pytest.approx(0.0, abs=1e-9)
    assert report.margins.net_margin_stability == pytest.approx(0.0, abs=1e-9)

    # --- Renditen: ROE = 133,1 / ((800+900)/2) = 133,1/850 ---
    assert report.returns.return_on_equity == pytest.approx(133.1 / 850.0)
    # ROIC: NOPAT = 266,2*(1-0,21)=210,298; invested_capital = 350+900-150=1100
    assert report.returns.return_on_invested_capital == pytest.approx(210.298 / 1100.0)
    assert report.returns.roic_tax_rate_assumption == pytest.approx(0.21)

    # --- Cashflow: Cash Conversion = OCF/Nettogewinn = 1,2 (per Konstruktion) ---
    assert report.cashflow.cash_conversion == pytest.approx(1.2)
    assert report.cashflow.capex_ratio == pytest.approx(0.05)
    assert report.cashflow.working_capital == pytest.approx(200.0)  # 500 - 300

    # --- Verschuldung ---
    assert report.leverage.net_debt == pytest.approx(200.0)  # 350 - 150
    assert report.leverage.ebitda == pytest.approx(306.2)  # 266,2 + 40
    assert report.leverage.net_debt_to_ebitda == pytest.approx(200.0 / 306.2)
    assert report.leverage.interest_coverage == pytest.approx(266.2 / 20.0)

    # --- Ausschüttung/Verwässerung ---
    assert report.shareholder.dividend_payout_ratio == pytest.approx(40.0 / 133.1)
    assert report.shareholder.shares_diluted_growth.horizon_3y == pytest.approx(0.0, abs=1e-9)

    # --- Keine Warnsignale bei diesem sauberen Beispiel ---
    assert report.warning_signals == []
    assert "going_concern_hinweise" in report.not_yet_implementable_signals

    # --- Datenvollständigkeit: von 33 versuchten Feldern sind 10 mangels
    #     EPS-/Langfrist-Historie None (ehrlich ausgewiesen, nicht geraten) ---
    assert len(report.missing_fields) == 10
    assert "eps_diluted_growth_1y" in report.missing_fields
    assert "revenue_growth_10y" in report.missing_fields
    assert report.data_completeness == pytest.approx((33 - 10) / 33)


def test_fundamentals_report_firma_b_datenluecken_und_warnsignal(tmp_path: Path) -> None:
    """Firma B liefert bewusst nur Nettogewinn und operativen Cashflow —
    demonstriert, dass fehlende Daten ehrlich als None erscheinen (nicht
    geraten) und dass ein Warnsignal trotzdem korrekt erkannt wird."""

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma B (synthetisches Beispiel, Datenlücken)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        source = sources["sec_edgar"]
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2022, 12, 31), value=100.0),
                _dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=date(2023, 12, 31), value=120.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2022, 12, 31), value=150.0),
                _dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=date(2023, 12, 31), value=100.0),
            ]
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        report = build_fundamentals_report(session, entity)

    # Nettogewinn-Wachstum: 120/100 - 1 = 20 %
    assert report.net_income_growth.horizon_1y == pytest.approx(0.20)
    # Cash Conversion: 100 / 120 (Umsatz fehlt, daher latest_date aus Nettogewinn-Serie)
    assert report.cashflow.cash_conversion == pytest.approx(100.0 / 120.0)

    # Umsatz wurde nie geliefert -> Margen/Renditen ehrlich None statt geraten
    assert report.margins.gross_margin is None
    assert report.margins.net_margin is None
    assert report.returns.return_on_equity is None
    assert report.revenue_growth.horizon_1y is None

    # Sinkender Cashflow (-33,3 %) trotz steigendem Gewinn (+20 %) -> Warnsignal
    codes = {s.code for s in report.warning_signals}
    assert "cashflow_divergence" in codes

    # Nur 2 von 33 Feldern tatsächlich berechenbar -> Konfidenz muss das widerspiegeln
    assert report.data_completeness < 0.10
    assert len(report.missing_fields) == 31


def test_fundamentals_report_findet_peers_ueber_sic_code(tmp_path: Path) -> None:
    """Firma C teilt sich den SIC-Code mit Firma A und muss als Peer erscheinen."""

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        firma_a = find_or_create_entity(
            session, name="Firma A (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        firma_a.sic_code = "3571"
        firma_c = find_or_create_entity(
            session, name="Firma C (gleiche Branche)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000003")],
        )
        firma_c.sic_code = "3571"
        session.flush()
        _insert_firma_a(session, firma_a, sources["sec_edgar"])
        session.add(
            _dp(entity=firma_c, source=sources["sec_edgar"], metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=500.0)
        )
        session.commit()
        firma_a_id = firma_a.id

    with session_factory() as session:
        firma_a = session.get(Entity, firma_a_id)
        assert firma_a is not None
        report = build_fundamentals_report(session, firma_a)

    assert [p.name for p in report.peers] == ["Firma C (gleiche Branche)"]


def test_fundamentals_report_ist_point_in_time(tmp_path: Path) -> None:
    """Ein erst später eingetroffenes Restatement darf ein Wachstum vor
    seinem Eintreffen nicht beeinflussen (kein Look-ahead, Auftrag §9)."""

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma D (Point-in-time-Test)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000004")],
        )
        session.flush()
        source = sources["sec_edgar"]
        session.add_all(
            [
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2022, 12, 31), value=1000.0),
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1100.0,
                    retrieved_at_utc=datetime(2024, 2, 1, tzinfo=UTC)),
                # Restatement, aber erst deutlich später bekannt geworden:
                _dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=date(2023, 12, 31), value=1150.0,
                    retrieved_at_utc=datetime(2024, 8, 1, tzinfo=UTC)),
            ]
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        report_vorher = build_fundamentals_report(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        report_nachher = build_fundamentals_report(session, entity, as_of=datetime(2024, 9, 1, tzinfo=UTC))

    assert report_vorher.revenue_growth.horizon_1y == pytest.approx(0.10)  # 1100/1000 - 1
    assert report_nachher.revenue_growth.horizon_1y == pytest.approx(0.15)  # 1150/1000 - 1
