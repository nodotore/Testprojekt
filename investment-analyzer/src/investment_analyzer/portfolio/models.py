"""ORM-Modelle: Watchlist und Portfolio (Auftrag §8 „Portfolio- und Vergleichsfunktionen").

Zwei getrennte, schlanke Modelle statt eines gemeinsamen mit optionalen
Feldern: eine Watchlist-Position trägt keine Bestandsdaten (Menge/
Einstandspreis), ein Portfolio-Bestand schon — eine nullable Menge würde
die beiden fachlich unterschiedlichen Konzepte („beobachten" vs.
„besitzen") künstlich vermischen.

Beide Modelle sind bewusst ein **Bestands-Snapshot**, keine
Transaktions-Historie (Auftrag §8 verlangt keine Kauf-/Verkaufshistorie,
nur den aktuellen Stand für Konzentrations-/Risikoanalysen) — je Entity
existiert höchstens eine Zeile; ein erneuter Import/eine erneute
manuelle Eingabe aktualisiert die bestehende Zeile statt eine weitere
anzulegen (siehe ``portfolio/csv_import.py``).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class WatchlistEntry(Base):
    """Eine beobachtete, aber (noch) nicht gehaltene Position."""

    __tablename__ = "watchlist_entries"
    __table_args__ = (UniqueConstraint("entity_id", name="uq_watchlist_entity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return f"WatchlistEntry(entity_id={self.entity_id!r})"


class PortfolioPosition(Base):
    """Eine tatsächlich gehaltene Position (Auftrag §8: „bestehendes Portfolio")."""

    __tablename__ = "portfolio_positions"
    __table_args__ = (UniqueConstraint("entity_id", name="uq_portfolio_entity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    average_cost: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Durchschnittlicher Einstandspreis je Stück, falls bekannt."
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        doc="Vom Nutzer angegebene Bestandswährung — nicht dieselbe Quelle wie der "
        "(bei Alpha Vantage unbekannte) Kurswährung, siehe DECISIONS.md ADR-20.",
    )
    acquired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return f"PortfolioPosition(entity_id={self.entity_id!r}, quantity={self.quantity!r})"
