"""Seiten-Datei für ``st.navigation()``: Start / Datenstatus (Auftrag §10, Seite 1)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.start import render_datenstatus

ctx = get_context()
profil = require_profile(ctx)
render_datenstatus(ctx, profil)
