from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from investment_analyzer.audit.models import AuditEventType, AuditLogEntry
from investment_analyzer.config.defaults import default_profile
from investment_analyzer.config.settings import get_settings
from investment_analyzer.config.store import ProfileStore
from investment_analyzer.connectors.gdelt import GdeltArticle
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.news.ingest import ingest_gdelt_articles
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.portfolio.models import PortfolioPosition

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


def _seed_nachrichten_fuer_firma_g(data_dir: Path) -> None:
    """Fügt zwei GDELT-Meldungen zur bereits per
    ``_seed_entity_mit_fundamentaldaten`` angelegten Firma G hinzu,
    damit ``ui/news.py`` einen mehrquellenbestätigten Cluster rendert."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma G (synthetisches Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
        )
        session.flush()

        articles = (
            GdeltArticle(
                url="https://outlet-a.test/artikel-1",
                title="Firma G meldet Rekordumsatz im ersten Quartal",
                domain="outlet-a.test",
                language="German",
                source_country="Germany",
                seen_at=datetime(2026, 3, 1, 8, tzinfo=UTC),
                fetched_at_utc=datetime(2026, 3, 1, 8, tzinfo=UTC),
                source_url="https://api.gdeltproject.org/api/v2/doc/doc?query=Firma+G",
            ),
            GdeltArticle(
                url="https://outlet-b.test/artikel-2",
                title="Firma G meldet Rekordumsatz im ersten Quartal 2026",
                domain="outlet-b.test",
                language="German",
                source_country="Germany",
                seen_at=datetime(2026, 3, 1, 10, tzinfo=UTC),
                fetched_at_utc=datetime(2026, 3, 1, 10, tzinfo=UTC),
                source_url="https://api.gdeltproject.org/api/v2/doc/doc?query=Firma+G",
            ),
        )
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()
    engine.dispose()


def _seed_portfolio_position_mit_kurs(data_dir: Path) -> None:
    """Legt eine einzelne Portfolio-Position mit bekanntem Kurs an, damit
    ``ui/watchlist.py`` eine vollständige Portfolio-Übersicht rendert."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma J (Portfolio-Beispiel)",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000010")],
        )
        entity.sic_description = "Software"
        entity.country = "US"
        session.flush()

        session.add(PortfolioPosition(entity_id=entity.id, quantity=10.0, currency="EUR"))
        session.add(
            DataPoint(
                entity_id=entity.id,
                source_id=sources["alpha_vantage"].id,
                metric_name=Metric.PRICE_CLOSE.value,
                period_start=None,
                period_end=date(2024, 1, 15),
                published_at=date(2024, 1, 15),
                retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
                value_raw="50.0",
                value_normalized=50.0,
                unit="price_per_share",
                currency=None,
                value_kind=ValueKind.REPORTED,
                document_url="https://example.invalid/quote",
                document_type="market_data_snapshot",
                content_hash="y" * 64,
                document_id=None,
            )
        )
        session.commit()
    engine.dispose()


