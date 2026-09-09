from __future__ import annotations

from investment_analyzer.ui.detail import _kennzahl


def test_kennzahl_none_wird_als_gedankenstrich_angezeigt() -> None:
    """Auftrag §11: fehlende Werte dürfen nie als 0 oder geratene Zahl
    erscheinen, sondern müssen als fehlend erkennbar sein."""

    assert _kennzahl(None) == "—"
    assert _kennzahl(None, prozent=True) == "—"


def test_kennzahl_prozent_formatierung() -> None:
    assert _kennzahl(0.0523, prozent=True) == "+5.2%"
    assert _kennzahl(-0.0523, prozent=True) == "-5.2%"
    assert _kennzahl(12.5, prozent=True) == "+1250%"


def test_kennzahl_zahl_formatierung() -> None:
    assert _kennzahl(1234.5678) == "1,234.57"
    assert _kennzahl(1234.5678, nachkomma=0) == "1,235"


def test_kennzahl_bool_wird_nicht_als_zahl_behandelt() -> None:
    # bool ist eine int-Unterklasse in Python -- ohne expliziten Vorrangzweig
    # würde True/False sonst als 1/0 formatiert statt als Ja/Nein.
    assert _kennzahl(True) == "Ja"
    assert _kennzahl(False) == "Nein"


def test_kennzahl_string_wird_unveraendert_durchgereicht() -> None:
    assert _kennzahl("Konsumgüter") == "Konsumgüter"
