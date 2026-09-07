from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from investment_analyzer.config.models import (
    Anlagehorizont,
    Anlagestil,
    Ausgabeformat,
    Risikoklasse,
)
from investment_analyzer.ui.profile_form import build_profile_from_form, split_csv


def test_split_csv_bereinigt_leerraum_und_leere_eintraege() -> None:
    assert split_csv(" Öl, Gas ,, Tabak") == ["Öl", "Gas", "Tabak"]


def test_split_csv_leerer_text() -> None:
    assert split_csv("") == []


def _valid_form() -> dict:
    return {
        "profil_name": "Standard",
        "anlageregionen": ["USA", "Deutschland"],
        "boersen": ["NYSE", "XETRA"],
        "branchen": "",
        "ausschlussbranchen": "Rüstung, Tabak",
        "ausschlusswerte": "",
        "anlagehorizont": Anlagehorizont.MITTELFRISTIG,
        "risikoklasse": Risikoklasse.AUSGEWOGEN,
        "stil": [Anlagestil.MISCHUNG],
        "waehrung": "EUR",
        "vergleichsindex": "MSCI World",
        "marktkap_min_mio": 1000.0,
        "marktkap_max_mio": None,
        "positionsgroesse_max_prozent": 5.0,
        "kandidatenzahl_ziel": 10,
        "microcaps_ausschliessen": True,
        "pennystocks_ausschliessen": True,
        "illiquide_ausschliessen": True,
        "speicherort": "/tmp/reports",
        "ausgabeformate": list(Ausgabeformat),
        "konfigurierte_quellen": ["sec_edgar"],
        "haftungsausschluss_akzeptiert": True,
    }


def test_build_profile_from_form_gueltig() -> None:
    profil = build_profile_from_form(_valid_form())
    assert profil.profil_name == "Standard"
    assert profil.ausschlussbranchen == ["Rüstung", "Tabak"]
    assert profil.speicherort == Path("/tmp/reports")
    assert profil.haftungsausschluss_akzeptiert is True


def test_build_profile_from_form_ungueltige_marktkap_wirft() -> None:
    daten = _valid_form()
    daten["marktkap_min_mio"] = 5000.0
    daten["marktkap_max_mio"] = 1000.0
    with pytest.raises(ValidationError):
        build_profile_from_form(daten)


def test_build_profile_from_form_ohne_stil_wirft() -> None:
    daten = _valid_form()
    daten["stil"] = []
    with pytest.raises(ValidationError):
        build_profile_from_form(daten)
