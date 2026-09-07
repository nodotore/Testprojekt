"""Deterministische JSON-Serialisierung eines ``ReportBundle`` (Auftrag §2:
Ausgabeformat JSON).

Rein strukturelle Umwandlung — es werden keine neuen Werte berechnet
oder verändert (Auftrag §11). ``datetime``/``date`` werden als ISO-8601-
Strings serialisiert, ``Entity``-Referenzen (z. B. Peers) auf die für den
Bericht relevanten Felder reduziert statt das komplette ORM-Objekt
(inkl. interner SQLAlchemy-Zustände) zu dumpen.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from typing import Any

from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.reports.bundle import ReportBundle


def _entity_to_dict(entity: Entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "name": entity.name,
        "country": entity.country,
        "primary_exchange": entity.primary_exchange,
        "sic_code": entity.sic_code,
        "sic_description": entity.sic_description,
    }


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Entity):
        return _entity_to_dict(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {
            (key if isinstance(key, str) else str(key)): _to_jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    raise TypeError(f"Nicht JSON-serialisierbarer Typ: {type(value)!r}")


def report_bundle_to_dict(bundle: ReportBundle) -> dict[str, Any]:
    """Wandelt ein ``ReportBundle`` vollständig in JSON-taugliche Python-Werte um."""

    result = _to_jsonable(bundle)
    assert isinstance(result, dict)
    return result


def report_bundle_to_json(bundle: ReportBundle, *, indent: int | None = 2) -> str:
    return json.dumps(report_bundle_to_dict(bundle), indent=indent, ensure_ascii=False, sort_keys=True)
