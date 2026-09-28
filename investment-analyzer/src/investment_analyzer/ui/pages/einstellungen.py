"""Seiten-Datei für ``st.navigation()``: Einstellungen, Quellen und Prüfprotokoll (Auftrag §10, Seite 10)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.settings import render_einstellungen

ctx = get_context()
profil = require_profile(ctx)
render_einstellungen(ctx, profil)
