"""Handrechnungs-Tests für den Fundamentalkennzahlen-Berechnungskern (Auftrag §15).

Alle Eingabewerte sind bewusst einfache, von Hand nachrechenbare Zahlen
(keine realen Unternehmensdaten — siehe PROGRESS.md/NEXT_STEPS.md für
den Hinweis zur noch ausstehenden Verifikation an drei realen
Unternehmen, die mangels Internetzugang in dieser Sandbox nicht möglich
war). Jeder Testfall dokumentiert die Handrechnung im Kommentar.
"""

from __future__ import annotations

from datetime import date

import pytest

from investment_analyzer.fundamentals import calculations as calc


def test_cagr_zehn_prozent_ueber_drei_jahre() -> None:
    # 1.1^3 = 1.331 exakt -> CAGR = 10 %
    assert calc.cagr(100.0, 133.1, 3) == pytest.approx(0.10, abs=1e-9)


def test_cagr_negative_jahre_liefert_none() -> None:
    assert calc.cagr(100.0, 110.0, 0) is None
    assert calc.cagr(100.0, 110.0, -2) is None


def test_cagr_fehlende_werte_liefern_none() -> None:
    assert calc.cagr(None, 100.0, 3) is None
    assert calc.cagr(100.0, None, 3) is None


def test_cagr_vorzeichenwechsel_liefert_none_statt_falscher_zahl() -> None:
    assert calc.cagr(-50.0, 100.0, 2) is None
    assert calc.cagr(100.0, 0.0, 2) is None


def test_growth_rate_findet_horizont_ueber_kalenderjahr() -> None:
    serie = [
        (date(2020, 12, 31), 100.0),
        (date(2021, 12, 31), 110.0),
        (date(2023, 12, 31), 133.1),
    ]
    # Letzter Wert 2023 = 133,1; Wert 2020 = 100 -> CAGR über 3 Jahre = 10 %
    assert calc.growth_rate(serie, horizon_years=3) == pytest.approx(0.10, abs=1e-9)


def test_growth_rate_ohne_passendes_jahr_liefert_none() -> None:
    serie = [(date(2020, 12, 31), 100.0), (date(2023, 12, 31), 133.1)]
    # Kein Wert für 2022 vorhanden -> 1-Jahres-Wachstum darf nicht erfunden werden
    assert calc.growth_rate(serie, horizon_years=1) is None


def test_growth_rate_leere_serie() -> None:
    assert calc.growth_rate([], horizon_years=1) is None


def test_margin_einfache_division() -> None:
    # Bruttomarge = 25 / 100 = 25 %
    assert calc.margin(25.0, 100.0) == pytest.approx(0.25)


def test_margin_division_durch_null_liefert_none() -> None:
    assert calc.margin(25.0, 0.0) is None


def test_margin_stability_konstante_margen_ergibt_null() -> None:
    assert calc.margin_stability([0.2, 0.2, 0.2]) == pytest.approx(0.0)


def test_margin_stability_mit_streuung() -> None:
    # Werte 0.2 und 0.3, Mittelwert 0.25, Stichprobenvarianz = (0.0025+0.0025)/1 = 0.005
    # Stichproben-Standardabweichung = sqrt(0.005) ≈ 0.0707107
    assert calc.margin_stability([0.2, None, 0.3]) == pytest.approx(0.07071067811865475)


def test_margin_stability_zu_wenig_werte_liefert_none() -> None:
    assert calc.margin_stability([0.2]) is None
    assert calc.margin_stability([]) is None


def test_average_of_beide_werte() -> None:
    assert calc.average_of(100.0, 200.0) == pytest.approx(150.0)


def test_average_of_ein_fehlender_wert() -> None:
    assert calc.average_of(None, 200.0) == pytest.approx(200.0)
    assert calc.average_of(100.0, None) == pytest.approx(100.0)
    assert calc.average_of(None, None) is None


def test_return_on_equity() -> None:
    # ROE = 50 / 250 = 20 %
    assert calc.return_on_equity(50.0, 250.0) == pytest.approx(0.20)


def test_return_on_invested_capital() -> None:
    # NOPAT = 100 * (1 - 0.21) = 79; ROIC = 79 / 500 = 15,8 %
    result = calc.return_on_invested_capital(100.0, tax_rate=0.21, invested_capital=500.0)
    assert result == pytest.approx(0.158)


def test_return_on_invested_capital_ohne_invested_capital() -> None:
    assert calc.return_on_invested_capital(100.0, tax_rate=0.21, invested_capital=None) is None
    assert calc.return_on_invested_capital(100.0, tax_rate=0.21, invested_capital=0.0) is None


def test_cash_conversion() -> None:
    # 90 / 100 = 0,9
    assert calc.cash_conversion(90.0, 100.0) == pytest.approx(0.9)


def test_capex_ratio_negatives_capex_wird_als_betrag_behandelt() -> None:
    # |−20| / 200 = 10 %
    assert calc.capex_ratio(-20.0, 200.0) == pytest.approx(0.10)


def test_working_capital() -> None:
    assert calc.working_capital(300.0, 180.0) == pytest.approx(120.0)


def test_working_capital_fehlende_werte() -> None:
    assert calc.working_capital(None, 180.0) is None


def test_ebitda_mit_abschreibungen() -> None:
    assert calc.ebitda(100.0, 30.0) == pytest.approx(130.0)


def test_ebitda_ohne_abschreibungen_liefert_none_statt_schaetzung() -> None:
    assert calc.ebitda(100.0, None) is None


def test_net_debt() -> None:
    assert calc.net_debt(400.0, 150.0) == pytest.approx(250.0)


def test_net_debt_to_ebitda() -> None:
    # 250 / 130 ≈ 1,9231
    assert calc.net_debt_to_ebitda(250.0, 130.0) == pytest.approx(250.0 / 130.0)


def test_interest_coverage() -> None:
    assert calc.interest_coverage(100.0, 20.0) == pytest.approx(5.0)


def test_dividend_payout_ratio() -> None:
    # |−30| / 100 = 30 %
    assert calc.dividend_payout_ratio(-30.0, 100.0) == pytest.approx(0.30)


def test_share_count_growth_verwaesserung() -> None:
    serie = [(date(2020, 12, 31), 1000.0), (date(2023, 12, 31), 1157.625)]
    # 1,05^3 = 1,157625 exakt -> 5 % Verwässerung p. a.
    assert calc.share_count_growth(serie, horizon_years=3) == pytest.approx(0.05, abs=1e-9)


def test_safe_divide_direkt() -> None:
    assert calc.safe_divide(10.0, 4.0) == pytest.approx(2.5)
    assert calc.safe_divide(10.0, None) is None
    assert calc.safe_divide(None, 4.0) is None
    assert calc.safe_divide(10.0, 0.0) is None
