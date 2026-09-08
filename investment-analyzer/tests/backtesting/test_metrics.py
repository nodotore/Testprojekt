from __future__ import annotations

import pytest

from investment_analyzer.backtesting.metrics import (
    annualized_volatility,
    cagr,
    sharpe_ratio,
    sortino_ratio,
    turnover,
)


def test_cagr_exaktes_beispiel() -> None:
    # (1.21)^(1/2) - 1 = 1.1 - 1 = 0.10 exakt, da 1.1^2 = 1.21
    assert cagr(0.21, years=2) == pytest.approx(0.10)


def test_cagr_negative_gesamtrendite() -> None:
    # (0.81)^(1/2) - 1 = 0.9 - 1 = -0.10
    assert cagr(-0.19, years=2) == pytest.approx(-0.10)


def test_cagr_totalverlust_liefert_none() -> None:
    assert cagr(-1.0, years=2) is None


def test_cagr_ungueltige_jahre_liefert_none() -> None:
    assert cagr(0.1, years=0) is None
    assert cagr(0.1, years=-1) is None


def test_annualized_volatility_konstante_reihe_ist_null() -> None:
    assert annualized_volatility([0.02, 0.02, 0.02]) == pytest.approx(0.0)


def test_annualized_volatility_exaktes_beispiel() -> None:
    # pstdev([0.01, -0.01, 0.01, -0.01]) = 0.01 (Mittelwert 0, jede Abweichung 0.01)
    result = annualized_volatility([0.01, -0.01, 0.01, -0.01], periods_per_year=12)
    assert result == pytest.approx(0.01 * (12**0.5))


def test_annualized_volatility_zu_wenig_perioden() -> None:
    assert annualized_volatility([0.01]) is None
    assert annualized_volatility([]) is None


def test_sharpe_ratio_exaktes_beispiel() -> None:
    # Renditen [0.01, 0.03], Mittel 0.02, pstdev = 0.01
    result = sharpe_ratio([0.01, 0.03], periods_per_year=12)
    assert result == pytest.approx((0.02 / 0.01) * (12**0.5))


def test_sharpe_ratio_ohne_volatilitaet_liefert_none() -> None:
    assert sharpe_ratio([0.02, 0.02, 0.02]) is None


def test_sharpe_ratio_zu_wenig_perioden() -> None:
    assert sharpe_ratio([0.02]) is None


def test_sharpe_ratio_beruecksichtigt_risikofreien_zins() -> None:
    result_ohne = sharpe_ratio([0.02, 0.04])
    result_mit = sharpe_ratio([0.02, 0.04], risk_free_rate_per_period=0.01)
    assert result_mit != result_ohne


def test_sortino_ratio_nur_aufwaertsrenditen_liefert_none() -> None:
    # Keine negativen Überschussrenditen -> downside_deviation = 0
    assert sortino_ratio([0.01, 0.03]) is None


def test_sortino_ratio_exaktes_beispiel() -> None:
    # Renditen [-0.02, 0.04], Mittel 0.01; downside = [-0.02, 0.0], pstdev = 0.01
    result = sortino_ratio([-0.02, 0.04], periods_per_year=12)
    assert result == pytest.approx((0.01 / 0.01) * (12**0.5))


def test_turnover_unveraendertes_portfolio_ist_null() -> None:
    assert turnover(["A", "B"], ["A", "B"]) == pytest.approx(0.0)


def test_turnover_komplett_neues_portfolio_ist_eins() -> None:
    assert turnover(["A", "B"], ["C", "D"]) == pytest.approx(1.0)


def test_turnover_teilweise_wechsel() -> None:
    # added={C}=1, removed={A}=1, avg_size=(2+2)/2=2 -> (1+1)/(2*2)=0.5
    assert turnover(["A", "B"], ["B", "C"]) == pytest.approx(0.5)


def test_turnover_beide_leer_ist_null() -> None:
    assert turnover([], []) == pytest.approx(0.0)
