"""Seiten-Datei für ``st.navigation()``: Marktscreener (Auftrag §10, Seite 2)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.screener import render_marktscreener

ctx = get_context()
profil = require_profile(ctx)
render_marktscreener(ctx, profil)
