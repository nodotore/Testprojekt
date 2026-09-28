"""Seiten-Datei für ``st.navigation()``: Unternehmensdetail mit Quellenleiste (Auftrag §10, Seite 4)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.detail import render_unternehmensdetail

ctx = get_context()
profil = require_profile(ctx)
render_unternehmensdetail(ctx, profil)
