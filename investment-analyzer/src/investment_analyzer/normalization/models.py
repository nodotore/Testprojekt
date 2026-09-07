"""ORM-Modell: provenienzbehafteter Datenpunkt (Kernmodell, Auftrag §5).

``DataPoint`` ist bewusst append-only: bestehende Zeilen werden nie
verändert oder gelöscht (außer expliziten DSGVO-/Bereinigungsfällen
außerhalb dieses Kernmodells). Eine Korrektur oder ein Restatement wird
als NEUE Zeile mit neuem ``retrieved_at_utc`` gespeichert. Dadurch bleibt
jede Point-in-time-Abfrage möglich: „Welcher Wert war zum Zeitpunkt X
bekannt?" = ``WHERE ... AND retrieved_at_utc <= X ORDER BY
retrieved_at_utc DESC LIMIT 1`` (Voraussetzung für Look-ahead-freie
Backtests, Auftrag §9, ADR-6).

Jedes Feld hier entspricht direkt einer Vorgabe aus Auftrag §5:
Unternehmen (``entity_id``), Wert/Einheit/Währung/Berichtsperiode, Veröffentlichungsdatum
und Abrufzeitpunkt (UTC), Quelle/URL/Dokumenttyp (``source_id``,
``document_url``, ``document_type``), Rohwert und normalisierter Wert,
geschätzt/gemeldet/berechnet (``value_kind``), Qualität/Konfidenz,
Hash/Dokument-ID zur Nachprüfbarkeit.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class ValueKind:
    """Erlaubte Werte für ``DataPoint.value_kind`` (Auftrag §5)."""

    REPORTED = "reported"
    ESTIMATED = "estimated"
    CALCULATED = "calculated"

    ALL = (REPORTED, ESTIMATED, CALCULATED)


class DataPoint(Base):
    """Ein einzelner, provenienzbehafteter Datenpunkt."""

    __tablename__ = "data_points"
    __table_args__ = (
        Index("ix_data_points_entity_metric_period", "entity_id", "metric_name", "period_end"),
        Index("ix_data_points_point_in_time", "entity_id", "metric_name", "retrieved_at_utc"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
    )

    #: Kennzahlen-Namensraum wird ab Milestone 3 im ``fundamentals``-Modul verbindlich definiert.
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)

    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)

    published_at: Mapped[date] = mapped_column(Date, nullable=False)
    retrieved_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    value_raw: Mapped[str] = mapped_column(Text, nullable=False)
    value_normalized: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    value_kind: Mapped[str] = mapped_column(String(20), nullable=False)

    quality_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="0..1, Datenqualität (Vollständigkeit/Plausibilität)."
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="0..1, Konfidenz in den Wert (u. a. Aktualität, Quellenlage)."
    )

    document_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, doc="Hash des Quelldokuments/-inhalts zur Nachprüfbarkeit."
    )
    document_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DataPoint(entity_id={self.entity_id!r}, metric_name={self.metric_name!r}, "
            f"value_normalized={self.value_normalized!r}, value_kind={self.value_kind!r})"
        )
