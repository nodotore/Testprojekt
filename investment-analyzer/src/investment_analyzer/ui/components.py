"""Über mehrere Seiten geteilte UI-Bausteine (Auftrag §10, §12).

Ausgelagert aus ``app.py``, damit ``screener.py`` (und künftige weitere
Seiten) denselben Pflichthinweis zeigen können, ohne ``app.py`` zu
importieren (vermeidet einen Zirkelimport).
"""

from __future__ import annotations

import streamlit as st

DISCLAIMER = (
    "⚠️ **Nur allgemeine Information — keine Anlageberatung.** Dieses Programm "
    "liefert Research-Ergebnisse im Simulationsmodus, keine individuelle Anlage-, "
    "Steuer- oder Rechtsberatung und keine Kauf-/Verkaufsempfehlung. Es werden keine "
    "Wertpapiere automatisch gehandelt. Investitionen in Wertpapiere können bis zum "
    "Totalverlust des eingesetzten Kapitals führen."
)


def render_disclaimer() -> None:
    st.warning(DISCLAIMER)
