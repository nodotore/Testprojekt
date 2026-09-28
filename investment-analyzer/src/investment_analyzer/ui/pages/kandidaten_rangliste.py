"""Seiten-Datei für ``st.navigation()``: Kandidaten-Rangliste (Auftrag §10, Seite 3)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.ranking import render_kandidatenrangliste

ctx = get_context()
profil = require_profile(ctx)
render_kandidatenrangliste(ctx, profil)
