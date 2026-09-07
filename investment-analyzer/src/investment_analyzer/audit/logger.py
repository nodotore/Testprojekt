"""Schreibender Zugriff auf das Audit-Log (``AuditLogEntry``, Auftrag §12).

Getrennt von ``logging_setup.py`` (Textlog für Entwickler/Diagnose):
``AuditLogger`` schreibt strukturierte, dauerhafte Einträge in die
Datenbank, die auf der UI-Seite „Einstellungen, Quellen und
Prüfprotokoll" (Auftrag §10) angezeigt werden.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from investment_analyzer.audit.models import AuditEventType, AuditLogEntry
from investment_analyzer.db import session_scope


class AuditLogger:
    """Schreibt ``AuditLogEntry``-Zeilen über eine SQLAlchemy-Sessionfabrik."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def log(
        self,
        *,
        event_type: str,
        actor: str,
        entity_id: str | None = None,
        source_key: str | None = None,
        detail: str | None = None,
    ) -> None:
        with session_scope(self._session_factory) as session:
            session.add(
                AuditLogEntry(
                    event_type=event_type,
                    actor=actor,
                    entity_id=entity_id,
                    source_key=source_key,
                    detail=detail,
                )
            )

    def log_data_fetch(
        self, *, actor: str, source_key: str, entity_id: str | None = None, detail: str | None = None
    ) -> None:
        self.log(
            event_type=AuditEventType.DATA_FETCH,
            actor=actor,
            entity_id=entity_id,
            source_key=source_key,
            detail=detail,
        )

    def log_data_fetch_error(
        self, *, actor: str, source_key: str, entity_id: str | None = None, detail: str | None = None
    ) -> None:
        self.log(
            event_type=AuditEventType.DATA_FETCH_ERROR,
            actor=actor,
            entity_id=entity_id,
            source_key=source_key,
            detail=detail,
        )

    def log_report_generated(self, *, actor: str, detail: str | None = None) -> None:
        self.log(event_type=AuditEventType.REPORT_GENERATED, actor=actor, detail=detail)

    def log_secret_accessed(self, *, actor: str, secret_name: str) -> None:
        """Protokolliert NUR, dass ein Secret gelesen wurde — niemals dessen Wert."""

        self.log(
            event_type=AuditEventType.SECRET_ACCESSED,
            actor=actor,
            detail=f"secret_name={secret_name}",
        )

    def log_config_changed(self, *, actor: str, detail: str | None = None) -> None:
        self.log(event_type=AuditEventType.CONFIG_CHANGED, actor=actor, detail=detail)

    def log_belegpruefung_fehlgeschlagen(
        self, *, actor: str, entity_id: str | None = None, detail: str | None = None
    ) -> None:
        """Auftrag §11: Belegprüfung vor jeder Ausgabe — Fehlschläge werden protokolliert."""

        self.log(
            event_type=AuditEventType.BELEGPRUEFUNG_FEHLGESCHLAGEN,
            actor=actor,
            entity_id=entity_id,
            detail=detail,
        )
