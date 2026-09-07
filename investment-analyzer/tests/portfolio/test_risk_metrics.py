from __future__ import annotations

from datetime import date

import pytest

from investment_analyzer.portfolio.risk_metrics import (
    correlation_matrix,
    max_drawdown,
    pairwise_correlation,
)


def test_max_drawdown_zu_wenig_punkte() -> None:
    result = max_drawdown([(date(2026, 1, 1), 100.0)])
    assert result.computable is False
    assert result.max_drawdown_pct is None


def test_max_drawdown_monoton_steigend_ist_null() -> None:
    series = [(date(2026, 1, 1), 100.0), (date(2026, 1, 2), 110.0), (date(2026, 1, 3), 120.0)]
    result = max_drawdown(series)
    assert result.computable is True
    assert result.max_drawdown_pct == 0.0


def test_max_drawdown_einfacher_rueckgang() -> None:
    series = [(date(2026, 1, 1), 100.0), (date(2026, 1, 2), 80.0)]
    result = max_drawdown(series)
    assert result.computable is True
    assert result.max_drawdown_pct == -0.2
    assert result.peak_date == date(2026, 1, 1)
    assert result.trough_date == date(2026, 1, 2)


def test_max_drawdown_findet_groessten_rueckgang_ueber_mehrere_phasen() -> None:
    # 100 -> 90 (-10%) -> 150 (neuer Höchststand) -> 90 (-40%, das Maximum)
    series = [
        (date(2026, 1, 1), 100.0),
        (date(2026, 1, 2), 90.0),
        (date(2026, 1, 3), 150.0),
        (date(2026, 1, 4), 90.0),
    ]
    result = max_drawdown(series)
    assert result.max_drawdown_pct == -0.4
    assert result.peak_date == date(2026, 1, 3)
    assert result.trough_date == date(2026, 1, 4)


def test_max_drawdown_unsortierte_eingabe_wird_sortiert() -> None:
    series = [(date(2026, 1, 2), 80.0), (date(2026, 1, 1), 100.0)]
    result = max_drawdown(series)
    assert result.max_drawdown_pct == -0.2


def test_pairwise_correlation_zu_wenig_ueberlappung() -> None:
    a = [(date(2026, 1, 1), 100.0), (date(2026, 1, 2), 101.0)]
    b = [(date(2026, 1, 1), 50.0), (date(2026, 1, 2), 51.0)]
    result = pairwise_correlation(a, b)
    assert result.computable is False
    assert result.overlapping_points == 2


def test_pairwise_correlation_perfekt_positiv() -> None:
    # Identische relative Bewegungen -> Korrelation exakt 1.0
    a = [(date(2026, 1, i), 100.0 * (1.0 + 0.01 * i)) for i in range(1, 6)]
    b = [(date(2026, 1, i), 50.0 * (1.0 + 0.01 * i)) for i in range(1, 6)]
    result = pairwise_correlation(a, b)
    assert result.computable is True
    assert result.correlation is not None
    assert result.correlation == pytest.approx(1.0)


def test_pairwise_correlation_perfekt_negativ() -> None:
    # b's Tagesrenditen sind exakt das Negative von a's Tagesrenditen
    # (per Konstruktion) -> Korrelation exakt -1.0.
    returns = [0.01, -0.02, 0.03, -0.01, 0.02]
    prices_a = [100.0]
    prices_b = [100.0]
    for r in returns:
        prices_a.append(prices_a[-1] * (1 + r))
        prices_b.append(prices_b[-1] * (1 - r))
    a = [(date(2026, 1, i + 1), price) for i, price in enumerate(prices_a)]
    b = [(date(2026, 1, i + 1), price) for i, price in enumerate(prices_b)]

    result = pairwise_correlation(a, b)
    assert result.computable is True
    assert result.correlation == pytest.approx(-1.0)


def test_pairwise_correlation_konstante_reihe_ist_nicht_berechenbar() -> None:
    a = [(date(2026, 1, i), 100.0) for i in range(1, 6)]
    b = [(date(2026, 1, i), 50.0 + i) for i in range(1, 6)]
    result = pairwise_correlation(a, b)
    assert result.computable is False
    assert "Varianz" in (result.note or "")


def test_correlation_matrix_liefert_nur_oberes_dreieck() -> None:
    series_map = {
        "a": [(date(2026, 1, i), 100.0 + i) for i in range(1, 6)],
        "b": [(date(2026, 1, i), 200.0 + 2 * i) for i in range(1, 6)],
        "c": [(date(2026, 1, i), 300.0 - i) for i in range(1, 6)],
    }
    matrix = correlation_matrix(series_map)
    assert set(matrix.keys()) == {("a", "b"), ("a", "c"), ("b", "c")}
    assert ("b", "a") not in matrix
