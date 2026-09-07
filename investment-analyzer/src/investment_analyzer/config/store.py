"""Laden und Speichern des Nutzerprofils als JSON-Datei.

Atomarer Schreibvorgang (Schreiben in Temp-Datei + ``os.replace``), damit
ein Absturz während des Speicherns keine korrupte Profildatei hinterlässt
(Auftrag §13: Sitzungsende darf keinen Wissensverlust verursachen —
gilt sinngemäß auch für Nutzerdaten).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from investment_analyzer.config.models import NutzerProfil


class ProfileStore:
    """Persistiert genau ein ``NutzerProfil`` unter einem festen Pfad."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> NutzerProfil:
        if not self.exists():
            raise FileNotFoundError(
                f"Kein Nutzerprofil unter {self._path} gefunden. "
                "Ersteinrichtungsdialog muss zuerst durchlaufen werden."
            )
        data = self._path.read_text(encoding="utf-8")
        return NutzerProfil.model_validate_json(data)

    def load_or_none(self) -> NutzerProfil | None:
        if not self.exists():
            return None
        return self.load()

    def save(self, profile: NutzerProfil) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = profile.model_dump_json(indent=2)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=".profile-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(payload)
            os.replace(tmp_name, self._path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
