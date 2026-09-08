"""Sicherung/Wiederherstellung der lokalen SQLite-Datenbank (Auftrag §15,
SECURITY.md „Restore-Prozess").

Bei lokalem Betrieb (Milestone-0-Entscheidung, ADR-8: SQLite als einzelne
Datei unter ``AppSettings.data_dir``) bedeutet Sicherung/Wiederherstellung
eine atomare Dateikopie, kein Datenbank-Dump-Format. Nur für diese lokale
SQLite-Standardkonfiguration gedacht — wird ``AppSettings.database_url``
gesetzt (z. B. für einen künftigen PostgreSQL-Produktivbetrieb, siehe
ADR-2), übernimmt die jeweilige Datenbank ihr eigenes Backup-Tooling;
dieses Modul lehnt den Aufruf in diesem Fall bewusst ab (Auftrag §11:
keine stillschweigend falsche/unvollständige Aktion).

**Hinweis:** Für eine konsistente Sicherung darf während ``backup_database``
keine offene Schreibverbindung zur Datenbank bestehen (Standard-SQLite-
Einschränkung bei reinem Dateikopieren, insbesondere im WAL-Modus). Die
Windows-Startskripte/Benutzerhandbuch weisen entsprechend darauf hin, die
Anwendung vor einer Sicherung zu beenden.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from investment_analyzer.config.settings import AppSettings
from investment_analyzer.db.types import utc_now


class BackupError(RuntimeError):
    """Sicherung/Wiederherstellung konnte nicht durchgeführt werden."""


def _sqlite_db_path(settings: AppSettings) -> Path:
    if settings.database_url:
        raise BackupError(
            "Backup/Restore in diesem Modul ist nur für die lokale SQLite-"
            "Standarddatenbank implementiert (AppSettings.database_url ist "
            "gesetzt -- eine andere Datenbank übernimmt ihr eigenes Backup-Tooling)."
        )
    return settings.data_dir / "investment_analyzer.db"


def _atomic_copy(source: Path, destination: Path) -> None:
    """Kopiert ``source`` nach ``destination`` über eine temporäre Datei im selben
    Zielverzeichnis + ``Path.replace`` — vermeidet eine sichtbare halbgeschriebene
    Zieldatei, falls der Kopiervorgang mittendrin abbricht (Stromausfall, voller
    Datenträger)."""

    tmp_path = destination.with_name(destination.name + ".tmp")
    try:
        shutil.copyfile(source, tmp_path)
        tmp_path.replace(destination)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def backup_database(
    settings: AppSettings,
    *,
    backup_dir: Path | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> Path:
    """Sichert die aktuelle SQLite-Datenbankdatei als Zeitstempel-Kopie.

    Wirft ``BackupError``, falls keine Datenbankdatei existiert (nichts zu
    sichern) oder eine Nicht-SQLite-``database_url`` konfiguriert ist. Liefert
    den Pfad der neu erzeugten Sicherungsdatei.
    """

    db_path = _sqlite_db_path(settings)
    if not db_path.exists():
        raise BackupError(f"Keine Datenbankdatei unter {db_path} gefunden -- nichts zu sichern.")

    target_dir = backup_dir or (settings.data_dir / "backups")
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = clock().strftime("%Y%m%dT%H%M%SZ")
    backup_path = target_dir / f"investment_analyzer-{timestamp}.db"
    _atomic_copy(db_path, backup_path)
    return backup_path


def restore_database(settings: AppSettings, backup_path: Path) -> Path:
    """Stellt die SQLite-Datenbankdatei aus einer zuvor mit ``backup_database``
    erzeugten Sicherung wieder her — überschreibt die aktuelle Datenbankdatei
    vollständig. Wirft ``BackupError``, falls die Sicherungsdatei nicht
    existiert. Liefert den Pfad der wiederhergestellten Datenbankdatei.
    """

    if not backup_path.exists():
        raise BackupError(f"Sicherungsdatei {backup_path} existiert nicht.")

    db_path = _sqlite_db_path(settings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_copy(backup_path, db_path)
    return db_path
