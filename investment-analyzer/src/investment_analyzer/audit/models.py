"""ORM-Modell: Audit-Log (Auftrag §12: vollständiges Audit-Log).

Append-only Protokoll aller sicherheits-/nachvollziehbarkeitsrelevanten
Vorgänge: Datenabrufe, Fehler, generierte Berichte, Secret-Zugriffe
(nur Metadaten, nie der Secret-Wert selbst). Wird in der UI-Seite
„Einstellungen, Quellen und Prüfprotokoll" angezeigt (Auftrag §10).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class AuditEventType:
    """Bekannte Ereignistypen (String-Konstanten statt striktem Enum, s. IdentifierType)."""

    DATA_FETCH = "data_fetch"
    DATA_FETCH_ERROR = "data_fetch_error"
    REPORT_GENERATED = "report_generated"
    SECRET_ACCESSED = "secret_accessed"
    CONFIG_CHANGED = "config_changed"
    BELEGPRUEFUNG_FEHLGESCHLAGEN = "belegpruefung_fehlgeschlagen"


class AuditLogEntry(Base):
    """Ein einzelner, unveränderlicher Audit-Log-Eintrag."""

    __tablename__ = "audit_log_entries"
    __table_args__ = (Index("ix_audit_log_timestamp", "timestamp_utc"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="Modul/Agent/Connector, der das Ereignis auslöste."
    )
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Freitext/JSON-Detail — NIEMALS Secret-Werte enthalten."
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"AuditLogEntry(event_type={self.event_type!r}, actor={self.actor!r})"
