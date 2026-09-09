from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.config.settings import get_settings
from investment_analyzer.config.store import ProfileStore
from investment_analyzer.db import create_all_tables, create_db_engine

APP_PATH = str(
    Path(__file__).resolve().parents[2] / "src" / "investment_analyzer" / "ui" / "app.py"
)


def _reset_caches() -> None:
    get_settings.cache_clear()
    st.cache_resource.clear()


def _migrate_test_db(data_dir: Path) -> None:
    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    create_all_tables(engine)
    engine.dispose()


def test_app_zeigt_ersteinrichtung_ohne_gespeichertes_profil(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Ersteinrichtung" in header_texte

    warnungen = " ".join(w.value for w in at.warning)
    assert "keine Anlageberatung" in warnungen

    _reset_caches()


def test_app_zeigt_datenstatus_mit_akzeptiertem_profil(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Datenstatus" in header_texte

    metrik_werte = {m.label: m.value for m in at.metric}
    assert metrik_werte.get("Unternehmen in der Datenbank") == "0"
    assert metrik_werte.get("Gespeicherte Datenpunkte") == "0"

    infos = " ".join(i.value for i in at.info)
    assert "keine Analysedaten" in infos

    _reset_caches()


def test_app_marktscreener_seite_ist_ueber_sidebar_erreichbar(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]

    at.sidebar.radio[0].set_value("Marktscreener").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Marktscreener" in header_texte
    subheader_texte = " ".join(h.value for h in at.subheader)
    assert "Unternehmen hinzufügen" in subheader_texte

    # Ohne hinterlegte Kontakt-E-Mail wird das Formular durch eine klare
    # Fehlermeldung ersetzt statt einen unbenutzbaren Abrufversuch zu erlauben.
    fehler = " ".join(e.value for e in at.error)
    assert "Kontakt-E-Mail" in fehler

    _reset_caches()


def test_app_marktscreener_zeigt_formular_mit_hinterlegter_kontakt_email(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    profil.sec_edgar_kontakt_email = "kontakt@example.invalid"
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Marktscreener").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    fehler = " ".join(e.value for e in at.error)
    assert "Kontakt-E-Mail" not in fehler
    radio_optionen = [option for r in at.radio for option in r.options]
    assert any("CIK" in option for option in radio_optionen)
    text_input_labels = [ti.label for ti in at.text_input]
    assert "CIK" in text_input_labels  # Standardauswahl des Radio-Buttons ist "CIK"

    _reset_caches()


def test_app_zeigt_fehler_wenn_db_nicht_migriert(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    # Bewusst KEINE Migration ausführen.

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    assert not at.exception
    fehler = " ".join(e.value for e in at.error)
    assert "nicht migriert" in fehler

    _reset_caches()
