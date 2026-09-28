"""Seiten-Datei für ``st.navigation()``: Backtest (Auftrag §10, Seite 9)."""

from __future__ import annotations

from investment_analyzer.ui.backtest import render_backtest
from investment_analyzer.ui.context import get_context, require_profile

ctx = get_context()
profil = require_profile(ctx)
render_backtest(ctx, profil)
