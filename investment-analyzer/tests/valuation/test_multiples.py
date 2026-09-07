from __future__ import annotations

import pytest

from investment_analyzer.valuation import multiples as m


def test_market_capitalization() -> None:
    # 25 * 40 = 1000
    assert m.market_capitalization(25.0, 40.0) == pytest.approx(1000.0)


def test_market_capitalization_fehlende_werte() -> None:
    assert m.market_capitalization(None, 40.0) is None
    assert m.market_capitalization(25.0, None) is None


def test_enterprise_value() -> None:
    # 1000 + 350 - 150 = 1200
    assert m.enterprise_value(1000.0, 350.0, 150.0) == pytest.approx(1200.0)


def test_enterprise_value_fehlende_werte() -> None:
    assert m.enterprise_value(None, 350.0, 150.0) is None


def test_price_earnings_ratio() -> None:
    # 25 / 2.5 = 10
    assert m.price_earnings_ratio(25.0, 2.5) == pytest.approx(10.0)


def test_price_earnings_ratio_negativer_eps_liefert_none() -> None:
    assert m.price_earnings_ratio(25.0, -1.0) is None
    assert m.price_earnings_ratio(25.0, 0.0) is None


def test_ev_to_ebitda() -> None:
    # 1200 / 300 = 4
    assert m.ev_to_ebitda(1200.0, 300.0) == pytest.approx(4.0)


def test_ev_to_ebitda_negatives_ebitda_liefert_none() -> None:
    assert m.ev_to_ebitda(1200.0, -50.0) is None


def test_ev_to_ebit() -> None:
    # 1200 / 240 = 5
    assert m.ev_to_ebit(1200.0, 240.0) == pytest.approx(5.0)


def test_price_to_book() -> None:
    # 1000 / 800 = 1,25
    assert m.price_to_book(1000.0, 800.0) == pytest.approx(1.25)


def test_price_to_book_negatives_eigenkapital_liefert_none() -> None:
    assert m.price_to_book(1000.0, -50.0) is None


def test_price_to_free_cash_flow() -> None:
    # 1000 / 80 = 12,5
    assert m.price_to_free_cash_flow(1000.0, 80.0) == pytest.approx(12.5)


def test_price_to_free_cash_flow_negativer_fcf_liefert_none() -> None:
    assert m.price_to_free_cash_flow(1000.0, -10.0) is None


def test_free_cash_flow_yield() -> None:
    # 80 / 1000 = 8 %
    assert m.free_cash_flow_yield(80.0, 1000.0) == pytest.approx(0.08)


def test_free_cash_flow_yield_ohne_marktkap_liefert_none() -> None:
    assert m.free_cash_flow_yield(80.0, None) is None
    assert m.free_cash_flow_yield(80.0, 0.0) is None


def test_free_cash_flow_yield_ist_kehrwert_von_price_to_fcf() -> None:
    fcf, market_cap = 80.0, 1000.0
    p_fcf = m.price_to_free_cash_flow(market_cap, fcf)
    fcf_yield = m.free_cash_flow_yield(fcf, market_cap)
    assert p_fcf is not None and fcf_yield is not None
    assert p_fcf * fcf_yield == pytest.approx(1.0)
