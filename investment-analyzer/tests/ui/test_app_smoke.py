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
    assert "keine Analysedaten" in infos or "Milestone 2" in infos

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
