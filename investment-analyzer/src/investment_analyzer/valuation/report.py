"""Orchestrierung: baut einen ``ValuationReport`` aus Multiples, DCF-Szenarien,
Sensitivitätsmatrizen und Sicherheitsmarge (Auftrag §6 „Bewertung").

Wie ``fundamentals/report.py``: alle Zahlen entstehen deterministisch aus
point-in-time-gefilterten ``DataPoint``-Zeitreihen (``fundamentals/series.py``)
und reinen Berechnungsfunktionen — nichts wird vom Sprachmodell erfunden
(Auftrag §11). Fehlt eine Eingabe (z. B. kein aktueller Kurs, keine
Schuldendaten), bleibt das betroffene Feld ``None`` statt geschätzt zu
werden; ``missing_data_notes`` macht das für nachgelagerte Schritte
(Scoring, UI) sichtbar.

**WACC und Terminalwachstum sind echte Annahmen, keine gemeldeten
Werte** (Auftrag §1: Annahmen deutlich kennzeichnen). Die Standardwerte
(``DEFAULT_WACC``, ``DEFAULT_TERMINAL_GROWTH_RATE``) sind grobe,
marktübliche Schätzungen — ein Aufrufer, der bessere unternehmens-
spezifische Werte hat (z. B. ein tatsächlich hergeleiteter WACC), sollte
sie explizit überschreiben.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime

from sqlalchemy.orm import Session

from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals import calculations as calc
from investment_analyzer.fundamentals import series
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.fundamentals.peers import find_peers
from investment_analyzer.valuation import multiples as m
from investment_analyzer.valuation.dcf import (
    DCFAssumptions,
    DCFInputs,
    DCFResult,
    SensitivityMatrix,
    build_sensitivity_matrix,
    run_dcf,
    safety_margin,
)

#: Grobe, marktübliche Schätzung (kein unternehmensspezifisch hergeleiteter WACC) — Annahme, kein gemeldeter Wert.
DEFAULT_WACC = 0.09
#: Langfristige Wachstumsannahme in Höhe eines groben nominalen BIP-/Inflationsniveaus — Annahme.
DEFAULT_TERMINAL_GROWTH_RATE = 0.02

OPTIMISTIC_GROWTH_DELTA = 0.03
PESSIMISTIC_GROWTH_DELTA = -0.03
OPTIMISTIC_MARGIN_DELTA = 0.02
PESSIMISTIC_MARGIN_DELTA = -0.02
_MIN_FCF_MARGIN = 0.001


@dataclass(frozen=True)
class MultiplesSnapshot:
    as_of: date | None
    price_per_share: float | None
    market_cap: float | None
    enterprise_value: float | None
    price_earnings_ratio: float | None
    ev_to_ebitda: float | None
    ev_to_ebit: float | None
    price_to_book: float | None
    price_to_free_cash_flow: float | None
    free_cash_flow_yield: float | None


@dataclass(frozen=True)
class PeerMultiple:
    entity_id: str
    entity_name: str
    price_earnings_ratio: float | None
    ev_to_ebitda: float | None


@dataclass(frozen=True)
class ValuationReport:
    entity_id: str
    entity_name: str
    generated_at_utc: datetime
    as_of: datetime

    multiples: MultiplesSnapshot
    peer_multiples: tuple[PeerMultiple, ...]

    dcf_scenarios: dict[str, DCFResult]
    sensitivity_growth_wacc: SensitivityMatrix | None
    sensitivity_margin_terminal_growth: SensitivityMatrix | None
    fair_value_lower_band: float | None
    fair_value_upper_band: float | None
    safety_margin: float | None

    missing_data_notes: tuple[str, ...]


def _value_at(session: Session, entity: Entity, metric: Metric, target_date: date | None, reference: datetime) -> float | None:
    if target_date is None:
        return None
    return series.get_value_at(session, entity, metric, target_date, as_of=reference)


def _compute_multiples_snapshot(session: Session, entity: Entity, reference: datetime) -> MultiplesSnapshot:
    price_point = series.get_latest_value(session, entity, Metric.PRICE_CLOSE, as_of=reference)
    price = price_point[1] if price_point else None

    revenue_point = series.get_latest_annual_value(session, entity, Metric.REVENUE, as_of=reference)
    latest_date = revenue_point[0] if revenue_point else None

    def value_at(metric: Metric) -> float | None:
        return _value_at(session, entity, metric, latest_date, reference)

    eps = value_at(Metric.EPS_DILUTED)
    operating_income = value_at(Metric.OPERATING_INCOME)
    depreciation_and_amortization = value_at(Metric.DEPRECIATION_AND_AMORTIZATION)
    ebitda_value = calc.ebitda(operating_income, depreciation_and_amortization)
    equity = value_at(Metric.TOTAL_EQUITY)
    long_term_debt = value_at(Metric.LONG_TERM_DEBT)
    short_term_debt = value_at(Metric.SHORT_TERM_DEBT)
    total_debt: float | None = None
    if long_term_debt is not None or short_term_debt is not None:
        total_debt = (long_term_debt or 0.0) + (short_term_debt or 0.0)
    cash = value_at(Metric.CASH_AND_EQUIVALENTS)
    shares_diluted = value_at(Metric.SHARES_DILUTED)
    ocf = value_at(Metric.OPERATING_CASH_FLOW)
    capex = value_at(Metric.CAPEX)
    fcf: float | None = None
    if ocf is not None and capex is not None:
        fcf = ocf - abs(capex)

    market_cap = m.market_capitalization(price, shares_diluted)
    ev = m.enterprise_value(market_cap, total_debt, cash) if total_debt is not None and cash is not None else None

    return MultiplesSnapshot(
        as_of=latest_date,
        price_per_share=price,
        market_cap=market_cap,
        enterprise_value=ev,
        price_earnings_ratio=m.price_earnings_ratio(price, eps),
        ev_to_ebitda=m.ev_to_ebitda(ev, ebitda_value),
        ev_to_ebit=m.ev_to_ebit(ev, operating_income),
        price_to_book=m.price_to_book(market_cap, equity),
        price_to_free_cash_flow=m.price_to_free_cash_flow(market_cap, fcf),
        free_cash_flow_yield=m.free_cash_flow_yield(fcf, market_cap),
    )


def derive_default_scenarios(
    session: Session,
    entity: Entity,
    *,
    reference: datetime,
    wacc: float = DEFAULT_WACC,
    terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE,
) -> dict[str, DCFAssumptions] | None:
    """Leitet Basis-/Optimistisch-/Pessimistisch-Annahmen aus der eigenen Historie ab.

    Liefert ``None``, wenn weder eine 3- noch eine 1-Jahres-Umsatzwachstumsrate
    UND eine plausible (positive) freie-Cashflow-Marge des jüngsten
    Geschäftsjahres ermittelbar sind — es wird keine Wachstums-/Margenannahme
    erfunden (Auftrag §11).
    """

    revenue_series = series.get_annual_series(session, entity, Metric.REVENUE, as_of=reference)
    ocf_series = dict(series.get_annual_series(session, entity, Metric.OPERATING_CASH_FLOW, as_of=reference))
    capex_series = dict(series.get_annual_series(session, entity, Metric.CAPEX, as_of=reference))

    if not revenue_series:
        return None

    base_growth = calc.growth_rate(revenue_series, horizon_years=3)
    if base_growth is None:
        base_growth = calc.growth_rate(revenue_series, horizon_years=1)
    if base_growth is None:
        return None

    latest_revenue_date, latest_revenue = revenue_series[-1]
    ocf = ocf_series.get(latest_revenue_date)
    capex = capex_series.get(latest_revenue_date)
    if ocf is None or capex is None:
        return None
    base_fcf_margin = calc.margin(ocf - abs(capex), latest_revenue)
    if base_fcf_margin is None or base_fcf_margin <= 0:
        return None

    basis = DCFAssumptions(
        revenue_growth_rate=base_growth,
        fcf_margin=base_fcf_margin,
        wacc=wacc,
        terminal_growth_rate=terminal_growth_rate,
    )
    optimistisch = replace(
        basis,
        revenue_growth_rate=base_growth + OPTIMISTIC_GROWTH_DELTA,
        fcf_margin=max(base_fcf_margin + OPTIMISTIC_MARGIN_DELTA, _MIN_FCF_MARGIN),
    )
    pessimistisch = replace(
        basis,
        revenue_growth_rate=base_growth + PESSIMISTIC_GROWTH_DELTA,
        fcf_margin=max(base_fcf_margin + PESSIMISTIC_MARGIN_DELTA, _MIN_FCF_MARGIN),
    )

    return {"Basis": basis, "Optimistisch": optimistisch, "Pessimistisch": pessimistisch}


def build_valuation_report(
    session: Session,
    entity: Entity,
    *,
    as_of: datetime | None = None,
    scenarios: dict[str, DCFAssumptions] | None = None,
    wacc: float = DEFAULT_WACC,
    terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE,
) -> ValuationReport:
    """Baut einen vollständigen Bewertungsbericht für ``entity`` (Auftrag §6)."""

    reference = as_of or utc_now()
    notes: list[str] = []

    multiples_snapshot = _compute_multiples_snapshot(session, entity, reference)
    if multiples_snapshot.price_per_share is None:
        notes.append("Kein aktueller Kurs verfügbar — Multiples und Sicherheitsmarge nicht berechenbar.")

    peers = find_peers(session, entity)
    peer_multiples = tuple(
        PeerMultiple(
            entity_id=peer.id,
            entity_name=peer.name,
            price_earnings_ratio=(snap := _compute_multiples_snapshot(session, peer, reference)).price_earnings_ratio,
            ev_to_ebitda=snap.ev_to_ebitda,
        )
        for peer in peers
    )

    scenarios_used = scenarios
    if scenarios_used is None:
        scenarios_used = derive_default_scenarios(
            session, entity, reference=reference, wacc=wacc, terminal_growth_rate=terminal_growth_rate
        )
        if scenarios_used is None:
            notes.append(
                "DCF nicht berechenbar: keine ausreichende Umsatzwachstums-/"
                "Cashflow-Historie für eine Basisannahme vorhanden."
            )

    revenue_point = series.get_latest_annual_value(session, entity, Metric.REVENUE, as_of=reference)

    dcf_results: dict[str, DCFResult] = {}
    sensitivity_growth_wacc: SensitivityMatrix | None = None
    sensitivity_margin_terminal_growth: SensitivityMatrix | None = None
    fair_value_lower: float | None = None
    fair_value_upper: float | None = None
    margin_of_safety: float | None = None

    if scenarios_used is not None and revenue_point is not None:
        latest_date, base_revenue = revenue_point
        long_term_debt = _value_at(session, entity, Metric.LONG_TERM_DEBT, latest_date, reference)
        short_term_debt = _value_at(session, entity, Metric.SHORT_TERM_DEBT, latest_date, reference)
        cash = _value_at(session, entity, Metric.CASH_AND_EQUIVALENTS, latest_date, reference)
        shares_diluted = _value_at(session, entity, Metric.SHARES_DILUTED, latest_date, reference)

        total_debt: float | None = None
        if long_term_debt is not None or short_term_debt is not None:
            total_debt = (long_term_debt or 0.0) + (short_term_debt or 0.0)
        net_debt_value = calc.net_debt(total_debt, cash) if total_debt is not None and cash is not None else None
        if net_debt_value is None:
            notes.append("DCF liefert keinen fairen Wert je Aktie: Schuldendaten unvollständig.")
        if not shares_diluted:
            notes.append("DCF liefert keinen fairen Wert je Aktie: Aktienanzahl unbekannt.")

        dcf_inputs = DCFInputs(
            base_revenue=base_revenue, as_of=latest_date, net_debt=net_debt_value, shares_diluted=shares_diluted
        )

        for scenario_name, assumptions in scenarios_used.items():
            result = run_dcf(assumptions, dcf_inputs, scenario_name=scenario_name)
            if result is not None:
                dcf_results[scenario_name] = result

        fair_values = [
            r.fair_value_per_share for r in dcf_results.values() if r.fair_value_per_share is not None
        ]
        if fair_values:
            fair_value_lower = min(fair_values)
            fair_value_upper = max(fair_values)
            margin_of_safety = safety_margin(fair_value_lower, multiples_snapshot.price_per_share)

        base_assumptions = scenarios_used.get("Basis")
        if base_assumptions is not None:
            sensitivity_growth_wacc = build_sensitivity_matrix(
                base_assumptions,
                dcf_inputs,
                row_parameter="revenue_growth_rate",
                row_values=[base_assumptions.revenue_growth_rate + d for d in (-0.02, -0.01, 0.0, 0.01, 0.02)],
                column_parameter="wacc",
                column_values=[base_assumptions.wacc + d for d in (-0.01, -0.005, 0.0, 0.005, 0.01)],
            )
            sensitivity_margin_terminal_growth = build_sensitivity_matrix(
                base_assumptions,
                dcf_inputs,
                row_parameter="fcf_margin",
                row_values=[
                    max(base_assumptions.fcf_margin + d, _MIN_FCF_MARGIN)
                    for d in (-0.02, -0.01, 0.0, 0.01, 0.02)
                ],
                column_parameter="terminal_growth_rate",
                column_values=[
                    base_assumptions.terminal_growth_rate + d for d in (-0.01, -0.005, 0.0, 0.005, 0.01)
                ],
            )
    elif scenarios_used is not None and revenue_point is None:
        notes.append("DCF nicht berechenbar: kein aktueller Jahresumsatz vorhanden.")

    return ValuationReport(
        entity_id=entity.id,
        entity_name=entity.name,
        generated_at_utc=utc_now(),
        as_of=reference,
        multiples=multiples_snapshot,
        peer_multiples=peer_multiples,
        dcf_scenarios=dcf_results,
        sensitivity_growth_wacc=sensitivity_growth_wacc,
        sensitivity_margin_terminal_growth=sensitivity_margin_terminal_growth,
        fair_value_lower_band=fair_value_lower,
        fair_value_upper_band=fair_value_upper,
        safety_margin=margin_of_safety,
        missing_data_notes=tuple(notes),
    )
