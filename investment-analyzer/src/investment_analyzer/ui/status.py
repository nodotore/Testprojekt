"""Wahrheitsgemäßer Datenstatus für die Seite „Start/Datenstatus" (Auftrag §10).

Zeigt ausschließlich tatsächlich in der Datenbank vorhandene Zahlen an.
Solange keine Connectoren angebunden sind (Milestone 2), sind das
Nullen — es werden NIEMALS Platzhalterzahlen angezeigt, die wie echte
aktuelle Marktdaten aussehen (Auftrag §16).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from investment_analyzer.audit.models import AuditLogEntry
from investment_analyzer.connectors.models import Source
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.normalization.models import DataPoint


@dataclass
class DatenStatus:
    anzahl_unternehmen: int
    anzahl_quellen: int
    anzahl_datenpunkte: int
    letzte_aktivitaet_utc: datetime | None


def lade_datenstatus(session_factory: sessionmaker[Session]) -> DatenStatus:
    with session_factory() as session:
        anzahl_unternehmen = session.scalar(select(func.count()).select_from(Entity)) or 0
        anzahl_quellen = session.scalar(select(func.count()).select_from(Source)) or 0
        anzahl_datenpunkte = session.scalar(select(func.count()).select_from(DataPoint)) or 0
        letzte_aktivitaet = session.scalar(select(func.max(AuditLogEntry.timestamp_utc)))

    return DatenStatus(
        anzahl_unternehmen=anzahl_unternehmen,
        anzahl_quellen=anzahl_quellen,
        anzahl_datenpunkte=anzahl_datenpunkte,
        letzte_aktivitaet_utc=letzte_aktivitaet,
    )
