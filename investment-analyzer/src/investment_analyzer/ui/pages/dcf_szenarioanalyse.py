"""Seiten-Datei für ``st.navigation()``: DCF- und Szenarioanalyse (Auftrag §10, Seite 6)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.dcf import render_dcfanalyse

ctx = get_context()
profil = require_profile(ctx)
render_dcfanalyse(ctx, profil)
