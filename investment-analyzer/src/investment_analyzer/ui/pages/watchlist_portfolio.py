"""Seiten-Datei für ``st.navigation()``: Watchlist/Portfolio (Auftrag §10, Seite 8)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.watchlist import render_watchlist_portfolio

ctx = get_context()
profil = require_profile(ctx)
render_watchlist_portfolio(ctx, profil)
