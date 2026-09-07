"""ORM-Modell: provenienzbehaftete Nachrichten (Auftrag §5, §6 „Nachrichten", Milestone 5).

``NewsItem`` folgt demselben Provenienz-Grundprinzip wie ``DataPoint``
(``normalization/models.py``, ADR-6): jede Zeile referenziert ihre Quelle
(``source_id``) und trägt Abrufzeitpunkt (UTC) sowie einen Inhalts-Hash
zur Nachprüfbarkeit. Anders als ``DataPoint`` ist ``NewsItem`` kein
numerischer Fakt, sondern ein Textdokument-Verweis — deshalb ein eigenes
Modell statt einer Wiederverwendung von ``DataPoint``.

Bewusst NICHT gespeichert wird der volle Artikeltext (Urheberrecht,
Fair-Use-Grenzen der angebundenen Quellen) — nur Titel und ein kurzer,
HTML-bereinigter Ausschnitt (``summary_text``, siehe ``news/sanitize.py``).
Jeder Volltext bleibt über ``url`` nachvollziehbar (Auftrag §11).

``source_category`` und ``event_type`` werden deterministisch, regel-
basiert vergeben (``news/classification.py``) — nie durch ein
Sprachmodell (Auftrag §8a-Analogie).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class NewsSourceCategory:
    """Quellqualität (Auftrag §6 „Nachrichten"): Unternehmensmeldung vs. Dritte."""

    UNTERNEHMENSMELDUNG = "unternehmensmeldung"
    UNABHAENGIGER_BERICHT = "unabhaengiger_bericht"
    KOMMENTAR = "kommentar"

    ALL = (UNTERNEHMENSMELDUNG, UNABHAENGIGER_BERICHT, KOMMENTAR)


class NewsEventType:
    """Grobe, regelbasierte Ereignisklassifikation (Auftrag §6 „Nachrichten")."""

    EARNINGS = "earnings"
    MERGER_ACQUISITION = "merger_acquisition"
    MANAGEMENT = "management"
    LEGAL_REGULATORY = "legal_regulatory"
    CAPITAL_MARKETS = "capital_markets"
    PRODUCT_OPERATIONS = "product_operations"
    CYBER_SUPPLY_CHAIN = "cyber_supply_chain"
    SONSTIGES = "sonstiges"

    ALL = (
        EARNINGS,
        MERGER_ACQUISITION,
        MANAGEMENT,
        LEGAL_REGULATORY,
        CAPITAL_MARKETS,
        PRODUCT_OPERATIONS,
        CYBER_SUPPLY_CHAIN,
        SONSTIGES,
    )


class NewsItem(Base):
    """Ein einzelner, provenienzbehafteter Nachrichten-/Meldungs-Treffer."""

    __tablename__ = "news_items"
    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="uq_news_items_source_hash"),
        Index("ix_news_items_entity_published", "entity_id", "published_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="None, falls die Quelle kein verlässliches Datum liefert (nie geraten, Auftrag §11).",
    )
    retrieved_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    language: Mapped[str | None] = mapped_column(
        String(20), nullable=True, doc="Von der Quelle gemeldete Sprache, sofern vorhanden."
    )
    summary_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="HTML-bereinigter Kurz-Ausschnitt, kein Volltext (news/sanitize.py).",
    )

    source_category: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)

    content_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, doc="Hash der normalisierten URL — Grundlage der Idempotenz."
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return f"NewsItem(entity_id={self.entity_id!r}, title={self.title!r}, url={self.url!r})"
