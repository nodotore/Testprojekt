"""Kommandozeilen-Werkzeug für Sicherung/Wiederherstellung (Auftrag §15,
SECURITY.md „Restore-Prozess"). Dünner Wrapper um ``db/backup.py`` — die
eigentliche Logik ist dort bereits unabhängig getestet
(``tests/db/test_backup.py``); dieses Modul übersetzt sie nur in einen für
Endnutzer über die Windows-Skripte (``scripts/backup-database.ps1``/
``scripts/restore-database.ps1``, siehe BENUTZERHANDBUCH.md) aufrufbaren
Befehl.

Aufruf (aus der aktivierten virtuellen Umgebung):
    python -m investment_analyzer.db.backup_cli sichern
    python -m investment_analyzer.db.backup_cli wiederherstellen <Pfad-zur-Sicherung>
    python -m investment_analyzer.db.backup_cli auflisten
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from investment_analyzer.config.settings import get_settings
from investment_analyzer.db.backup import BackupError, backup_database, restore_database


def _sichern() -> int:
    settings = get_settings()
    try:
        pfad = backup_database(settings)
    except BackupError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"Sicherung erstellt: {pfad}")
    return 0


def _wiederherstellen(backup_pfad: str) -> int:
    settings = get_settings()
    try:
        pfad = restore_database(settings, Path(backup_pfad))
    except BackupError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"Datenbank wiederhergestellt aus: {backup_pfad}")
    print(f"Aktive Datenbankdatei: {pfad}")
    print("Bitte den Investment-Analysator (falls noch geöffnet) neu starten.")
    return 0


def _auflisten() -> int:
    settings = get_settings()
    backup_dir = settings.data_dir / "backups"
    if not backup_dir.exists():
        print("Noch keine Sicherungen vorhanden.")
        return 0
    backups = sorted(backup_dir.glob("investment_analyzer-*.db"))
    if not backups:
        print("Noch keine Sicherungen vorhanden.")
        return 0
    for path in backups:
        print(path)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m investment_analyzer.db.backup_cli",
        description=(
            "Sicherung/Wiederherstellung der lokalen Investment-Analysator-"
            "Datenbank (nur für die lokale SQLite-Standardkonfiguration)."
        ),
    )
    subparsers = parser.add_subparsers(dest="befehl", required=True)
    subparsers.add_parser("sichern", help="Erstellt eine neue Sicherung der aktuellen Datenbank.")
    wiederherstellen_parser = subparsers.add_parser(
        "wiederherstellen", help="Stellt die Datenbank aus einer Sicherungsdatei wieder her."
    )
    wiederherstellen_parser.add_argument("backup_pfad", help="Pfad zur Sicherungsdatei (siehe 'auflisten').")
    subparsers.add_parser("auflisten", help="Listet vorhandene Sicherungen auf.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.befehl == "sichern":
        return _sichern()
    if args.befehl == "wiederherstellen":
        return _wiederherstellen(args.backup_pfad)
    return _auflisten()


if __name__ == "__main__":
    raise SystemExit(main())
