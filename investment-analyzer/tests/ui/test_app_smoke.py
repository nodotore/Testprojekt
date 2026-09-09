from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.config.settings import get_settings
from investment_analyzer.config.store import ProfileStore
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind

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


FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _seed_entity_mit_fundamentaldaten(data_dir: Path) -> None:
    """Legt ein einzelnes synthetisches Unternehmen mit genug Kennzahlen an,
    damit ``Unternehmensdetail`` einen vollständigen Bericht rendert — kein
    Internetzugang in dieser Sandbox für echte Marktdaten (siehe
    tests/reports/test_bundle.py, gleiches Muster)."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()
        source = sources["sec_edgar"]

        def dp(metric: Metric, period_end: date, value: float) -> DataPoint:
            return DataPoint(
                entity_id=entity.id,
                source_id=source.id,
                metric_name=metric.value,
                period_start=None,
                period_end=period_end,
                published_at=period_end,
                retrieved_at_utc=FETCHED_AT,
                value_raw=str(value),
                value_normalized=value,
                unit="USD",
                currency="USD",
                value_kind=ValueKind.REPORTED,
                document_url="https://example.invalid/doc",
                document_type="10-K",
                content_hash="x" * 64,
                document_id=f"acc-{metric.value}-{period_end.isoformat()}",
            )

        jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
        umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
        for jahr, u in zip(jahre, umsatz, strict=True):
            session.add(dp(Metric.REVENUE, jahr, u))
            session.add(dp(Metric.OPERATING_CASH_FLOW, jahr, u * 0.15))
            session.add(dp(Metric.CAPEX, jahr, -u * 0.05))
            session.add(dp(Metric.NET_INCOME, jahr, u * 0.1))

        letztes_jahr = date(2023, 12, 31)
        for metric, value in (
            (Metric.OPERATING_INCOME, 180.0),
            (Metric.DEPRECIATION_AND_AMORTIZATION, 40.0),
            (Metric.TOTAL_EQUITY, 1000.0),
            (Metric.LONG_TERM_DEBT, 300.0),
            (Metric.SHORT_TERM_DEBT, 100.0),
            (Metric.CASH_AND_EQUIVALENTS, 200.0),
            (Metric.SHARES_DILUTED, 100.0),
            (Metric.EPS_DILUTED, 2.0),
            (Metric.INTEREST_EXPENSE, 20.0),
            (Metric.CURRENT_ASSETS, 500.0),
            (Metric.CURRENT_LIABILITIES, 250.0),
            (Metric.DIVIDENDS_PAID, 30.0),
            (Metric.GROSS_PROFIT, 500.0),
        ):
            session.add(dp(metric, letztes_jahr, value))

        session.add(dp(Metric.PRICE_CLOSE, date(2024, 1, 15), 20.0))
        session.commit()
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


def test_app_kandidatenrangliste_ohne_unternehmen_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Kandidaten-Rangliste").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Kandidaten-Rangliste" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Unternehmen erfasst" in infos

    _reset_caches()


def test_app_kandidatenrangliste_zeigt_rangfolge_nach_score(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Kandidaten-Rangliste").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Kandidaten-Rangliste" in header_texte

    captions = " ".join(c.value for c in at.caption)
    assert "1 erfasste Unternehmen" in captions

    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert list(df["Unternehmen"]) == ["Firma G (synthetisches Beispiel)"]
    assert df.loc[0, "Score (0–100)"] > 0

    _reset_caches()


def test_app_unternehmensdetail_ohne_unternehmen_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Unternehmensdetail").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Unternehmensdetail" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Unternehmen erfasst" in infos

    _reset_caches()


def test_app_unternehmensdetail_zeigt_bericht_fuer_erfasstes_unternehmen(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Unternehmensdetail").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Unternehmensdetail" in header_texte

    subheader_texte = " ".join(h.value for h in at.subheader)
    for erwartet in ("Kennzahlen", "Bewertung", "Score", "Nachrichten", "Quellen", "Annahmen", "Export"):
        assert erwartet in subheader_texte

    # Auftrag-§10-Kopfzeilenpflicht: Datenstand/Analysezeit/Marktdatenverzögerung/
    # Datenabdeckung/Konfidenz müssen sichtbar sein.
    captions = " ".join(c.value for c in at.caption)
    assert "Datenstand (as_of)" in captions
    assert "Analysezeit" in captions
    assert "Datenabdeckung" in captions
    assert "Konfidenz" in captions

    # Auftrag-§10-Titel „Unternehmensdetail MIT Quellenleiste" -- die
    # registrierten Quellen inkl. Lizenzhinweis müssen als Tabelle erscheinen.
    tabellen_werte = [str(t.value) for t in at.table]
    assert any("sec_edgar" in v or "SEC" in v for v in tabellen_werte)

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
