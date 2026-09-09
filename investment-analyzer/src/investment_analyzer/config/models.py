"""Nutzerprofil-Datenmodell gemäß Auftrag §2 (Startdialog).

Dieses Modell wird beim ersten Programmstart über den
Ersteinrichtungsdialog befüllt und ist danach jederzeit über die
Einstellungsseite änderbar (siehe Auftrag §10, Seite 10). Es enthält
bewusst KEINE API-Schlüssel im Klartext — diese werden ausschließlich
über den ``SecretStore`` (siehe ``investment_analyzer.audit`` /
``investment_analyzer.config.secrets``) verwaltet; das Profil speichert
nur, welche Quellen konfiguriert *sind* (Referenz per Quellenname).
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class Anlagehorizont(StrEnum):
    KURZFRISTIG = "kurzfristig"
    MITTELFRISTIG = "mittelfristig"
    LANGFRISTIG = "langfristig"


class Risikoklasse(StrEnum):
    DEFENSIV = "defensiv"
    AUSGEWOGEN = "ausgewogen"
    CHANCENORIENTIERT = "chancenorientiert"


class Anlagestil(StrEnum):
    VALUE = "value"
    QUALITAET = "qualitaet"
    WACHSTUM = "wachstum"
    DIVIDENDE = "dividende"
    MISCHUNG = "mischung"


class Ausgabeformat(StrEnum):
    DASHBOARD = "dashboard"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"


#: Standardmäßig alle vier Ausgabeformate aktiv (Auftrag §2).
ALLE_AUSGABEFORMATE: tuple[Ausgabeformat, ...] = tuple(Ausgabeformat)


class NutzerProfil(BaseModel):
    """Änderbares Analyseprofil eines Nutzers.

    Alle Felder entsprechen den in Auftrag §2 geforderten Angaben des
    Startdialogs. Geldbeträge (Marktkapitalisierung) werden in der
    unter ``waehrung`` angegebenen Einheit, in Millionen, gespeichert.
    """

    model_config = {"extra": "forbid"}

    profil_name: str = Field(default="Standard", min_length=1, max_length=100)

    # Märkte
    anlageregionen: list[str] = Field(
        default_factory=list,
        description="Z. B. ['USA', 'Deutschland', 'Übriges Europa'].",
    )
    boersen: list[str] = Field(
        default_factory=list,
        description="Z. B. ['NYSE', 'NASDAQ', 'XETRA'].",
    )

    # Branchen
    branchen: list[str] = Field(default_factory=list, description="Leer = alle Branchen.")
    ausschlussbranchen: list[str] = Field(default_factory=list)
    ausschlusswerte: list[str] = Field(
        default_factory=list, description="Ticker/ISIN einzelner ausgeschlossener Werte."
    )

    # Anlagepräferenzen
    anlagehorizont: Anlagehorizont = Anlagehorizont.MITTELFRISTIG
    risikoklasse: Risikoklasse = Risikoklasse.AUSGEWOGEN
    stil: list[Anlagestil] = Field(default_factory=lambda: [Anlagestil.MISCHUNG])

    # Referenzwerte
    waehrung: str = Field(default="EUR", min_length=3, max_length=3)
    vergleichsindex: str = Field(default="MSCI World")

    # Marktkapitalisierung (in Mio. der gewählten Währung)
    marktkap_min_mio: float | None = Field(
        default=1000.0,
        ge=0,
        description="Mindestmarktkapitalisierung; Standard schließt Microcaps aus (Auftrag §2).",
    )
    marktkap_max_mio: float | None = Field(default=None, ge=0)

    # Positionsgrößen und Kandidatenzahl
    positionsgroesse_max_prozent: float = Field(
        default=5.0,
        gt=0,
        le=100,
        description="Maximale Positionsgröße als unverbindliche Bandbreitenobergrenze (% Portfolio).",
    )
    kandidatenzahl_ziel: int = Field(default=10, ge=1, le=50)

    # Ausschlusskriterien (Auftrag §2, Standardverhalten)
    microcaps_ausschliessen: bool = True
    pennystocks_ausschliessen: bool = True
    illiquide_ausschliessen: bool = True
    mindest_datenqualitaet_erforderlich: bool = True

    # Ausgabe
    speicherort: Path = Field(default_factory=lambda: default_speicherort())
    ausgabeformate: list[Ausgabeformat] = Field(
        default_factory=lambda: list(ALLE_AUSGABEFORMATE)
    )

    # Konfigurierte Datenquellen (nur Referenz auf Quellennamen, keine Secrets)
    konfigurierte_quellen: list[str] = Field(default_factory=list)

    sec_edgar_kontakt_email: str | None = Field(
        default=None,
        description=(
            "Kontaktadresse für den SEC-EDGAR-User-Agent-Header (SEC-Pflichtangabe, "
            "siehe DATA_SOURCES.md) — wird bei jedem SEC-EDGAR-Abruf im Marktscreener "
            "verwendet. Bewusst ein eigenes, ausdrücklich vom Nutzer gesetztes Feld statt "
            "automatisch aus dem Anmeldekonto übernommen (Auftrag §12: keine Daten an "
            "Dritte ohne ausdrückliche Zustimmung)."
        ),
    )

    haftungsausschluss_akzeptiert: bool = Field(
        default=False,
        description=(
            "Muss vor erster Nutzung bestätigt werden: allgemeine Information, "
            "keine individuelle Anlage-, Steuer- oder Rechtsberatung, "
            "Verluste bis zum Totalverlust möglich (Auftrag §12)."
        ),
    )

    @field_validator("waehrung")
    @classmethod
    def _waehrung_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("sec_edgar_kontakt_email")
    @classmethod
    def _sec_edgar_kontakt_email_grobformat(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        if "@" not in stripped or stripped.startswith("@") or stripped.endswith("@"):
            raise ValueError("sec_edgar_kontakt_email sieht nicht wie eine E-Mail-Adresse aus.")
        return stripped

    @field_validator("stil")
    @classmethod
    def _stil_nicht_leer(cls, v: list[Anlagestil]) -> list[Anlagestil]:
        if not v:
            raise ValueError("Mindestens ein Anlagestil muss angegeben werden.")
        return v

    @field_validator("ausgabeformate")
    @classmethod
    def _ausgabeformate_nicht_leer(cls, v: list[Ausgabeformat]) -> list[Ausgabeformat]:
        if not v:
            raise ValueError("Mindestens ein Ausgabeformat muss aktiv sein.")
        return v

    @model_validator(mode="after")
    def _marktkap_range_konsistent(self) -> NutzerProfil:
        if (
            self.marktkap_min_mio is not None
            and self.marktkap_max_mio is not None
            and self.marktkap_min_mio > self.marktkap_max_mio
        ):
            raise ValueError(
                "marktkap_min_mio darf nicht größer als marktkap_max_mio sein."
            )
        return self


def default_speicherort() -> Path:
    """Standard-Speicherort für Berichte/Exporte (änderbar im Ersteinrichtungsdialog)."""

    return Path.home() / "InvestmentAnalyzer" / "reports"
