"""Gemeinsame, dialektunabhängige Hilfstypen für ORM-Modelle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime


def new_uuid() -> str:
    """Neue UUID4 als String (36 Zeichen) — funktioniert identisch unter SQLite und PostgreSQL."""

    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Zeitzonenbewusster UTC-Zeitstempel (Auftrag §5: Abrufzeitpunkt in UTC)."""

    return datetime.now(UTC)
