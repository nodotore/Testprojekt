from __future__ import annotations

from datetime import date

from investment_analyzer.ui.dcf import _pct, _sensitivitaetstabelle, _zahl
from investment_analyzer.valuation.dcf import (
    DCFAssumptions,
    DCFInputs,
    SensitivityMatrix,
    build_sensitivity_matrix,
    run_dcf,
)


def test_pct_und_zahl_formatieren_none_als_gedankenstrich() -> None:
    assert _pct(None) == "—"
    assert _zahl(None) == "—"


def test_pct_zeigt_vorzeichen() -> None:
    assert _pct(0.09) == "+9.0%"
    assert _pct(-0.02) == "-2.0%"


def test_zahl_formatiert_mit_tausendertrennzeichen() -> None:
    assert _zahl(1234.5) == "1,234.50"


def test_sensitivitaetstabelle_enthaelt_zeilen_und_spaltenlabels() -> None:
    base = DCFAssumptions(revenue_growth_rate=0.10, fcf_margin=0.10, wacc=0.09, terminal_growth_rate=0.02)
    inputs = DCFInputs(base_revenue=1000.0, as_of=date(2023, 12, 31), net_debt=200.0, shares_diluted=100.0)
    matrix = build_sensitivity_matrix(
        base, inputs,
        row_parameter="revenue_growth_rate", row_values=[0.08, 0.10, 0.12],
        column_parameter="wacc", column_values=[0.08, 0.09, 0.10],
    )

    df = _sensitivitaetstabelle(matrix)

    assert df.shape == (3, 4)  # 3 Zeilen, 1 Label-Spalte + 3 Wert-Spalten
    assert list(df["Umsatzwachstum"]) == ["+8.0%", "+10.0%", "+12.0%"]
    assert any("WACC" in spalte for spalte in df.columns)


def test_sensitivitaetstabelle_zeigt_none_bei_unzulaessigen_annahmen() -> None:
    # WACC <= Terminalwachstum ist rechnerisch unzulässig -- run_dcf liefert
    # dann None, was in der Matrix als fehlender (NaN-)Wert erscheinen muss,
    # nie als geratene Zahl (Auftrag §11).
    base = DCFAssumptions(revenue_growth_rate=0.10, fcf_margin=0.10, wacc=0.02, terminal_growth_rate=0.02)
    inputs = DCFInputs(base_revenue=1000.0, as_of=date(2023, 12, 31), net_debt=200.0, shares_diluted=100.0)
    matrix = SensitivityMatrix(
        row_parameter="revenue_growth_rate",
        row_values=(0.10,),
        column_parameter="wacc",
        column_values=(0.01, 0.02),
        fair_value_per_share=((None, None),),
    )
    assert run_dcf(base, inputs) is None

    df = _sensitivitaetstabelle(matrix)
    assert df.iloc[0, 1] is None or df.iloc[0, 1] != df.iloc[0, 1]  # None oder NaN
