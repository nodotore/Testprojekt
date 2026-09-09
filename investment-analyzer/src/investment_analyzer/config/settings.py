"""Anwendungsweite Einstellungen (Umgebung, Datenbank, Pfade).

Getrennt vom Nutzerprofil (``models.NutzerProfil``): Diese Einstellungen
betreffen die technische Laufzeitumgebung (Dev/Prod, DB-URL, Datenpfade),
nicht die fachlichen Analysepräferenzen des Nutzers.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    return Path.home() / "InvestmentAnalyzer"


class AppSettings(BaseSettings):
    """Liest Einstellungen aus Umgebungsvariablen (Präfix ``IA_``) oder ``.env``.

    Beispiel: ``IA_DATABASE_URL=postgresql+psycopg://...`` überschreibt
    den SQLite-Standardwert für den Produktivbetrieb (Auftrag §4).
    """

    model_config = SettingsConfigDict(env_prefix="IA_", env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    data_dir: Path = Field(default_factory=default_data_dir)
    database_url: str | None = Field(
        default=None,
        description=(
            "SQLAlchemy-URL. Wenn nicht gesetzt, wird eine lokale SQLite-Datei "
            "unter data_dir verwendet (Milestone-0-Entscheidung: lokal, Windows + SQLite)."
        ),
    )
    log_level: str = Field(default="INFO")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.data_dir / "investment_analyzer.db"
        return f"sqlite:///{db_path.as_posix()}"

    @property
    def profile_path(self) -> Path:
        return self.data_dir / "profile.json"

    @property
    def secrets_path(self) -> Path:
        return self.data_dir / "secrets.enc.json"

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def cache_dir(self) -> Path:
        """Lokaler Connector-Cache (``connectors/cache.py::FileCache``), z. B. für
        den Marktscreener (``ui/screener.py``)."""

        return self.data_dir / "cache"

    def ensure_data_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    """Gecachte Singleton-Instanz der Anwendungseinstellungen."""

    return AppSettings()
