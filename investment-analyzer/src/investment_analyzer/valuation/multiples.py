"""Bewertungsmultiplikatoren — reine Berechnungsfunktionen (Auftrag §6 „Bewertung").

Wie ``fundamentals/calculations.py``: keine Datenbank-/Netzwerkzugriffe,
keine geschätzten Ersatzwerte bei fehlenden Eingaben — jede Funktion
liefert ``None`` statt einer erfundenen Zahl, wenn eine benötigte
Eingabe fehlt oder der Nenner null/negativ ist (bei negativen Gewinnen
ist z. B. ein KGV nicht sinnvoll interpretierbar und wird nicht
ausgegeben).
"""

from __future__ import annotations

from investment_analyzer.fundamentals.calculations import safe_divide


def market_capitalization(price_per_share: float | None, shares_diluted: float | None) -> float | None:
    """Marktkapitalisierung = Kurs × verwässerte Aktienanzahl."""

    if price_per_share is None or shares_diluted is None:
        return None
    return price_per_share * shares_diluted


def enterprise_value(
    market_cap: float | None, total_debt: float | None, cash_and_equivalents: float | None
) -> float | None:
    """EV = Marktkapitalisierung + Gesamtschulden − liquide Mittel."""

    if market_cap is None or total_debt is None or cash_and_equivalents is None:
        return None
    return market_cap + total_debt - cash_and_equivalents


def price_earnings_ratio(price_per_share: float | None, eps_diluted: float | None) -> float | None:
    """KGV = Kurs / verwässertes Ergebnis je Aktie. Bei negativem EPS nicht aussagekräftig -> None."""

    if eps_diluted is None or eps_diluted <= 0:
        return None
    return safe_divide(price_per_share, eps_diluted)


def ev_to_ebitda(ev: float | None, ebitda: float | None) -> float | None:
    """EV/EBITDA. Bei negativem/Null-EBITDA nicht aussagekräftig -> None."""

    if ebitda is None or ebitda <= 0:
        return None
    return safe_divide(ev, ebitda)


def ev_to_ebit(ev: float | None, ebit: float | None) -> float | None:
    """EV/EBIT (EBIT hier als operatives Ergebnis genähert, wie in fundamentals/report.py)."""

    if ebit is None or ebit <= 0:
        return None
    return safe_divide(ev, ebit)


def price_to_book(market_cap: float | None, total_equity: float | None) -> float | None:
    """KBV = Marktkapitalisierung / Eigenkapital. Bei negativem Eigenkapital nicht aussagekräftig -> None."""

    if total_equity is None or total_equity <= 0:
        return None
    return safe_divide(market_cap, total_equity)


def price_to_free_cash_flow(market_cap: float | None, free_cash_flow: float | None) -> float | None:
    """Kurs/Free-Cashflow = Marktkapitalisierung / freier Cashflow."""

    if free_cash_flow is None or free_cash_flow <= 0:
        return None
    return safe_divide(market_cap, free_cash_flow)


def free_cash_flow_yield(free_cash_flow: float | None, market_cap: float | None) -> float | None:
    """FCF-Rendite = freier Cashflow / Marktkapitalisierung (Kehrwert von Kurs/FCF)."""

    if market_cap is None or market_cap <= 0:
        return None
    return safe_divide(free_cash_flow, market_cap)
