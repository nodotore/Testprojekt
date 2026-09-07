"""ORM-Modell: registrierte Datenquellen (Connectoren).

Jede Zeile entspricht einer Quelle aus ``DATA_SOURCES.md`` (Quellen-
/Lizenzmatrix). ``DataPoint`` (siehe ``normalization/models.py``)
referenziert genau eine ``Source`` je Datenpunkt (Auftrag §5: Quelle,
direkte URL, Dokumenttyp, Lizenzhinweis).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from investment_analyzer.db import Base
from investment_analyzer.db.types import new_uuid, utc_now


class Source(Base):
    """Eine in ``DATA_SOURCES.md`` dokumentierte, angebundene Datenquelle."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    #: Kurzname, z. B. "sec_edgar", "alpha_vantage" — referenziert in NutzerProfil.konfigurierte_quellen.
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    license_note: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Lizenzhinweis/Nutzungsbedingungen (Auftrag §4)."
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Source(key={self.key!r})"
