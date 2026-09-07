"""Dateibasierter Antwort-Cache mit TTL (Auftrag §4: „Cache").

Wichtig (Auftrag §4, SECURITY.md): Ein abgelaufener Cache-Eintrag wird
NIE stillschweigend als aktuell zurückgegeben. ``get()`` liefert nur
innerhalb der TTL gültige Einträge; ist der Eintrag abgelaufen oder nicht
vorhanden, liefert ``get()`` ``None`` — die Entscheidung, was dann
passiert (neuer Live-Abruf, oder Fehler falls dieser fehlschlägt), trifft
``base.Connector``, nicht der Cache selbst.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from investment_analyzer.db.types import utc_now


@dataclass(frozen=True)
class CacheEntry:
    data: Any
    fetched_at_utc: datetime
    ttl_seconds: int
    status_code: int

    def is_fresh(self, *, now: datetime | None = None) -> bool:
        reference = now or utc_now()
        age_seconds = (reference - self.fetched_at_utc).total_seconds()
        return 0 <= age_seconds < self.ttl_seconds

    def age_seconds(self, *, now: datetime | None = None) -> float:
        reference = now or utc_now()
        return (reference - self.fetched_at_utc).total_seconds()


def cache_key_for(url: str, params: dict[str, Any] | None) -> str:
    """Deterministischer Cache-Schlüssel aus URL + sortierten Query-Parametern."""

    payload = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FileCache:
    """Ein Cache-Eintrag pro Datei unter ``base_dir/<source_key>/<cache_key>.json``."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def _path_for(self, source_key: str, key: str) -> Path:
        return self._base_dir / source_key / f"{key}.json"

    def get(self, source_key: str, key: str) -> CacheEntry | None:
        path = self._path_for(source_key, key)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry(
                data=raw["data"],
                fetched_at_utc=datetime.fromisoformat(raw["fetched_at_utc"]),
                ttl_seconds=raw["ttl_seconds"],
                status_code=raw["status_code"],
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # Korrupter Cache-Eintrag: als „nicht vorhanden" behandeln, niemals als gültig.
            return None
        return entry if entry.is_fresh() else None

    def set(self, source_key: str, key: str, entry: CacheEntry) -> None:
        path = self._path_for(source_key, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "data": entry.data,
            "fetched_at_utc": entry.fetched_at_utc.isoformat(),
            "ttl_seconds": entry.ttl_seconds,
            "status_code": entry.status_code,
        }
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".cache-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file)
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
