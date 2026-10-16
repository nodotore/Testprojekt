"""Seiten-Datei für ``st.navigation()``: Ersteinrichtungsdialog (Auftrag §2).

Einziger Eintrag der Navigation, solange noch kein akzeptiertes Profil
vorliegt (siehe ``app.py::main()``) — ``st.navigation()`` blendet die
Seitenleiste bei nur einer Seite ohnehin aus, der Dialog erscheint also
wie zuvor ohne sichtbares Seitenmenü.
"""

from __future__ import annotations

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.ui.context import get_context
from investment_analyzer.ui.start import render_ersteinrichtungsdialog

ctx = get_context()
profil = ctx.profile_store.load_or_none()
render_ersteinrichtungsdialog(ctx, vorbelegung=profil or default_profile())
