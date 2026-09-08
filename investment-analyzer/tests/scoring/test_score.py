"""Tests für das Scoring-Modul (Auftrag §7, §15).

Zwei Ebenen:
1. Reine Handrechnungs-Tests für ``_linear_score`` und die einzelnen
   ``_score_*``-Komponentenfunktionen mit minimal-vollständigen, von
   Hand gebauten Berichten (präzise, unabhängig nachrechenbar).
2. Ein Integrationstest über die Datenbank (``score_entity``), der die
   Gewichtungs-/Abzugs-/Klassifikationslogik anhand der tatsächlich von
   ``build_fundamentals_report``/``build_valuation_report`` gelieferten
   Werte prüft (diese Pipelines sind bereits in
   ``tests/fundamentals/test_report.py`` und
   ``tests/valuation/test_report.py`` unabhängig hand-verifiziert).
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
from investment_analyzer.fundamentals.report import (
    CashflowProfile,
    FundamentalsReport,
    GrowthRates,
    LeverageProfile,
    MarginProfile,
    ReturnsProfile,
    ShareholderProfile,
)
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.risk.warning_signals import WarningSignal
from investment_analyzer.scoring.score import (
    DEFAULT_WEIGHTS,
    KLASSE_BEOBACHTEN,
    KLASSE_DATENLAGE_UNZUREICHEND,
    NOT_YET_IMPLEMENTABLE_COMPONENTS,
    _linear_score,
    _score_bewertung,
    _score_bilanzstaerke,
    _score_datenqualitaet,
    _score_finanzqualitaet,
    _score_management,
    _score_wachstum,
    compute_score,
    score_entity,
)
from investment_analyzer.valuation.report import MultiplesSnapshot, ValuationReport

# ---------------------------------------------------------------------------
# _linear_score: reine Handrechnung
# ---------------------------------------------------------------------------


def test_linear_score_mittelpunkt() -> None:
    assert _linear_score(0.10, 0.0, 0.20) == pytest.approx(50.0)


def test_linear_score_kappt_nach_oben_und_unten() -> None:
    assert _linear_score(0.30, 0.0, 0.20) == pytest.approx(100.0)
    assert _linear_score(-0.05, 0.0, 0.20) == pytest.approx(0.0)


def test_linear_score_umgekehrte_richtung_niedriger_ist_besser() -> None:
    # Verschuldungsgrad: 0 -> 100 Punkte, 6 -> 0 Punkte, 3 -> 50 Punkte
    assert _linear_score(0.0, 6.0, 0.0) == pytest.approx(100.0)
    assert _linear_score(6.0, 6.0, 0.0) == pytest.approx(0.0)
    assert _linear_score(3.0, 6.0, 0.0) == pytest.approx(50.0)


def test_linear_score_gleiche_grenzen_liefert_50() -> None:
    assert _linear_score(1.0, 5.0, 5.0) == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Minimal-vollständige Berichte für fokussierte Komponententests
# ---------------------------------------------------------------------------


def _leere_growth_rates() -> GrowthRates:
    return GrowthRates(None, None, None, None)


def _leerer_fundamentals_report(**overrides: object) -> FundamentalsReport:
    basis: dict[str, object] = {
        "entity_id": "e1",
        "entity_name": "Test AG",
        "generated_at_utc": datetime(2024, 1, 1, tzinfo=UTC),
        "as_of": datetime(2024, 1, 1, tzinfo=UTC),
        "revenue_growth": _leere_growth_rates(),
        "net_income_growth": _leere_growth_rates(),
        "eps_diluted_growth": _leere_growth_rates(),
        "free_cash_flow_growth": _leere_growth_rates(),
        "margins": MarginProfile(None, None, None, None, None, None, None),
        "returns": ReturnsProfile(None, None, None, 0.21),
        "cashflow": CashflowProfile(None, None, None, None),
        "leverage": LeverageProfile(None, None, None, None, None),
        "shareholder": ShareholderProfile(None, None, _leere_growth_rates()),
        "warning_signals": [],
        "not_yet_implementable_signals": (),
        "peers": [],
        "data_completeness": 1.0,
        "missing_fields": (),
    }
    basis.update(overrides)
    return FundamentalsReport(**basis)  # type: ignore[arg-type]


def _leerer_valuation_report(**overrides: object) -> ValuationReport:
    basis: dict[str, object] = {
        "entity_id": "e1",
        "entity_name": "Test AG",
        "generated_at_utc": datetime(2024, 1, 1, tzinfo=UTC),
        "as_of": datetime(2024, 1, 1, tzinfo=UTC),
        "multiples": MultiplesSnapshot(None, None, None, None, None, None, None, None, None, None),
        "peer_multiples": (),
        "dcf_scenarios": {},
        "sensitivity_growth_wacc": None,
        "sensitivity_margin_terminal_growth": None,
        "fair_value_lower_band": None,
        "fair_value_upper_band": None,
        "safety_margin": None,
        "missing_data_notes": (),
    }
    basis.update(overrides)
    return ValuationReport(**basis)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Komponententests (Handrechnung)
# ---------------------------------------------------------------------------


def test_score_finanzqualitaet_handrechnung() -> None:
    fr = _leerer_fundamentals_report(
        margins=MarginProfile(date(2023, 12, 31), 0.40, 0.20, 0.10, 0.0, 0.0, 0.0),
        returns=ReturnsProfile(date(2023, 12, 31), 0.15, 0.10, 0.21),
        cashflow=CashflowProfile(date(2023, 12, 31), 1.2, 0.05, 200.0),
    )
    score, notes = _score_finanzqualitaet(fr)

    erwartet = [
        _linear_score(0.10, 0.0, 0.20),  # Nettomarge
        _linear_score(0.40, 0.20, 0.60),  # Bruttomarge
        _linear_score(0.20, 0.05, 0.25),  # operative Marge
        _linear_score(0.0, 0.10, 0.0),  # Margenstabilität (perfekt stabil)
        _linear_score(0.15, 0.0, 0.25),  # ROE
        _linear_score(0.10, 0.0, 0.20),  # ROIC
        _linear_score(1.2, 0.3, 1.1),  # Cash Conversion (über Band -> gekappt)
    ]
    assert score == pytest.approx(sum(erwartet) / len(erwartet))
    assert len(notes) == 7


def test_score_finanzqualitaet_ohne_daten_liefert_none() -> None:
    fr = _leerer_fundamentals_report()
    score, notes = _score_finanzqualitaet(fr)
    assert score is None
    assert notes == []


def test_score_bewertung_handrechnung() -> None:
    vr = _leerer_valuation_report(safety_margin=0.20)
    score, notes = _score_bewertung(vr)
    assert score == pytest.approx(_linear_score(0.20, -0.20, 0.40))
    assert len(notes) == 1


def test_score_bewertung_ohne_sicherheitsmarge_liefert_none() -> None:
    vr = _leerer_valuation_report()
    score, notes = _score_bewertung(vr)
    assert score is None
    assert notes == []


def test_score_wachstum_handrechnung_mit_konsistenz() -> None:
    fr = _leerer_fundamentals_report(
        revenue_growth=GrowthRates(0.10, 0.10, None, None),
        net_income_growth=GrowthRates(0.12, 0.08, None, None),
    )
    score, notes = _score_wachstum(fr)
    erwartet = [
        _linear_score(0.10, -0.05, 0.15),  # Umsatzwachstum (3J bevorzugt)
        _linear_score(0.08, -0.10, 0.20),  # Gewinnwachstum (3J bevorzugt)
        100.0,  # 1J und 3J beide positiv -> konsistent
    ]
    assert score == pytest.approx(sum(erwartet) / len(erwartet))
    assert len(notes) == 3


def test_score_wachstum_uneinheitliche_richtung_wird_abgewertet() -> None:
    fr = _leerer_fundamentals_report(revenue_growth=GrowthRates(-0.02, 0.10, None, None))
    score, notes = _score_wachstum(fr)
    konsistenz_note = next(n for n in notes if "beständigkeit" in n.label.lower())
    assert konsistenz_note.score == pytest.approx(30.0)


def test_score_bilanzstaerke_handrechnung() -> None:
    fr = _leerer_fundamentals_report(
        leverage=LeverageProfile(date(2023, 12, 31), 200.0, 306.2, 200.0 / 306.2, 13.31),
        cashflow=CashflowProfile(date(2023, 12, 31), None, None, 200.0),
    )
    score, notes = _score_bilanzstaerke(fr)
    erwartet = [
        _linear_score(200.0 / 306.2, 6.0, 0.0),
        _linear_score(13.31, 1.0, 10.0),  # über Band -> gekappt auf 100
        100.0,  # positives Working Capital
    ]
    assert score == pytest.approx(sum(erwartet) / len(erwartet))
    assert len(notes) == 3


def test_score_management_dilution_handrechnung() -> None:
    fr = _leerer_fundamentals_report(
        shareholder=ShareholderProfile(date(2023, 12, 31), 0.3, GrowthRates(None, 0.03, None, None))
    )
    score, _notes = _score_management(fr)
    assert score == pytest.approx(_linear_score(0.03, 0.05, -0.02))


def test_score_management_ohne_daten_liefert_none() -> None:
    fr = _leerer_fundamentals_report()
    score, notes = _score_management(fr)
    assert score is None
    assert notes == []


def test_score_datenqualitaet_spiegelt_data_completeness() -> None:
    fr = _leerer_fundamentals_report(data_completeness=0.7)
    score, notes = _score_datenqualitaet(fr)
    assert score == pytest.approx(70.0)
    assert len(notes) == 1


# ---------------------------------------------------------------------------
# compute_score: Gewichtung, Konfidenz, Klassifikation, verbotene Formulierungen
# ---------------------------------------------------------------------------


def _vollstaendiger_fundamentals_report(**overrides: object) -> FundamentalsReport:
    basis: dict[str, object] = {
        "revenue_growth": GrowthRates(0.10, 0.10, None, None),
        "net_income_growth": GrowthRates(0.10, 0.10, None, None),
        "margins": MarginProfile(date(2023, 12, 31), 0.40, 0.20, 0.10, 0.0, 0.0, 0.0),
        "returns": ReturnsProfile(date(2023, 12, 31), 0.15, 0.10, 0.21),
        "cashflow": CashflowProfile(date(2023, 12, 31), 1.0, 0.05, 200.0),
        "leverage": LeverageProfile(date(2023, 12, 31), 200.0, 306.2, 0.65, 13.31),
        "shareholder": ShareholderProfile(date(2023, 12, 31), 0.3, GrowthRates(None, 0.0, None, None)),
        "data_completeness": 0.9,
    }
    basis.update(overrides)
    return _leerer_fundamentals_report(**basis)


def test_compute_score_gewichteter_durchschnitt_ueber_verfuegbare_komponenten() -> None:
    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(safety_margin=0.20)

    result = compute_score(fr, vr)

    verfuegbar = [c for c in result.components if c.score is not None]
    erwartetes_gewicht = sum(c.weight for c in verfuegbar)
    erwarteter_score = sum(c.score * c.weight for c in verfuegbar) / erwartetes_gewicht  # type: ignore[operator]

    assert result.raw_score == pytest.approx(erwarteter_score)
    assert result.total_score == pytest.approx(erwarteter_score)  # keine Warnsignale -> kein Abzug

    # Wettbewerbsvorteil (10) + Nachrichten (5) strukturell nicht verfügbar -> 85 % Abdeckung
    assert result.coverage == pytest.approx(0.85)
    for name in NOT_YET_IMPLEMENTABLE_COMPONENTS:
        komponente = next(c for c in result.components if c.name == name)
        assert komponente.score is None


def test_compute_score_risikoabzuege_sind_sichtbar_und_korrekt_summiert() -> None:
    fr = _vollstaendiger_fundamentals_report(
        warning_signals=[
            WarningSignal(code="strong_dilution", severity="mittel", description="X", evidence="Y"),
            WarningSignal(code="late_filing", severity="hoch", description="Z", evidence="W"),
        ]
    )
    vr = _leerer_valuation_report(safety_margin=0.20)

    result = compute_score(fr, vr)

    assert len(result.risk_deductions) == 2
    gesamtabzug = sum(d.points for d in result.risk_deductions)
    assert gesamtabzug == pytest.approx(5.0 + 10.0)
    assert result.total_score == pytest.approx(max(0.0, result.raw_score - gesamtabzug))  # type: ignore[operator]


def test_compute_score_starkes_unternehmen_wird_vertieft_pruefen(tmp_path: Path) -> None:
    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(safety_margin=0.30)

    result = compute_score(fr, vr)

    assert result.total_score is not None
    assert result.total_score >= 70.0
    assert result.classification == "Vertieft prüfen"


def test_compute_score_datenlage_unzureichend_bei_wenig_abdeckung() -> None:
    fr = _leerer_fundamentals_report(data_completeness=0.9)  # nur Datenqualität berechenbar (Gewicht 5)
    vr = _leerer_valuation_report()

    result = compute_score(fr, vr)

    assert result.coverage == pytest.approx(5.0 / 100.0)
    assert result.classification == KLASSE_DATENLAGE_UNZUREICHEND


def test_compute_score_niedrige_data_completeness_erzwingt_datenlage_unzureichend() -> None:
    fr = _vollstaendiger_fundamentals_report(data_completeness=0.1)
    vr = _leerer_valuation_report(safety_margin=0.30)

    result = compute_score(fr, vr)

    assert result.classification == KLASSE_DATENLAGE_UNZUREICHEND


def test_compute_score_hohe_abdeckung_aber_mittelmaessiger_score_ist_beobachten() -> None:
    fr = _vollstaendiger_fundamentals_report(
        margins=MarginProfile(date(2023, 12, 31), 0.25, 0.08, 0.03, 0.05, 0.05, 0.05),
        returns=ReturnsProfile(date(2023, 12, 31), 0.03, 0.02, 0.21),
        revenue_growth=GrowthRates(0.0, 0.0, None, None),
        net_income_growth=GrowthRates(0.0, 0.0, None, None),
    )
    vr = _leerer_valuation_report(safety_margin=-0.05)

    result = compute_score(fr, vr)
    assert result.classification in {KLASSE_BEOBACHTEN, "Derzeit unattraktiv"}


def test_compute_score_ungueltige_gewichte_wirft() -> None:
    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(safety_margin=0.2)
    unvollstaendige_gewichte = dict(DEFAULT_WEIGHTS)
    del unvollstaendige_gewichte["finanzqualitaet"]

    with pytest.raises(ValueError, match="weights"):
        compute_score(fr, vr, weights=unvollstaendige_gewichte)


def test_compute_score_benutzerdefinierte_gewichte_werden_nachvollziehbar_uebernommen() -> None:
    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(safety_margin=0.2)
    eigene_gewichte = dict(DEFAULT_WEIGHTS)
    eigene_gewichte["finanzqualitaet"] = 50.0
    eigene_gewichte["bewertung_sicherheitsmarge"] = 0.0

    result = compute_score(fr, vr, weights=eigene_gewichte)

    finanzqualitaet = next(c for c in result.components if c.name == "finanzqualitaet")
    bewertung = next(c for c in result.components if c.name == "bewertung_sicherheitsmarge")
    assert finanzqualitaet.weight == pytest.approx(50.0)
    assert bewertung.weight == pytest.approx(0.0)


def test_compute_score_texte_enthalten_keine_verbotenen_formulierungen() -> None:
    fr = _vollstaendiger_fundamentals_report(
        warning_signals=[WarningSignal(code="x", severity="hoch", description="Risiko X", evidence="Beleg Y")]
    )
    vr = _leerer_valuation_report(
        safety_margin=0.20,
        dcf_scenarios={},
    )

    result = compute_score(fr, vr)

    alle_texte = " ".join(
        [
            *result.top_positive_factors,
            *result.top_risks,
            *result.counterarguments,
            *result.invalidation_conditions,
        ]
    )
    assert "sicherer Kauf" not in alle_texte
    assert "garantierter Gewinn" not in alle_texte


def test_compute_score_gegenargumente_nennen_fehlende_komponenten() -> None:
    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(safety_margin=0.2)

    result = compute_score(fr, vr)

    gegenargumente_text = " ".join(result.counterarguments)
    assert "Wettbewerbsvorteil" in gegenargumente_text
    assert "Nachrichten und Katalysatoren" in gegenargumente_text


def test_compute_score_top_risks_enthaelt_warnsignal_evidenz() -> None:
    signal = WarningSignal(code="strong_dilution", severity="hoch", description="Starke Verwässerung.", evidence="12% p.a.")
    fr = _vollstaendiger_fundamentals_report(warning_signals=[signal])
    vr = _leerer_valuation_report(safety_margin=0.2)

    result = compute_score(fr, vr)

    assert any("Starke Verwässerung" in risk and "12% p.a." in risk for risk in result.top_risks)


def test_compute_score_invalidation_conditions_referenzieren_dcf_annahmen() -> None:
    from investment_analyzer.valuation.dcf import DCFAssumptions, DCFInputs, run_dcf

    annahmen = DCFAssumptions(revenue_growth_rate=0.08, fcf_margin=0.12, wacc=0.09, terminal_growth_rate=0.02)
    inputs = DCFInputs(base_revenue=1000.0, as_of=date(2023, 12, 31), net_debt=100.0, shares_diluted=50.0)
    ergebnis = run_dcf(annahmen, inputs, scenario_name="Basis")
    assert ergebnis is not None

    fr = _vollstaendiger_fundamentals_report()
    vr = _leerer_valuation_report(
        safety_margin=0.2, dcf_scenarios={"Basis": ergebnis}, fair_value_lower_band=ergebnis.fair_value_per_share
    )

    result = compute_score(fr, vr)
    bedingungen_text = " ".join(result.invalidation_conditions)
    assert "8.0%" in bedingungen_text or "8,0%" in bedingungen_text


# ---------------------------------------------------------------------------
# score_entity: Datenbank-Integration
# ---------------------------------------------------------------------------


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'score-entity-test.db'}")
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
    retrieved_at_utc: datetime,
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


def test_score_entity_end_to_end_gegen_datenbank(tmp_path: Path) -> None:
    fetched_at = datetime(2024, 3, 1, tzinfo=UTC)
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma H (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000008")],
        )
        session.flush()
        source = sources["sec_edgar"]

        jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
        umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
        for d, u in zip(jahre, umsatz, strict=True):
            session.add(_dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.1, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.GROSS_PROFIT, period_end=d, value=u * 0.4, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_INCOME, period_end=d, value=u * 0.2, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05, retrieved_at_utc=fetched_at))

        session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2022, 12, 31), value=800.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2023, 12, 31), value=900.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.LONG_TERM_DEBT, period_end=date(2023, 12, 31), value=300.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.SHORT_TERM_DEBT, period_end=date(2023, 12, 31), value=50.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CASH_AND_EQUIVALENTS, period_end=date(2023, 12, 31), value=150.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_ASSETS, period_end=date(2023, 12, 31), value=500.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_LIABILITIES, period_end=date(2023, 12, 31), value=300.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.DEPRECIATION_AND_AMORTIZATION, period_end=date(2023, 12, 31), value=40.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.INTEREST_EXPENSE, period_end=date(2023, 12, 31), value=20.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=1000.0, retrieved_at_utc=fetched_at))
        # Deutlich unter dem zu erwartenden fairen Wert -> positive Sicherheitsmarge:
        session.add(
            _dp(
                entity=entity, source=source, metric=Metric.PRICE_CLOSE,
                period_end=date(2024, 1, 15), value=1.00,
                retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        result = score_entity(session, entity)

    assert result.entity_name == "Firma H (synthetisches Beispiel)"
    assert result.coverage == pytest.approx(0.85)
    assert result.risk_deductions == ()  # keine Auffälligkeiten in diesem sauberen Beispiel
    assert result.total_score is not None
    assert result.classification in {"Vertieft prüfen", "Beobachten"}

    verfuegbar = [c for c in result.components if c.score is not None]
    erwarteter_score = sum(c.score * c.weight for c in verfuegbar) / sum(c.weight for c in verfuegbar)  # type: ignore[operator]
    assert result.raw_score == pytest.approx(erwarteter_score)

    assert 1 <= len(result.top_positive_factors) <= 5
    assert 0 <= len(result.top_risks) <= 5
    assert 1 <= len(result.counterarguments) <= 5
    assert 1 <= len(result.invalidation_conditions) <= 5


def test_score_entity_widerspruechliche_daten_fuehren_zu_sichtbarer_warnung(tmp_path: Path) -> None:
    """Milestone-8-Ausfalltest (SECURITY.md: „absichtlich falsche/
    widersprüchliche Testdaten [...] muss zu sichtbarer Warnung führen,
    nicht zu stiller Fehlkalkulation").

    Ansonsten identisch zu ``test_score_entity_end_to_end_gegen_datenbank``
    (dieselbe „saubere" Basis), aber mit einer stark widersprüchlichen
    Zusatzangabe: die verwässerte Aktienanzahl versechsfacht sich
    innerhalb von drei Jahren (Auftrag-widriges Ausreißer-Datum, wie es
    z. B. bei einem Dateneingabefehler oder einer manipulierten Quelle
    entstehen könnte). Das Ergebnis MUSS sichtbar (``risk_deductions``,
    ``top_risks``, reduzierter ``total_score``) reagieren, statt die
    Verwässerung stillschweigend zu ignorieren oder einen unauffällig
    hohen Score auszugeben."""

    fetched_at = datetime(2024, 3, 1, tzinfo=UTC)
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma I (widersprüchliche Testdaten)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000010")],
        )
        session.flush()
        source = sources["sec_edgar"]

        jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
        umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
        for d, u in zip(jahre, umsatz, strict=True):
            session.add(_dp(entity=entity, source=source, metric=Metric.REVENUE, period_end=d, value=u, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.NET_INCOME, period_end=d, value=u * 0.1, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.GROSS_PROFIT, period_end=d, value=u * 0.4, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_INCOME, period_end=d, value=u * 0.2, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15, retrieved_at_utc=fetched_at))
            session.add(_dp(entity=entity, source=source, metric=Metric.CAPEX, period_end=d, value=-u * 0.05, retrieved_at_utc=fetched_at))

        session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2022, 12, 31), value=800.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.TOTAL_EQUITY, period_end=date(2023, 12, 31), value=900.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.LONG_TERM_DEBT, period_end=date(2023, 12, 31), value=300.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.SHORT_TERM_DEBT, period_end=date(2023, 12, 31), value=50.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CASH_AND_EQUIVALENTS, period_end=date(2023, 12, 31), value=150.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_ASSETS, period_end=date(2023, 12, 31), value=500.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.CURRENT_LIABILITIES, period_end=date(2023, 12, 31), value=300.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.DEPRECIATION_AND_AMORTIZATION, period_end=date(2023, 12, 31), value=40.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.INTEREST_EXPENSE, period_end=date(2023, 12, 31), value=20.0, retrieved_at_utc=fetched_at))
        # Widersprüchlich/extrem: Versechsfachung der verwässerten Aktienanzahl
        # in drei Jahren (Schwelle für "starke Verwässerung": 3 %/Jahr).
        session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2020, 12, 31), value=1000.0, retrieved_at_utc=fetched_at))
        session.add(_dp(entity=entity, source=source, metric=Metric.SHARES_DILUTED, period_end=date(2023, 12, 31), value=6000.0, retrieved_at_utc=fetched_at))
        session.add(
            _dp(
                entity=entity, source=source, metric=Metric.PRICE_CLOSE,
                period_end=date(2024, 1, 15), value=1.00,
                retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        result = score_entity(session, entity)

    # Sichtbare Warnung, kein stilles Ignorieren:
    assert result.risk_deductions != ()
    assert any(d.code == "strong_dilution" for d in result.risk_deductions)
    assert result.top_risks  # mindestens ein Risiko wird in der Kurzfassung genannt

    # Der Score wird sichtbar reduziert (kein unbeeinflusster "sauberer" Score):
    assert result.total_score is not None
    assert result.raw_score is not None
    assert result.total_score < result.raw_score


def test_score_entity_ohne_jegliche_daten_ist_datenlage_unzureichend(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000009")],
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        result = score_entity(session, entity)

    assert result.classification == KLASSE_DATENLAGE_UNZUREICHEND
