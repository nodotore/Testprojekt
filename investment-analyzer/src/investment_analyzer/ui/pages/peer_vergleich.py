"""Seiten-Datei für ``st.navigation()``: Peer-Vergleich (Auftrag §10, Seite 5)."""

from __future__ import annotations

from investment_analyzer.ui.context import get_context, require_profile
from investment_analyzer.ui.peers import render_peervergleich

ctx = get_context()
profil = require_profile(ctx)
render_peervergleich(ctx, profil)