def _seed_quellen_und_pruefprotokoll(data_dir: Path) -> None:
    """Registriert die Standardquellen und schreibt zwei Audit-Log-Einträge
    unterschiedlichen Ereignistyps, damit ``ui/settings.py`` sowohl die
    Quellen- als auch die Prüfprotokoll-Tabelle mit echten Zeilen rendert."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        ensure_default_sources(session)
        session.add(
            AuditLogEntry(
                event_type=AuditEventType.CONFIG_CHANGED, actor="test", detail="Testeintrag Konfiguration"
            )
        )
        session.add(
            AuditLogEntry(
                event_type=AuditEventType.REPORT_GENERATED, actor="test", detail="Testeintrag Bericht"
            )
        )
        session.commit()
    engine.dispose()


def _seed_zwei_firmen_fuer_backtest(data_dir: Path) -> None:
    """Legt zwei synthetische Unternehmen mit vollständigem, berechenbarem
    Score-Profil und monatlichen Kurspunkten Jan–Mär 2024 an, damit
    ``ui/backtest.py`` einen echten Backtest über drei Rebalancing-Stichtage
    (1.1./1.2./1.3.2024, Intervall „Monatlich") ausführen kann."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        source = sources["sec_edgar"]
        retrieved_at = datetime(2023, 12, 1, tzinfo=UTC)

        def dp(entity, metric: Metric, period_end: date, value: float, retrieved_at_utc: datetime) -> DataPoint:
            return DataPoint(
                entity_id=entity.id,
                source_id=source.id,
                metric_name=metric.value,
                period_start=None,
                period_end=period_end,
                published_at=period_end,
                retrieved_at_utc=retrieved_at_utc,
                value_raw=str(value),
                value_normalized=value,
                unit="USD",
                currency="USD",
                value_kind=ValueKind.REPORTED,
                document_url="https://example.invalid/doc",
                document_type="10-K",
                content_hash=f"bt-{entity.id}-{metric.value}-{period_end.isoformat()}",
                document_id=None,
            )

        def seed(name: str, cik: str, kurse: tuple[float, float, float]) -> None:
            entity = find_or_create_entity(
                session, name=name, identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value=cik)]
            )
            session.flush()

            jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
            umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
            for jahr, u in zip(jahre, umsatz, strict=True):
                session.add(dp(entity, Metric.REVENUE, jahr, u, retrieved_at))
                session.add(dp(entity, Metric.OPERATING_CASH_FLOW, jahr, u * 0.15, retrieved_at))
                session.add(dp(entity, Metric.CAPEX, jahr, -u * 0.05, retrieved_at))
                session.add(dp(entity, Metric.NET_INCOME, jahr, u * 0.1, retrieved_at))

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
                session.add(dp(entity, metric, letztes_jahr, value, retrieved_at))

            for monat, kurs in zip((date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)), kurse, strict=True):
                session.add(dp(entity, Metric.PRICE_CLOSE, monat, kurs, datetime.combine(monat, datetime.min.time(), tzinfo=UTC)))

        seed("Firma M (Backtest-Beispiel)", "0000000013", (100.0, 110.0, 121.0))
        seed("Firma N (Backtest-Beispiel)", "0000000014", (100.0, 95.0, 99.0))
        session.commit()
    engine.dispose()


def _seed_zwei_peer_unternehmen(data_dir: Path) -> None:
    """Legt zwei synthetische Unternehmen mit identischem SIC-Code an,
    damit ``Peer-Vergleich`` (ui/peers.py) einen Peer findet und eine
    vollständige Vergleichstabelle rendert."""

    engine = create_db_engine(f"sqlite:///{data_dir / 'investment_analyzer.db'}")
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        source = sources["sec_edgar"]

        def dp(entity, metric: Metric, period_end: date, value: float) -> DataPoint:
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
                document_id=f"acc-{entity.id}-{metric.value}-{period_end.isoformat()}",
            )

        def seed(name: str, cik: str) -> None:
            entity = find_or_create_entity(
                session, name=name, identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value=cik)]
            )
            entity.sic_code = "7372"
            session.flush()

            jahre = [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]
            umsatz = [1000.0, 1100.0, 1210.0, 1331.0]
            for jahr, u in zip(jahre, umsatz, strict=True):
                session.add(dp(entity, Metric.REVENUE, jahr, u))
                session.add(dp(entity, Metric.OPERATING_CASH_FLOW, jahr, u * 0.15))
                session.add(dp(entity, Metric.CAPEX, jahr, -u * 0.05))
                session.add(dp(entity, Metric.NET_INCOME, jahr, u * 0.1))

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
                session.add(dp(entity, metric, letztes_jahr, value))
            session.add(dp(entity, Metric.PRICE_CLOSE, date(2024, 1, 15), 20.0))

        seed("Firma G (synthetisches Beispiel)", "0000000007")
        seed("Firma H (Peer)", "0000000008")
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


def test_app_peervergleich_ohne_unternehmen_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Peer-Vergleich").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Peer-Vergleich" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Unternehmen erfasst" in infos

    _reset_caches()


