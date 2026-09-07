from __future__ import annotations

import pytest

from investment_analyzer.portfolio.position_sizing import position_size_band


def test_position_size_band_ohne_bestehende_position() -> None:
    band = position_size_band(portfolio_value=100_000.0, max_position_pct=5.0)
    assert band.max_position_value == 5_000.0
    assert band.min_additional_value == 0.0
    assert band.max_additional_value == 5_000.0
    assert band.max_additional_shares is None


def test_position_size_band_mit_bestehender_position() -> None:
    band = position_size_band(
        portfolio_value=100_000.0, max_position_pct=5.0, current_position_value=2_000.0
    )
    assert band.max_additional_value == 3_000.0


def test_position_size_band_bereits_ueber_limit_liefert_null_statt_negativ() -> None:
    band = position_size_band(
        portfolio_value=100_000.0, max_position_pct=5.0, current_position_value=10_000.0
    )
    assert band.max_additional_value == 0.0


def test_position_size_band_mit_kurs_liefert_stueckzahl() -> None:
    band = position_size_band(
        portfolio_value=100_000.0, max_position_pct=5.0, latest_price=50.0
    )
    assert band.max_additional_shares == 100.0
    assert band.min_additional_shares == 0.0


def test_position_size_band_enthaelt_unverbindlichkeitshinweis() -> None:
    band = position_size_band(portfolio_value=10_000.0, max_position_pct=10.0)
    assert "Unverbindlich" in band.note
    assert "keine Kaufempfehlung" in band.note


def test_position_size_band_ungueltiges_portfolio_value() -> None:
    with pytest.raises(ValueError, match="portfolio_value"):
        position_size_band(portfolio_value=0.0, max_position_pct=5.0)


def test_position_size_band_ungueltiges_max_position_pct() -> None:
    with pytest.raises(ValueError, match="max_position_pct"):
        position_size_band(portfolio_value=1000.0, max_position_pct=0.0)
    with pytest.raises(ValueError, match="max_position_pct"):
        position_size_band(portfolio_value=1000.0, max_position_pct=101.0)
