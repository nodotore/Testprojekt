"""Seiten-Datei für ``st.navigation()``: Nachrichten/Ereignisse (Auftrag §10, Seite 7)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.news import render_nachrichten

ctx = get_context()
profil = require_profile(ctx)
render_nachrichten(ctx, profil)
