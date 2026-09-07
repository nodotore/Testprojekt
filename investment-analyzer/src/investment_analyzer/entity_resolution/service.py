"""Find-or-create-Service für stabile Unternehmens-Identitäten (Auftrag §5).

Zentrale Regel: **Ticker werden nie allein als globale Identität
verwendet.** ``find_or_create_entity`` verlangt mindestens eine stabile
Kennung (ISIN, LEI oder — als Übergangslösung für SEC-EDGAR-Daten ohne
ISIN — die SEC-eigene CIK) und weist andernfalls ab. Ticker dürfen
zusätzlich mitgegeben werden, dienen aber nur als bequeme Sekundärsuche/
-anzeige, nie als alleiniges Abgleichskriterium.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.entity_resolution.models import Entity, EntityIdentifier, IdentifierType

#: Kennungstypen, die für sich genommen als globale Identität ausreichen (Auftrag §5).
STABLE_IDENTIFIER_TYPES = frozenset(
    {IdentifierType.ISIN, IdentifierType.LEI, IdentifierType.CIK}
)


@dataclass(frozen=True)
class IdentifierSpec:
    id_type: str
    id_value: str
    exchange: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None


def find_entity_by_identifier(
    session: Session, id_type: str, id_value: str, *, exchange: str | None = None
) -> Entity | None:
    """Sucht eine ``Entity`` über genau eine externe Kennung."""

    query = select(EntityIdentifier).where(
        EntityIdentifier.id_type == id_type, EntityIdentifier.id_value == id_value
    )
    if exchange is not None:
        query = query.where(EntityIdentifier.exchange == exchange)
    row = session.scalars(query).first()
    return row.entity if row is not None else None


def find_or_create_entity(
    session: Session,
    *,
    name: str,
    identifiers: Sequence[IdentifierSpec],
    country: str | None = None,
    primary_exchange: str | None = None,
) -> Entity:
    """Findet eine bestehende ``Entity`` über eine stabile Kennung oder legt eine neue an.

    Ergänzt bei jedem Aufruf fehlende Kennungen aus ``identifiers`` an der
    (gefundenen oder neuen) Entity — so sammelt eine Entity im Zeitverlauf
    z. B. sowohl CIK als auch ISIN, sobald beide Quellen verfügbar sind.
    """

    if not identifiers:
        raise ValueError(
            "Mindestens eine externe Kennung ist erforderlich, um eine Entity anzulegen."
        )
    stable_specs = [spec for spec in identifiers if spec.id_type in STABLE_IDENTIFIER_TYPES]
    if not stable_specs:
        raise ValueError(
            "Mindestens eine stabile Kennung (ISIN, LEI oder CIK) ist erforderlich — "
            "ein Ticker allein darf nie als globale Identität verwendet werden (Auftrag §5)."
        )

    for spec in stable_specs:
        existing = find_entity_by_identifier(session, spec.id_type, spec.id_value, exchange=spec.exchange)
        if existing is not None:
            _ensure_identifiers(session, existing, identifiers)
            return existing

    entity = Entity(name=name, country=country, primary_exchange=primary_exchange)
    session.add(entity)
    session.flush()  # Entity-ID wird für die Identifier-Zeilen benötigt.
    _ensure_identifiers(session, entity, identifiers)
    return entity


def _ensure_identifiers(
    session: Session, entity: Entity, identifiers: Sequence[IdentifierSpec]
) -> None:
    for spec in identifiers:
        already_present = session.scalars(
            select(EntityIdentifier).where(
                EntityIdentifier.entity_id == entity.id,
                EntityIdentifier.id_type == spec.id_type,
                EntityIdentifier.id_value == spec.id_value,
                EntityIdentifier.exchange == spec.exchange,
            )
        ).first()
        if already_present is None:
            session.add(
                EntityIdentifier(
                    entity_id=entity.id,
                    id_type=spec.id_type,
                    id_value=spec.id_value,
                    exchange=spec.exchange,
                    valid_from=spec.valid_from,
                    valid_to=spec.valid_to,
                )
            )
