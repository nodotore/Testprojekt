"""ORM-Modelle: stabile Unternehmens-Identität (Auftrag §5).

``Entity`` ist die interne, stabile Identität eines Unternehmens.
``EntityIdentifier`` bildet die N:1-Beziehung zu externen Kennungen
(Ticker, ISIN, LEI, CIK, ...) ab — inklusive Gültigkeitszeitraum, da sich
z. B. Ticker durch Umbenennung/Börsenwechsel ändern können. Ticker werden
NIE allein als globale Identität verwendet (Auftrag §5); jede Zuordnung
externer Daten zu einer ``Entity`` muss über eine hier gepflegte,
möglichst stabile Kennung (bevorzugt ISIN oder LEI) erfolgen.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class Entity(Base):
    """Ein börsennotiertes Unternehmen (oder eine Notierung davon) als stabile Entität."""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    primary_exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    #: SEC Standard Industrial Classification — Grundlage für die Peer-Gruppen-Zuordnung
    #: (Auftrag §6, Milestone 3). Wird aus SecSubmissions befüllt, siehe
    #: normalization/ingest.py::update_entity_classification.
    sic_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sic_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    identifiers: Mapped[list[EntityIdentifier]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - Diagnosehilfe
        return f"Entity(id={self.id!r}, name={self.name!r})"


class IdentifierType:
    """Bekannte Kennungstypen (kein Enum, da Erweiterung ohne Migration möglich bleiben soll)."""

    TICKER = "ticker"
    ISIN = "isin"
    LEI = "lei"
    CIK = "cik"  # SEC EDGAR Central Index Key


class EntityIdentifier(Base):
    """Externe Kennung einer ``Entity``, mit optionalem Gültigkeitszeitraum."""

    __tablename__ = "entity_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "id_type", "id_value", "exchange", "valid_from", name="uq_identifier_scope"
        ),
        Index("ix_entity_identifiers_lookup", "id_type", "id_value"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    id_type: Mapped[str] = mapped_column(String(20), nullable=False)
    id_value: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    entity: Mapped[Entity] = relationship(back_populates="identifiers")

    def __repr__(self) -> str:  # pragma: no cover
        return f"EntityIdentifier({self.id_type}={self.id_value!r} -> {self.entity_id!r})"
