"""Stabile Unternehmens-Identität: Ticker/ISIN/LEI/CIK → interne Entity-ID (Auftrag §5).

Siehe ``models.py`` für das Datenmodell und ``service.py`` für den
Find-or-create-Service (Ticker werden nie allein als globale Identität
verwendet).
"""

from investment_analyzer.entity_resolution.models import Entity, EntityIdentifier, IdentifierType
from investment_analyzer.entity_resolution.service import (
    STABLE_IDENTIFIER_TYPES,
    IdentifierSpec,
    find_entity_by_identifier,
    find_or_create_entity,
)

__all__ = [
    "STABLE_IDENTIFIER_TYPES",
    "Entity",
    "EntityIdentifier",
    "IdentifierSpec",
    "IdentifierType",
    "find_entity_by_identifier",
    "find_or_create_entity",
]
