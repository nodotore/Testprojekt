"""Nicht-UI-Logik zum Hochfahren der Anwendung (getrennt von ``app.py``, damit sie ohne
Streamlit-Laufzeitkontext testbar bleibt).

Erstellt bewusst KEIN Datenbankschema (das ist Aufgabe von Alembic, siehe
``alembic/`` und die Windows-Startskripte). Ist das Schema nicht
migriert, meldet ``check_database_ready`` dies, statt es stillschweigend
per ``create_all`` zu reparieren — Abweichungen vom Alembic-Versionsstand
sollen sichtbar werden, nicht verschwunden sein (CLAUDE.md: „Fail loud,
nicht silent").
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import Logger

from sqlalchemy import Engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from investment_analyzer.audit.logger import AuditLogger
from investment_analyzer.audit.logging_setup import configure_logging
from investment_analyzer.config.secrets import (
    SecretStore,
    SecretStoreUnavailableError,
    get_secret_store,
)
from investment_analyzer.config.settings import AppSettings, get_settings
from investment_analyzer.config.store import ProfileStore
from investment_analyzer.db import create_db_engine, create_session_factory

#: Tabellen, deren Vorhandensein als „Schema ist migriert" gewertet wird.
_EXPECTED_TABLES = {"entities", "entity_identifiers", "sources", "data_points", "audit_log_entries"}


@dataclass
class AppContext:
    settings: AppSettings
    engine: Engine
    session_factory: sessionmaker[Session]
    audit_logger: AuditLogger
    profile_store: ProfileStore
    logger: Logger
    #: ``None``, falls kein Secret-Store-Backend verfügbar ist (z. B. kein
    #: OS-Keyring und kein Master-Passwort gesetzt) — der Marktscreener
    #: zeigt in diesem Fall einen klaren Hinweis statt eines Absturzes
    #: (Auftrag §4: „Fail loud, nicht silent"). Ein Bedienfeld zum Setzen
    #: eines Master-Passworts für den verschlüsselten Datei-Fallback ist
    #: noch nicht gebaut (siehe TODO.md, Einstellungen-Seite).
    secret_store: SecretStore | None


def check_database_ready(engine: Engine) -> bool:
    """Prüft, ob das erwartete Schema bereits migriert wurde."""

    try:
        inspector = inspect(engine)
        return _EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    except Exception:
        return False


def bootstrap(settings: AppSettings | None = None) -> AppContext:
    """Baut den Anwendungskontext auf (Engine, Sessions, Logging, Audit, Profilspeicher)."""

    resolved_settings = settings or get_settings()
    resolved_settings.ensure_data_dirs()
    logger = configure_logging(resolved_settings)

    engine = create_db_engine(resolved_settings.resolved_database_url)
    session_factory = create_session_factory(engine)
    audit_logger = AuditLogger(session_factory)
    profile_store = ProfileStore(resolved_settings.profile_path)

    try:
        # Ohne Master-Passwort: nutzt nur das OS-Keyring (unter Windows der
        # Credential Manager) — funktioniert dort i. d. R. ohne weitere
        # Einrichtung. Ist kein Keyring verfügbar, bleibt secret_store
        # bewusst None statt eine Passwortabfrage zu erzwingen, für die es
        # noch keine Oberflächenseite gibt.
        secret_store: SecretStore | None = get_secret_store(path=resolved_settings.secrets_path)
    except SecretStoreUnavailableError:
        secret_store = None

    return AppContext(
        settings=resolved_settings,
        engine=engine,
        session_factory=session_factory,
        audit_logger=audit_logger,
        profile_store=profile_store,
        logger=logger,
        secret_store=secret_store,
    )
