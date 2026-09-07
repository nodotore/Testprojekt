"""Orchestrierung: baut einen ``FundamentalsReport`` aus den Bausteinen dieses Moduls
(Auftrag §6 „Fundamentaldaten").

Alle Zahlen entstehen deterministisch aus den in ``fundamentals/series.py``
abgefragten, point-in-time-gefilterten ``DataPoint``-Zeitreihen und den
reinen Funktionen aus ``fundamentals/calculations.py`` — nichts wird vom
Sprachmodell erfunden (Auftrag §11). Fehlt eine Eingabe, wird das
entsprechende Feld ``None`` statt eines geratenen Werts; ``missing_fields``
und ``data_completeness`` machen das für nachgelagerte Schritte
(Scoring, Milestone 4) sichtbar, statt es stillschweigend als „neutral"
zu behandeln (Auftrag §7).

Der ROIC-Steuersatz ist die einzige echte Annahme in diesem Modul — ein
expliziter, im Report sichtbarer Parameter (``roic_tax_rate_assumption``),
kein stiller Default tief im Code.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.orm import Session

from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals import calculations as calc
from investment_analyzer.fundamentals import series
from investment_analyzer.fundamentals.calculations import TimeSeries
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.fundamentals.peers import find_peers
from investment_analyzer.risk.warning_signals import (
    NOT_YET_IMPLEMENTABLE_SIGNALS,
    WarningSignal,
    run_all_checks,
)

#: In Milestone 3 verwendeter Standard-Steuersatz für ROIC (aktueller US-Bundes-
#: Körperschaftsteuersatz) — eine Schätzung/Annahme, kein gemeldeter Wert
#: (Auftrag §1: Annahmen deutlich kennzeichnen). Aufrufer können einen
#: abweichenden Satz über ``roic_tax_rate`` explizit übergeben.
DEFAULT_ROIC_TAX_RATE = 0.21


@dataclass(frozen=True)
class GrowthRates:
    """CAGR über die in Auftrag §6 geforderten Horizonte (1/3/5/10 Jahre)."""

    horizon_1y: float | None
    horizon_3y: float | None
    horizon_5y: float | None
    horizon_10y: float | None


@dataclass(frozen=True)
class MarginProfile:
    latest_period_end: date | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    gross_margin_stability: float | None
    operating_margin_stability: float | None
    net_margin_stability: float | None


@dataclass(frozen=True)
class ReturnsProfile:
    latest_period_end: date | None
    return_on_equity: float | None
    return_on_invested_capital: float | None
    roic_tax_rate_assumption: float


@dataclass(frozen=True)
class CashflowProfile:
    latest_period_end: date | None
    cash_conversion: float | None
    capex_ratio: float | None
    working_capital: float | None


@dataclass(frozen=True)
class LeverageProfile:
    latest_period_end: date | None
    net_debt: float | None
    ebitda: float | None
    net_debt_to_ebitda: float | None
    interest_coverage: float | None


@dataclass(frozen=True)
class ShareholderProfile:
    latest_period_end: date | None
    dividend_payout_ratio: float | None
    shares_diluted_growth: GrowthRates


@dataclass(frozen=True)
class FundamentalsReport:
    entity_id: str
    entity_name: str
    generated_at_utc: datetime
    as_of: datetime

    revenue_growth: GrowthRates
    net_income_growth: GrowthRates
    eps_diluted_growth: GrowthRates
    free_cash_flow_growth: GrowthRates

    margins: MarginProfile
    returns: ReturnsProfile
    cashflow: CashflowProfile
    leverage: LeverageProfile
    shareholder: ShareholderProfile

    warning_signals: list[WarningSignal]
    not_yet_implementable_signals: tuple[str, ...]
    peers: list[Entity] = field(repr=False)

    data_completeness: float
    missing_fields: tuple[str, ...]


def _combine(a: TimeSeries, b: TimeSeries, op: Callable[[float, float], float | None]) -> list[tuple[date, float]]:
    """Verknüpft zwei Zeitreihen über gemeinsame Periodenenden (z. B. Marge = a/b)."""

    a_map = dict(a)
    b_map = dict(b)
    result: list[tuple[date, float]] = []
    for d in sorted(set(a_map) & set(b_map)):
        value = op(a_map[d], b_map[d])
        if value is not None:
            result.append((d, value))
    return result


def _growth_rates_for(points: TimeSeries) -> GrowthRates:
    return GrowthRates(
        horizon_1y=calc.growth_rate(points, horizon_years=1),
        horizon_3y=calc.growth_rate(points, horizon_years=3),
        horizon_5y=calc.growth_rate(points, horizon_years=5),
        horizon_10y=calc.growth_rate(points, horizon_years=10),
    )


def build_fundamentals_report(
    session: Session,
    entity: Entity,
    *,
    as_of: datetime | None = None,
    roic_tax_rate: float = DEFAULT_ROIC_TAX_RATE,
) -> FundamentalsReport:
    """Baut einen vollständigen Fundamentalbericht für ``entity`` (Auftrag §6)."""

    reference = as_of or utc_now()

    def annual(metric: Metric) -> list[tuple[date, float]]:
        return series.get_annual_series(session, entity, metric, as_of=reference)

    def value_at(metric: Metric, target_date: date | None) -> float | None:
        if target_date is None:
            return None
        return series.get_value_at(session, entity, metric, target_date, as_of=reference)

    revenue_series = annual(Metric.REVENUE)
    net_income_series = annual(Metric.NET_INCOME)
    eps_series = annual(Metric.EPS_DILUTED)
    ocf_series = annual(Metric.OPERATING_CASH_FLOW)
    capex_series = annual(Metric.CAPEX)
    shares_series = annual(Metric.SHARES_DILUTED)
    fcf_series = _combine(ocf_series, capex_series, lambda ocf, capex: ocf - abs(capex))

    revenue_growth = _growth_rates_for(revenue_series)
    net_income_growth = _growth_rates_for(net_income_series)
    eps_growth = _growth_rates_for(eps_series)
    fcf_growth = _growth_rates_for(fcf_series)
    shares_growth = _growth_rates_for(shares_series)

    # Referenzdatum für alle "aktuellen" Kennzahlen dieses Berichts: neuestes
    # Umsatz-Periodenende, ersatzweise (falls Umsatz fehlt) das neueste
    # Nettogewinn-Periodenende — damit bleiben auch Berichte mit lückenhaften
    # Daten möglich, statt komplett leer zu sein (Auftrag §7: Konfidenz statt
    # Nullwertung).
    if revenue_series:
        latest_date = revenue_series[-1][0]
    elif net_income_series:
        latest_date = net_income_series[-1][0]
    else:
        latest_date = None

    gross_profit = value_at(Metric.GROSS_PROFIT, latest_date)
    operating_income = value_at(Metric.OPERATING_INCOME, latest_date)
    net_income = value_at(Metric.NET_INCOME, latest_date)
    revenue = value_at(Metric.REVENUE, latest_date)

    gross_margin_series = _combine(annual(Metric.GROSS_PROFIT), revenue_series, calc.margin)
    operating_margin_series = _combine(annual(Metric.OPERATING_INCOME), revenue_series, calc.margin)
    net_margin_series = _combine(net_income_series, revenue_series, calc.margin)

    margins = MarginProfile(
        latest_period_end=latest_date,
        gross_margin=calc.margin(gross_profit, revenue),
        operating_margin=calc.margin(operating_income, revenue),
        net_margin=calc.margin(net_income, revenue),
        gross_margin_stability=calc.margin_stability([v for _, v in gross_margin_series]),
        operating_margin_stability=calc.margin_stability([v for _, v in operating_margin_series]),
        net_margin_stability=calc.margin_stability([v for _, v in net_margin_series]),
    )

    equity = value_at(Metric.TOTAL_EQUITY, latest_date)
    equity_series = annual(Metric.TOTAL_EQUITY)
    equity_dates = [d for d, _ in equity_series]
    equity_prior: float | None = None
    if latest_date in equity_dates:
        idx = equity_dates.index(latest_date)
        if idx > 0:
            equity_prior = equity_series[idx - 1][1]
    average_equity = calc.average_of(equity_prior, equity)

    long_term_debt = value_at(Metric.LONG_TERM_DEBT, latest_date)
    short_term_debt = value_at(Metric.SHORT_TERM_DEBT, latest_date)
    total_debt: float | None = None
    if long_term_debt is not None or short_term_debt is not None:
        total_debt = (long_term_debt or 0.0) + (short_term_debt or 0.0)
    cash = value_at(Metric.CASH_AND_EQUIVALENTS, latest_date)

    invested_capital: float | None = None
    if total_debt is not None and equity is not None:
        invested_capital = total_debt + equity - (cash or 0.0)

    returns = ReturnsProfile(
        latest_period_end=latest_date,
        return_on_equity=calc.return_on_equity(net_income, average_equity),
        return_on_invested_capital=calc.return_on_invested_capital(
            operating_income, tax_rate=roic_tax_rate, invested_capital=invested_capital
        ),
        roic_tax_rate_assumption=roic_tax_rate,
    )

    current_assets = value_at(Metric.CURRENT_ASSETS, latest_date)
    current_liabilities = value_at(Metric.CURRENT_LIABILITIES, latest_date)
    capex = value_at(Metric.CAPEX, latest_date)
    ocf = value_at(Metric.OPERATING_CASH_FLOW, latest_date)

    cashflow = CashflowProfile(
        latest_period_end=latest_date,
        cash_conversion=calc.cash_conversion(ocf, net_income),
        capex_ratio=calc.capex_ratio(capex, revenue),
        working_capital=calc.working_capital(current_assets, current_liabilities),
    )

    depreciation_and_amortization = value_at(Metric.DEPRECIATION_AND_AMORTIZATION, latest_date)
    ebitda_value = calc.ebitda(operating_income, depreciation_and_amortization)
    net_debt_value = calc.net_debt(total_debt, cash) if total_debt is not None else None
    interest_expense = value_at(Metric.INTEREST_EXPENSE, latest_date)

    leverage = LeverageProfile(
        latest_period_end=latest_date,
        net_debt=net_debt_value,
        ebitda=ebitda_value,
        net_debt_to_ebitda=calc.net_debt_to_ebitda(net_debt_value, ebitda_value),
        interest_coverage=calc.interest_coverage(operating_income, interest_expense),
    )

    dividends_paid = value_at(Metric.DIVIDENDS_PAID, latest_date)
    shareholder = ShareholderProfile(
        latest_period_end=latest_date,
        dividend_payout_ratio=calc.dividend_payout_ratio(dividends_paid, net_income),
        shares_diluted_growth=shares_growth,
    )

    warning_signals = run_all_checks(session, entity)
    peers = find_peers(session, entity)

    scalar_fields: dict[str, float | None] = {
        "revenue_growth_1y": revenue_growth.horizon_1y,
        "revenue_growth_3y": revenue_growth.horizon_3y,
        "revenue_growth_5y": revenue_growth.horizon_5y,
        "revenue_growth_10y": revenue_growth.horizon_10y,
        "net_income_growth_1y": net_income_growth.horizon_1y,
        "net_income_growth_3y": net_income_growth.horizon_3y,
        "net_income_growth_5y": net_income_growth.horizon_5y,
        "net_income_growth_10y": net_income_growth.horizon_10y,
        "eps_diluted_growth_1y": eps_growth.horizon_1y,
        "eps_diluted_growth_3y": eps_growth.horizon_3y,
        "eps_diluted_growth_5y": eps_growth.horizon_5y,
        "eps_diluted_growth_10y": eps_growth.horizon_10y,
        "free_cash_flow_growth_1y": fcf_growth.horizon_1y,
        "free_cash_flow_growth_3y": fcf_growth.horizon_3y,
        "free_cash_flow_growth_5y": fcf_growth.horizon_5y,
        "free_cash_flow_growth_10y": fcf_growth.horizon_10y,
        "gross_margin": margins.gross_margin,
        "operating_margin": margins.operating_margin,
        "net_margin": margins.net_margin,
        "gross_margin_stability": margins.gross_margin_stability,
        "operating_margin_stability": margins.operating_margin_stability,
        "net_margin_stability": margins.net_margin_stability,
        "return_on_equity": returns.return_on_equity,
        "return_on_invested_capital": returns.return_on_invested_capital,
        "cash_conversion": cashflow.cash_conversion,
        "capex_ratio": cashflow.capex_ratio,
        "working_capital": cashflow.working_capital,
        "net_debt": leverage.net_debt,
        "ebitda": leverage.ebitda,
        "net_debt_to_ebitda": leverage.net_debt_to_ebitda,
        "interest_coverage": leverage.interest_coverage,
        "dividend_payout_ratio": shareholder.dividend_payout_ratio,
        "shares_diluted_growth_3y": shareholder.shares_diluted_growth.horizon_3y,
    }
    missing_fields = tuple(name for name, value in scalar_fields.items() if value is None)
    data_completeness = 1.0 - (len(missing_fields) / len(scalar_fields))

    return FundamentalsReport(
        entity_id=entity.id,
        entity_name=entity.name,
        generated_at_utc=utc_now(),
        as_of=reference,
        revenue_growth=revenue_growth,
        net_income_growth=net_income_growth,
        eps_diluted_growth=eps_growth,
        free_cash_flow_growth=fcf_growth,
        margins=margins,
        returns=returns,
        cashflow=cashflow,
        leverage=leverage,
        shareholder=shareholder,
        warning_signals=warning_signals,
        not_yet_implementable_signals=NOT_YET_IMPLEMENTABLE_SIGNALS,
        peers=peers,
        data_completeness=data_completeness,
        missing_fields=missing_fields,
    )
