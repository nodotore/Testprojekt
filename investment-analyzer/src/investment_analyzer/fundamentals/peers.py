"""Peer-Gruppen-Zuordnung (Auftrag §6: „Vergleich mit ... passenden Branchenunternehmen").

Erster, einfacher Ansatz für Milestone 3: Unternehmen mit identischem
SIC-Code (US-Branchenklassifikation, aus SEC-Submissions über
``normalization.ingest.update_entity_classification`` befüllt) gelten
als Peers. Eine zusätzliche Größenähnlichkeit (Marktkapitalisierung) ist
erst ab Milestone 4 möglich, sobald Kursdaten mit Marktkapitalisierung
verknüpft sind — bis dahin ist dies eine reine Branchen-, keine
größenbereinigte Peer-Gruppe.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.entity_resolution.models import Entity


def find_peers(session: Session, entity: Entity, *, limit: int = 10) -> list[Entity]:
    """Liefert bis zu ``limit`` andere Entities mit demselben SIC-Code.

    Liefert eine leere Liste, wenn ``entity`` (noch) keinen SIC-Code hat
    — es gibt bewusst keine Ersatz-Peer-Gruppe ohne Branchenklassifikation
    (kein Rateergebnis, Auftrag §11).
    """

    if not entity.sic_code:
        return []

    return list(
        session.scalars(
            select(Entity)
            .where(Entity.sic_code == entity.sic_code, Entity.id != entity.id)
            .order_by(Entity.name)
            .limit(limit)
        )
    )
