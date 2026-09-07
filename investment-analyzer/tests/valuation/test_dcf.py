"""Handrechnungs-Tests für das DCF-Modell (Auftrag §15).

Die Basisfälle nutzen bewusst ``revenue_growth_rate == wacc``, wodurch
sich jedes projizierte Jahr exakt zu ``base_revenue * fcf_margin``
abdiskontiert (siehe Kommentar in ``test_run_dcf_...``) — das macht die
Summe der abgezinsten Cashflows von Hand ohne Taschenrechner-Rundung
nachrechenbar.
"""

from __future__ import annotations

from datetime import date

import pytest

from investment_analyzer.valuation.dcf import (
    DCFAssumptions,
    DCFInputs,
    build_sensitivity_matrix,
    run_dcf,
    safety_margin,
)


def _basis_annahmen(**overrides: float) -> DCFAssumptions:
    werte = {
        "revenue_growth_rate": 0.10,
        "fcf_margin": 0.10,
        "wacc": 0.10,
        "terminal_growth_rate": 0.02,
        "projection_years": 3,
    }
    werte.update(overrides)
    return DCFAssumptions(**werte)  # type: ignore[arg-type]


def _basis_inputs(**overrides: object) -> DCFInputs:
    werte: dict[str, object] = {
        "base_revenue": 1000.0,
        "as_of": date(2024, 1, 1),
        "net_debt": 75.0,
        "shares_diluted": 100.0,
    }
    werte.update(overrides)
    return DCFInputs(**werte)  # type: ignore[arg-type]


def test_run_dcf_handrechnung_mit_wachstum_gleich_wacc() -> None:
    """Wenn revenue_growth_rate == wacc, kürzt sich (1+g)^n / (1+wacc)^n zu 1 —
    jedes Jahr diskontiert exakt auf base_revenue * fcf_margin zurück:

    Jahr 1: Umsatz 1100, FCF 110, abgezinst 110/1,1   = 100
    Jahr 2: Umsatz 1210, FCF 121, abgezinst 121/1,21  = 100
    Jahr 3: Umsatz 1331, FCF 133,1, abgezinst 133,1/1,331 = 100
    Summe abgezinster FCF = 300

    Terminalwert: FCF_terminal = 133,1 * 1,02 = 135,762
    Terminal Value = 135,762 / (0,10 - 0,02) = 1697,025
    abgezinst über 3 Jahre = 1697,025 / 1,331 = 1275,0

    Enterprise Value = 300 + 1275 = 1575
    Equity Value = 1575 - 75 (Nettoschulden) = 1500
    Fair Value je Aktie = 1500 / 100 = 15,0
    """

    result = run_dcf(_basis_annahmen(), _basis_inputs())

    assert result is not None
    assert result.projected_fcf == pytest.approx((110.0, 121.0, 133.1))
    assert result.discounted_fcf == pytest.approx((100.0, 100.0, 100.0))
    assert result.terminal_value_discounted == pytest.approx(1275.0)
    assert result.enterprise_value == pytest.approx(1575.0)
    assert result.equity_value == pytest.approx(1500.0)
    assert result.fair_value_per_share == pytest.approx(15.0)


def test_run_dcf_ohne_nettoschulden_oder_aktienzahl_liefert_keinen_fair_value_per_share() -> None:
    result = run_dcf(_basis_annahmen(), _basis_inputs(net_debt=None, shares_diluted=None))
    assert result is not None
    assert result.equity_value is None
    assert result.fair_value_per_share is None
    assert result.enterprise_value == pytest.approx(1575.0)  # EV bleibt trotzdem berechenbar


def test_run_dcf_wacc_kleiner_gleich_terminalwachstum_liefert_none() -> None:
    assert run_dcf(_basis_annahmen(wacc=0.02, terminal_growth_rate=0.02), _basis_inputs()) is None
    assert run_dcf(_basis_annahmen(wacc=0.01, terminal_growth_rate=0.02), _basis_inputs()) is None


def test_run_dcf_negativer_oder_null_wacc_liefert_none() -> None:
    assert run_dcf(_basis_annahmen(wacc=0.0), _basis_inputs()) is None
    assert run_dcf(_basis_annahmen(wacc=-0.05), _basis_inputs()) is None


