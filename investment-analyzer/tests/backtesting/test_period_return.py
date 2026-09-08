from __future__ import annotations

import pytest

from investment_analyzer.backtesting.period_return import (
    compute_period_return,
    estimate_dividends_per_share,
)


def test_estimate_dividends_per_share_teilt_korrekt() -> None:
    assert estimate_dividends_per_share(200.0, 100.0) == 2.0


def test_estimate_dividends_per_share_ohne_dividende_ist_none() -> None:
    assert estimate_dividends_per_share(None, 100.0) is None


def test_estimate_dividends_per_share_ohne_aktienanzahl_ist_none() -> None:
    assert estimate_dividends_per_share(200.0, None) is None


def test_estimate_dividends_per_share_bei_null_aktien_ist_none() -> None:
    assert estimate_dividends_per_share(200.0, 0.0) is None


def test_compute_period_return_reine_kurssteigerung() -> None:
    result = compute_period_return(price_start=100.0, price_end=110.0)
    assert result.gross_return == pytest.approx(0.10)
    assert result.net_return == pytest.approx(0.10)


def test_compute_period_return_mit_dividende_und_kosten() -> None:
    # (110 - 100 + 2) / 100 = 0.12 brutto; (1.12 * 0.99) - 1 = 0.1088 netto
    result = compute_period_return(
        price_start=100.0, price_end=110.0, dividends_per_share=2.0, transaction_cost_pct=0.01
    )
    assert result.gross_return == pytest.approx(0.12)
    assert result.net_return == pytest.approx(0.1088)


def test_compute_period_return_kursverlust() -> None:
    result = compute_period_return(price_start=100.0, price_end=80.0)
    assert result.gross_return == pytest.approx(-0.20)


def test_compute_period_return_totalverlust() -> None:
    result = compute_period_return(price_start=100.0, price_end=0.0)
    assert result.gross_return == pytest.approx(-1.0)


def test_compute_period_return_ungueltiger_price_start() -> None:
    with pytest.raises(ValueError, match="price_start"):
        compute_period_return(price_start=0.0, price_end=100.0)


def test_compute_period_return_negativer_price_end() -> None:
    with pytest.raises(ValueError, match="price_end"):
        compute_period_return(price_start=100.0, price_end=-1.0)


def test_compute_period_return_negative_dividende() -> None:
    with pytest.raises(ValueError, match="dividends_per_share"):
        compute_period_return(price_start=100.0, price_end=100.0, dividends_per_share=-1.0)


def test_compute_period_return_ungueltige_transaktionskosten() -> None:
    with pytest.raises(ValueError, match="transaction_cost_pct"):
        compute_period_return(price_start=100.0, price_end=100.0, transaction_cost_pct=1.0)
    with pytest.raises(ValueError, match="transaction_cost_pct"):
        compute_period_return(price_start=100.0, price_end=100.0, transaction_cost_pct=-0.01)
