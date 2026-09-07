"""Vorgeschlagene Standardwerte für das Nutzerprofil.

Diese Werte entsprechen den in ``investment-analyzer/MILESTONE_0.md``
(Abschnitt B) mit dem Nutzer abgestimmten Vorschlägen. Sie werden beim
Ersteinrichtungsdialog vorbelegt und sind dort änderbar (Auftrag §2).
"""

from __future__ import annotations

from investment_analyzer.config.models import (
    Anlagehorizont,
    Anlagestil,
    NutzerProfil,
    Risikoklasse,
)


def default_profile() -> NutzerProfil:
    """Erzeugt ein Nutzerprofil mit den abgestimmten Startwerten.

    Marktauswahl gemäß Milestone-0-Entscheidung (ADR-9): breit, ohne
    initiale Einschränkung (USA, Deutschland, übriges Europa).
    """

    return NutzerProfil(
        anlageregionen=["USA", "Deutschland", "Übriges Europa"],
        boersen=["NYSE", "NASDAQ", "XETRA"],
        anlagehorizont=Anlagehorizont.MITTELFRISTIG,
        risikoklasse=Risikoklasse.AUSGEWOGEN,
        stil=[Anlagestil.MISCHUNG],
        waehrung="EUR",
        vergleichsindex="MSCI World",
        konfigurierte_quellen=["sec_edgar", "alpha_vantage"],
    )