def test_run_dcf_ungueltige_projektionsjahre_liefert_none() -> None:
    assert run_dcf(_basis_annahmen(projection_years=0), _basis_inputs()) is None


def test_drei_szenarien_ergeben_eine_bewertungsspanne() -> None:
    """Basis-, optimistisches und pessimistisches Szenario müssen sich sinnvoll ordnen
    (Auftrag §6: Bewertungsspanne statt Einzelkurs)."""

    inputs = _basis_inputs()
    basis = run_dcf(_basis_annahmen(), inputs, scenario_name="Basis")
    optimistisch = run_dcf(
        _basis_annahmen(revenue_growth_rate=0.15, fcf_margin=0.12), inputs, scenario_name="Optimistisch"
    )
    pessimistisch = run_dcf(
        _basis_annahmen(revenue_growth_rate=0.05, fcf_margin=0.08), inputs, scenario_name="Pessimistisch"
    )

    assert basis is not None and optimistisch is not None and pessimistisch is not None
    assert pessimistisch.fair_value_per_share is not None
    assert basis.fair_value_per_share is not None
    assert optimistisch.fair_value_per_share is not None
    assert pessimistisch.fair_value_per_share < basis.fair_value_per_share < optimistisch.fair_value_per_share


def test_safety_margin_handrechnung() -> None:
    # (15 - 12) / 15 = 20 %
    assert safety_margin(15.0, 12.0) == pytest.approx(0.20)


def test_safety_margin_kurs_ueber_fairem_wert_ist_negativ() -> None:
    # (15 - 18) / 15 = -20 % -> keine Sicherheitsmarge, Kurs teurer als unteres Band
    assert safety_margin(15.0, 18.0) == pytest.approx(-0.20)


def test_safety_margin_fehlende_werte_liefert_none() -> None:
    assert safety_margin(None, 12.0) is None
    assert safety_margin(15.0, None) is None
    assert safety_margin(0.0, 12.0) is None
    assert safety_margin(-5.0, 12.0) is None


def test_sensitivity_matrix_wachstum_x_wacc() -> None:
    inputs = _basis_inputs()
    matrix = build_sensitivity_matrix(
        _basis_annahmen(),
        inputs,
        row_parameter="revenue_growth_rate",
        row_values=[0.08, 0.10, 0.12],
        column_parameter="wacc",
        column_values=[0.09, 0.10, 0.11],
    )

    assert matrix.row_values == (0.08, 0.10, 0.12)
    assert matrix.column_values == (0.09, 0.10, 0.11)
    assert len(matrix.fair_value_per_share) == 3
    assert all(len(row) == 3 for row in matrix.fair_value_per_share)

    # Mittelwert der Matrix (Zeile 2, Spalte 2) entspricht exakt dem Basisfall:
    assert matrix.fair_value_per_share[1][1] == pytest.approx(15.0)

    # Höheres Wachstum bei gleichem WACC -> höherer fairer Wert je Aktie:
    niedrig = matrix.fair_value_per_share[0][1]
    hoch = matrix.fair_value_per_share[2][1]
    assert niedrig is not None and hoch is not None
    assert niedrig < hoch

    # Höherer WACC bei gleichem Wachstum -> niedrigerer fairer Wert je Aktie:
    tiefer_wacc = matrix.fair_value_per_share[1][0]
    hoeherer_wacc = matrix.fair_value_per_share[1][2]
    assert tiefer_wacc is not None and hoeherer_wacc is not None
    assert hoeherer_wacc < tiefer_wacc


def test_sensitivity_matrix_markiert_unzulaessige_kombinationen_als_none() -> None:
    inputs = _basis_inputs()
    matrix = build_sensitivity_matrix(
        _basis_annahmen(),
        inputs,
        row_parameter="terminal_growth_rate",
        row_values=[0.02],
        column_parameter="wacc",
        column_values=[0.01, 0.10],  # 0.01 <= terminal_growth_rate(0.02) -> unzulaessig
    )

    assert matrix.fair_value_per_share[0][0] is None
    assert matrix.fair_value_per_share[0][1] is not None
