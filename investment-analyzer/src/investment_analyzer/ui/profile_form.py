"""UI-unabhängige Logik des Ersteinrichtungsdialogs (Auftrag §2).

Von ``app.py`` verwendet, aber bewusst ohne Streamlit-Import, damit sie
mit gewöhnlichem ``pytest`` (ohne Streamlit-Laufzeitkontext) getestet
werden kann.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from investment_analyzer.config.models import NutzerProfil


def split_csv(text: str) -> list[str]:
    """Zerlegt eine kommagetrennte Texteingabe in eine bereinigte Liste."""

    return [teil.strip() for teil in text.split(",") if teil.strip()]


def build_profile_from_form(data: dict[str, Any]) -> NutzerProfil:
    """Baut ein validiertes ``NutzerProfil`` aus den rohen Formularwerten.

    Wirft ``pydantic.ValidationError``, falls die Eingaben ungültig sind
    (z. B. Mindest- > Höchstmarktkapitalisierung) — der Aufrufer (UI)
    fängt dies ab und zeigt die Meldung dem Nutzer an, statt ein
    unvollständiges Profil zu speichern.
    """

    return NutzerProfil(
        profil_name=data["profil_name"],
        anlageregionen=data["anlageregionen"],
        boersen=data["boersen"],
        branchen=split_csv(data.get("branchen", "")),
        ausschlussbranchen=split_csv(data.get("ausschlussbranchen", "")),
        ausschlusswerte=split_csv(data.get("ausschlusswerte", "")),
        anlagehorizont=data["anlagehorizont"],
        risikoklasse=data["risikoklasse"],
        stil=data["stil"],
        waehrung=data["waehrung"],
        vergleichsindex=data["vergleichsindex"],
        marktkap_min_mio=data.get("marktkap_min_mio") or None,
        marktkap_max_mio=data.get("marktkap_max_mio") or None,
        positionsgroesse_max_prozent=data["positionsgroesse_max_prozent"],
        kandidatenzahl_ziel=data["kandidatenzahl_ziel"],
        microcaps_ausschliessen=data["microcaps_ausschliessen"],
        pennystocks_ausschliessen=data["pennystocks_ausschliessen"],
        illiquide_ausschliessen=data["illiquide_ausschliessen"],
        speicherort=Path(data["speicherort"]),
        ausgabeformate=data["ausgabeformate"],
        konfigurierte_quellen=data.get("konfigurierte_quellen", []),
        sec_edgar_kontakt_email=data.get("sec_edgar_kontakt_email") or None,
        haftungsausschluss_akzeptiert=data["haftungsausschluss_akzeptiert"],
    )