def test_app_peervergleich_ohne_sic_code_zeigt_warnung(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Peer-Vergleich").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    warnungen = " ".join(w.value for w in at.warning)
    assert "SIC-Branchencode" in warnungen

    _reset_caches()


def test_app_peervergleich_zeigt_vergleichstabelle_mit_peer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_zwei_peer_unternehmen(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Peer-Vergleich").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    captions = " ".join(c.value for c in at.caption)
    assert "1 Peer(s) gefunden" in captions

    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert list(df["Unternehmen"]) == ["Firma G (synthetisches Beispiel) (ausgewählt)", "Firma H (Peer)"]

    _reset_caches()


def test_app_dcfanalyse_ohne_unternehmen_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("DCF- und Szenarioanalyse").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "DCF- und Szenarioanalyse" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Unternehmen erfasst" in infos

    _reset_caches()


def test_app_dcfanalyse_zeigt_szenarien_und_sensitivitaet(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("DCF- und Szenarioanalyse").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "DCF- und Szenarioanalyse" in header_texte

    subheader_texte = " ".join(h.value for h in at.subheader)
    assert "Szenarien" in subheader_texte
    assert "Sensitivitätsanalyse" in subheader_texte

    expander_labels = [exp.label for exp in at.expander]
    assert any("Basis" in label for label in expander_labels)
    assert any("Optimistisch" in label for label in expander_labels)
    assert any("Pessimistisch" in label for label in expander_labels)

    markdown_texte = " ".join(m.value for m in at.markdown)
    assert "Umsatzwachstum × WACC" in markdown_texte
    assert "FCF-Marge × Terminalwachstum" in markdown_texte

    _reset_caches()


def test_app_nachrichten_ohne_meldungen_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Nachrichten/Ereignisse").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Nachrichten/Ereignisse" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Nachrichtenmeldungen" in infos

    _reset_caches()


def test_app_nachrichten_zeigt_mehrquellenbestaetigten_cluster(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_entity_mit_fundamentaldaten(tmp_path)
    _seed_nachrichten_fuer_firma_g(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Nachrichten/Ereignisse").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    body_texte = " ".join(w.value for w in at.markdown) + " ".join(w.value for w in at.text)
    assert "2 Meldung(en) in 1 Ereignis-Cluster(n)" in body_texte

    expander_labels = [exp.label for exp in at.expander]
    assert any("mehrquellenbestätigt" in label for label in expander_labels)

    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert len(df) == 2
    assert set(df["Domain"]) == {"outlet-a.test", "outlet-b.test"}

    _reset_caches()


def test_app_watchlist_portfolio_ohne_eintraege_zeigt_hinweise(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Watchlist/Portfolio").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Watchlist/Portfolio" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Watchlist-Einträge" in infos
    assert "Noch keine Portfolio-Positionen" in infos

    _reset_caches()


def test_app_watchlist_portfolio_zeigt_position_und_konzentration(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_portfolio_position_mit_kurs(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Watchlist/Portfolio").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    metrik_werte = {m.label: m.value for m in at.metric}
    assert metrik_werte.get("Gesamtwert (bekannter Anteil)") == "500.00"

    assert len(at.dataframe) >= 1
    positionen_df = at.dataframe[0].value
    assert list(positionen_df["Unternehmen"]) == ["Firma J (Portfolio-Beispiel)"]
    assert positionen_df.loc[0, "Marktwert"] == 500.0

    markdown_texte = " ".join(m.value for m in at.markdown)
    assert "Branchenkonzentration" in markdown_texte
    assert "Länderkonzentration" in markdown_texte

    _reset_caches()


def test_app_backtest_ohne_ausfuehrung_zeigt_hinweis(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Backtest").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Backtest" in header_texte
    infos = " ".join(i.value for i in at.info)
    assert "Backtest ausführen" in infos

    _reset_caches()


def test_app_backtest_zeigt_kennzahlen_und_perioden(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_zwei_firmen_fuer_backtest(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Backtest").run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]

    at.date_input[0].set_value(date(2024, 1, 1))
    at.date_input[1].set_value(date(2024, 3, 1))
    at.selectbox[0].set_value("Monatlich")
    at.number_input[0].set_value(2)
    at.button[0].click().run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    metrik_werte = {m.label: m.value for m in at.metric}
    assert "Gesamtrendite" in metrik_werte
    assert metrik_werte["Gesamtrendite"] != "—"

    subheader_texte = " ".join(h.value for h in at.subheader)
    assert "NAV-Verlauf" in subheader_texte
    assert "Rebalancing-Perioden" in subheader_texte

    assert len(at.dataframe) == 1
    perioden_df = at.dataframe[0].value
    assert len(perioden_df) == 2  # 3 Stichtage -> 2 Halteperioden

    _reset_caches()


def test_app_einstellungen_ohne_daten_zeigt_leere_zustaende(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Einstellungen, Quellen und Prüfprotokoll").run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    header_texte = " ".join(h.value for h in at.header)
    assert "Einstellungen, Quellen und Prüfprotokoll" in header_texte

    # In dieser Sandbox ist kein OS-Keyring verfügbar (per keyring.get_keyring()
    # bestätigt) -- ctx.secret_store ist daher None, die Seite muss den
    # Master-Passwort-Einrichtungsdialog zeigen statt abzustürzen.
    warnungen = " ".join(w.value for w in at.warning)
    assert "Kein OS-Keyring verfügbar" in warnungen

    infos = " ".join(i.value for i in at.info)
    assert "Noch keine Quellen registriert" in infos
    assert "Noch keine Prüfprotokoll-Einträge" in infos

    _reset_caches()


def test_app_einstellungen_zeigt_quellen_und_pruefprotokoll(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)
    _seed_quellen_und_pruefprotokoll(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Einstellungen, Quellen und Prüfprotokoll").run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]

    assert len(at.dataframe) == 2
    quellen_df = at.dataframe[0].value
    assert set(quellen_df["Schlüssel"]) == {"sec_edgar", "alpha_vantage", "gdelt", "ir_rss"}

    protokoll_df = at.dataframe[1].value
    assert len(protokoll_df) == 2
    assert set(protokoll_df["Ereignistyp"]) == {
        AuditEventType.CONFIG_CHANGED, AuditEventType.REPORT_GENERATED,
    }

    # Nach Ereignistyp filtern -- nur config_changed soll übrig bleiben.
    at.selectbox[0].set_value(AuditEventType.CONFIG_CHANGED).run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]
    gefiltert = at.dataframe[1].value
    assert list(gefiltert["Ereignistyp"]) == [AuditEventType.CONFIG_CHANGED]

    _reset_caches()


def test_app_einstellungen_richtet_secret_store_ein_und_setzt_schluessel(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("IA_DATA_DIR", str(tmp_path))
    _reset_caches()
    _migrate_test_db(tmp_path)

    profil = default_profile()
    profil.haftungsausschluss_akzeptiert = True
    ProfileStore(tmp_path / "profile.json").save(profil)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("Einstellungen, Quellen und Prüfprotokoll").run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]

    # ``st.rerun()`` im Formular-Handler wird innerhalb desselben ``.run()``
    # automatisch nachvollzogen (AppTest führt den erneuten Skriptlauf sofort
    # aus) — die einmalige ``st.success("Eingerichtet.")``-Meldung aus dem
    # verworfenen Lauf ist danach nicht mehr sichtbar. Geprüft wird daher der
    # dauerhafte Effekt: ``ctx.secret_store`` ist gesetzt, wodurch die
    # Alpha-Vantage-Schluesselverwaltung an ihrer Stelle erscheint.
    passwort_felder = [ti for ti in at.text_input if ti.proto.type == ti.proto.PASSWORD]
    assert len(passwort_felder) == 2
    passwort_felder[0].set_value("ein-sehr-sicheres-master-passwort")
    passwort_felder[1].set_value("ein-sehr-sicheres-master-passwort")
    at.button[0].click().run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    infos = " ".join(i.value for i in at.info)
    assert "Kein Alpha-Vantage-API-Schlüssel hinterlegt" in infos

    schluessel_felder = [ti for ti in at.text_input if ti.proto.type == ti.proto.PASSWORD]
    assert len(schluessel_felder) == 1
    schluessel_felder[0].set_value("dummy-test-schluessel")
    at.button[0].click().run(timeout=30)

    assert not at.exception, [str(e) for e in at.exception]
    erfolge = " ".join(s.value for s in at.success)
    assert "Ein Alpha-Vantage-API-Schlüssel ist hinterlegt" in erfolge

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
