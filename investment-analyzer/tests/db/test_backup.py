"""Restore-Prozess-Ausfalltest (Auftrag §15, SECURITY.md „Restore-Prozess
[...] end-to-end getestet") — Sicherung, Datenverlust/-korruption der
Live-Datenbank simuliert, Wiederherstellung, Datenintegrität geprüft."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from investment_analyzer.config.settings import AppSettings
from investment_analyzer.connectors.models import Source
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.db.backup import BackupError, backup_database, restore_database
from investment_analyzer.entity_resolution.models import Entity


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(data_dir=tmp_path)


def _seed_database(settings: AppSettings, *, entity_name: str) -> None:
    engine = create_db_engine(settings.resolved_database_url)
    create_all_tables(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        session.add(Entity(name=entity_name, country="DE"))
        session.commit()
    engine.dispose()


def _entity_names(settings: AppSettings) -> set[str]:
    engine = create_db_engine(settings.resolved_database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        names = set(session.scalars(select(Entity.name)).all())
    engine.dispose()
    return names


def test_backup_ohne_vorhandene_datenbank_wirft(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.raises(BackupError, match="nichts zu sichern"):
        backup_database(settings)


def test_backup_lehnt_nicht_sqlite_datenbank_ab(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path, database_url="postgresql+psycopg://x/y")
    with pytest.raises(BackupError, match="database_url"):
        backup_database(settings)


def test_restore_ohne_vorhandene_sicherungsdatei_wirft(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.raises(BackupError, match="existiert nicht"):
        restore_database(settings, tmp_path / "nicht-vorhanden.db")


def test_backup_erzeugt_zeitgestempelte_kopie(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_database(settings, entity_name="Firma H (synthetisches Beispiel)")

    backup_path = backup_database(settings)

    assert backup_path.exists()
    assert backup_path.parent == settings.data_dir / "backups"
    assert backup_path.suffix == ".db"
    assert backup_path.stat().st_size > 0


def test_end_zu_end_restore_prozess_stellt_daten_nach_datenverlust_wieder_her(
    tmp_path: Path,
) -> None:
    """Der eigentliche Abnahmenachweis: Sicherung -> simulierter Datenverlust
    (Live-Datenbankdatei wird durch eine leere/kaputte Datei ersetzt, wie bei
    einem Festplattenfehler oder einer fehlgeschlagenen Migration) ->
    Wiederherstellung -> die ursprünglichen Daten sind wieder vollständig da."""

    settings = _settings(tmp_path)
    _seed_database(settings, entity_name="Firma H (synthetisches Beispiel)")
    assert _entity_names(settings) == {"Firma H (synthetisches Beispiel)"}

    backup_path = backup_database(settings)

    db_path = settings.data_dir / "investment_analyzer.db"
    db_path.write_bytes(b"KORRUPTE DATEI -- SIMULIERTER DATENVERLUST")

    restored_path = restore_database(settings, backup_path)

    assert restored_path == db_path
    assert _entity_names(settings) == {"Firma H (synthetisches Beispiel)"}


def test_backups_ueberschreiben_sich_nicht_gegenseitig(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed_database(settings, entity_name="Firma H")

    clock_values = iter([datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC)])
    erste = backup_database(settings, clock=lambda: next(clock_values))
    zweite = backup_database(settings, clock=lambda: next(clock_values))

    assert erste != zweite
    assert erste.exists()
    assert zweite.exists()


def test_backup_bewahrt_registrierte_quellen(tmp_path: Path) -> None:
    """Stichprobe an einer zweiten Tabelle -- die Sicherung ist eine vollständige
    Dateikopie, nicht eine selektive Export der Entity-Tabelle allein."""

    settings = _settings(tmp_path)
    engine = create_db_engine(settings.resolved_database_url)
    create_all_tables(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        session.add(
            Source(
                key="test_source",
                display_name="Testquelle",
                base_url="https://example.invalid",
                license_note="nur für Tests",
            )
        )
        session.commit()
    engine.dispose()

    backup_path = backup_database(settings)
    (settings.data_dir / "investment_analyzer.db").unlink()
    restore_database(settings, backup_path)

    engine = create_db_engine(settings.resolved_database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        keys = set(session.scalars(select(Source.key)).all())
    engine.dispose()
    assert keys == {"test_source"}
