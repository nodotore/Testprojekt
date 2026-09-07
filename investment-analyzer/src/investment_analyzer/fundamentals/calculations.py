"""Reine Berechnungsfunktionen für Fundamentalkennzahlen (Auftrag §6).

Alle Funktionen hier sind bewusst **rein** (keine Datenbank-, Netzwerk-
oder sonstigen Seiteneffekte) und operieren auf einfachen Zahlen bzw.
chronologisch aufsteigend sortierten Zeitreihen. Das macht sie direkt
und deterministisch mit Handrechnungen vergleichbar (Auftrag §15:
„DCF und Kernkennzahlen gegen Handrechnungen geprüft").

Grundprinzip: **Keine Kennzahl wird geschätzt, wenn eine Eingabe fehlt.**
Fehlt ein benötigter Wert, liefert die Funktion ``None`` statt eines
geratenen Ersatzwerts (Auftrag §11: „Wurde eine Annahme als Tatsache
formuliert?"). Wo eine Annahme unvermeidbar ist (z. B. ein Steuersatz für
ROIC), ist sie ein expliziter, unbenannter Pflichtparameter ohne
stillen Default — der Aufrufer muss die Annahme bewusst treffen und
sichtbar dokumentieren (siehe ``fundamentals/report.py``).
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import date

#: Ein Datenpunkt (Berichtsperiode, Wert), aufsteigend nach Datum in Serien erwartet.
TimeSeries = Sequence[tuple[date, float]]


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    """Division, die bei fehlenden Werten oder Division durch Null ``None`` liefert."""

    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def cagr(begin_value: float | None, end_value: float | None, years: float) -> float | None:
    """Compound Annual Growth Rate: ``(end/begin) ** (1/years) - 1``.

    Liefert ``None``, wenn ``years`` nicht positiv ist, ein Wert fehlt,
    oder ``begin_value``/``end_value`` nicht positiv ist (bei
    Vorzeichenwechsel oder Nulldurchgang ist eine Wachstumsrate im
    strengen Sinn nicht definiert — wird nicht approximiert).
    """

    if years <= 0:
        return None
    if begin_value is None or end_value is None:
        return None
    if begin_value <= 0 or end_value <= 0:
        return None
    return (end_value / begin_value) ** (1.0 / years) - 1.0


def growth_rate(series: TimeSeries, *, horizon_years: int) -> float | None:
    """CAGR über ``horizon_years`` Jahre, gemessen vom jeweils letzten Wert der Serie.

    ``series`` sollte einen Wert je Geschäftsjahr enthalten (z. B. durch
    das Zeitreihen-Repository auf ``fiscal_period == "FY"`` gefiltert,
    siehe ``fundamentals/series.py``). Der Vorjahreswert wird über das
    Kalenderjahr des Periodenendes gesucht (``end.year - horizon_years``);
    wird kein passendes Jahr gefunden, liefert die Funktion ``None``
    statt eine Rate über eine andere Zeitspanne vorzutäuschen.
    """

    if not series:
        return None
    sorted_series = sorted(series, key=lambda item: item[0])
    end_date, end_value = sorted_series[-1]
    target_year = end_date.year - horizon_years
    for period_date, value in sorted_series:
        if period_date.year == target_year:
            return cagr(value, end_value, float(horizon_years))
    return None


def margin(numerator: float | None, denominator: float | None) -> float | None:
    """Allgemeine Margen-/Quotenberechnung (z. B. Bruttomarge = Bruttogewinn/Umsatz)."""

    return safe_divide(numerator, denominator)


def margin_stability(margins: Sequence[float | None]) -> float | None:
    """Stichproben-Standardabweichung einer Margen-Zeitreihe (Stabilitätsmaß).

    Kleinere Werte bedeuten stabilere Margen. Liefert ``None`` bei
    weniger als zwei tatsächlich vorhandenen (nicht ``None``) Werten.
    """

    values = [m for m in margins if m is not None]
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def average_of(begin: float | None, end: float | None) -> float | None:
    """Mittelwert zweier optionaler Werte (z. B. Anfangs-/Endbestand für ROE-Nenner)."""

    if begin is None and end is None:
        return None
    if begin is None:
        return end
    if end is None:
        return begin
    return (begin + end) / 2.0


def return_on_equity(net_income: float | None, average_equity: float | None) -> float | None:
    """ROE = Nettogewinn / durchschnittliches Eigenkapital."""

    return safe_divide(net_income, average_equity)


def return_on_invested_capital(
    operating_income: float | None,
    *,
    tax_rate: float,
    invested_capital: float | None,
) -> float | None:
    """ROIC ≈ NOPAT / investiertes Kapital, NOPAT = operatives Ergebnis × (1 − Steuersatz).

    ``invested_capital`` wird üblicherweise als Gesamtschulden + Eigenkapital
    − liquide Mittel approximiert (siehe ``report.py``). ``tax_rate`` ist
    eine explizite Annahme ohne stillen Default (Auftrag §11) — Aufrufer
    müssen ihn bewusst wählen und die Herkunft dokumentieren.
    """

    if operating_income is None or invested_capital is None or invested_capital == 0:
        return None
    nopat = operating_income * (1.0 - tax_rate)
    return nopat / invested_capital


def cash_conversion(operating_cash_flow: float | None, net_income: float | None) -> float | None:
    """Cash Conversion = operativer Cashflow / Nettogewinn (Auftrag §6)."""

    return safe_divide(operating_cash_flow, net_income)


def capex_ratio(capex: float | None, revenue: float | None) -> float | None:
    """Investitionsquote = |Capex| / Umsatz. Capex wird in Cashflow-Statements

    häufig als negativer Auszahlungsbetrag geführt — der Betrag (nicht das
    Vorzeichen) ist hier relevant.
    """

    if capex is None:
        return None
    return safe_divide(abs(capex), revenue)


def working_capital(current_assets: float | None, current_liabilities: float | None) -> float | None:
    """Working Capital = kurzfristige Vermögenswerte − kurzfristige Verbindlichkeiten."""

    if current_assets is None or current_liabilities is None:
        return None
    return current_assets - current_liabilities


def ebitda(
    operating_income: float | None, depreciation_and_amortization: float | None
) -> float | None:
    """EBITDA ≈ operatives Ergebnis + Abschreibungen (Auftrag §6-Näherung, dokumentiert).

    Ohne explizit gemeldete Abschreibungssumme wird EBITDA NICHT
    geschätzt (liefert ``None``) — eine grobe Annäherung ohne diese
    Eingabe wäre eine unbelegte Zahl (Auftrag §11).
    """

    if operating_income is None or depreciation_and_amortization is None:
        return None
    return operating_income + depreciation_and_amortization


def net_debt(total_debt: float | None, cash_and_equivalents: float | None) -> float | None:
    """Nettoverschuldung = Gesamtschulden − liquide Mittel."""

    if total_debt is None or cash_and_equivalents is None:
        return None
    return total_debt - cash_and_equivalents


def net_debt_to_ebitda(net_debt_value: float | None, ebitda_value: float | None) -> float | None:
    """Nettoverbindlichkeiten/EBITDA (Auftrag §6)."""

    return safe_divide(net_debt_value, ebitda_value)


def interest_coverage(ebit_value: float | None, interest_expense: float | None) -> float | None:
    """Zinsdeckung = EBIT / Zinsaufwand. EBIT wird hier als operatives Ergebnis genähert."""

    return safe_divide(ebit_value, interest_expense)


def dividend_payout_ratio(dividends_paid: float | None, net_income: float | None) -> float | None:
    """Ausschüttungsquote = |gezahlte Dividenden| / Nettogewinn (Dividendenqualität, Auftrag §6)."""

    if dividends_paid is None:
        return None
    return safe_divide(abs(dividends_paid), net_income)


def share_count_growth(series: TimeSeries, *, horizon_years: int) -> float | None:
    """CAGR der verwässerten Aktienanzahl — positiv bedeutet Verwässerung (Auftrag §6)."""

    return growth_rate(series, horizon_years=horizon_years)
