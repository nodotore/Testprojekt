from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.config.models import (
    Anlagehorizont,
    Ausgabeformat,
    NutzerProfil,
    Risikoklasse,
)
from investment_analyzer.config.settings import AppSettings
from investment_analyzer.config.store import ProfileStore


def test_default_profile_hat_alle_ausgabeformate() -> None:
    profil = default_profile()
    assert set(profil.ausgabeformate) == set(Ausgabeformat)


def test_default_profile_schliesst_microcaps_aus() -> None:
    profil = default_profile()
    assert profil.microcaps_ausschliessen is True
    assert profil.pennystocks_ausschliessen is True
    assert profil.illiquide_ausschliessen is True
    assert profil.marktkap_min_mio is not None and profil.marktkap_min_mio > 0


def test_default_profile_horizont_und_risikoklasse() -> None:
    profil = default_profile()
    assert profil.anlagehorizont == Anlagehorizont.MITTELFRISTIG
    assert profil.risikoklasse == Risikoklasse.AUSGEWOGEN


def test_leerer_stil_ist_ungueltig() -> None:
    with pytest.raises(ValidationError):
        NutzerProfil(stil=[])


def test_leere_ausgabeformate_sind_ungueltig() -> None:
    with pytest.raises(ValidationError):
        NutzerProfil(ausgabeformate=[])


def test_marktkap_min_groesser_max_ist_ungueltig() -> None:
    with pytest.raises(ValidationError):
        NutzerProfil(marktkap_min_mio=5000, marktkap_max_mio=1000)


def test_waehrung_wird_normalisiert() -> None:
    profil = NutzerProfil(waehrung="eur")
    assert profil.waehrung == "EUR"


def test_unbekanntes_feld_wird_abgelehnt() -> None:
    with pytest.raises(ValidationError):
        NutzerProfil.model_validate({"unbekanntes_feld": 123})


def test_profile_store_roundtrip(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    assert store.load_or_none() is None

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    store.save(profil)

    geladen = store.load()
    assert geladen == profil
    assert geladen.haftungsausschluss_akzeptiert is True


def test_profile_store_load_ohne_datei_wirft_fehler(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    with pytest.raises(FileNotFoundError):
        store.load()


def test_app_settings_sqlite_default(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path, database_url=None)
    assert settings.resolved_database_url.startswith("sqlite:///")
    assert str(tmp_path.name) in settings.resolved_database_url


def test_app_settings_explizite_database_url_hat_vorrang(tmp_path: Path) -> None:
    settings = AppSettings(
        data_dir=tmp_path, database_url="postgresql+psycopg://user:pass@localhost/db"
    )
    assert settings.resolved_database_url == "postgresql+psycopg://user:pass@localhost/db"


def test_app_settings_ensure_data_dirs(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path / "sub")
    settings.ensure_data_dirs()
    assert settings.data_dir.exists()
    assert settings.log_dir.exists()
