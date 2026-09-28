"""Streamlit-Einstiegspunkt: Router für ``st.navigation()``.

Prüft Datenbank-Migration und Nutzerprofil (Auftrag §2), zeigt bis dahin
den Ersteinrichtungsdialog (``ui/start.py``). Sobald ein akzeptiertes
Profil vorliegt, bindet ``st.navigation()`` alle zehn Auftrag-§10-Seiten
als eigene Dateien unter ``ui/pages/`` ein — abgelöst vom ursprünglichen
``st.sidebar.radio``-Muster (ADR-26, inzwischen auf zehn Einträge
gewachsen), weil erst eine dateibasierte Seite mit
``AppTest.switch_page()`` testbar ist (siehe ADR-35).

Jede Seiten-Datei ruft ausschließlich ``ui/context.py::get_context()``
(gecacht, identische Instanz wie hier) und die jeweilige
``render_*``-Funktion auf — nie ``app.py`` selbst, um den erneuten Aufruf
von ``main()`` beim Import zu vermeiden.

Start: ``streamlit run src/investment_analyzer/ui/app.py`` (siehe
``start.ps1``/``start.bat`` im Projektstamm für den vollständigen
Windows-Startvorgang inkl. Migrationen).
"""

from __future__ import annotations

import streamlit as st

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.ui.bootstrap import check_database_ready
from investment_analyzer.ui.context import get_context
from investment_analyzer.ui.start import render_ersteinrichtungsdialog

_PAGES = [
    st.Page("pages/start.py", title="Start / Datenstatus", default=True),
    st.Page("pages/marktscreener.py", title="Marktscreener"),
    st.Page("pages/kandidaten_rangliste.py", title="Kandidaten-Rangliste"),
    st.Page("pages/unternehmensdetail.py", title="Unternehmensdetail"),
    st.Page("pages/peer_vergleich.py", title="Peer-Vergleich"),
    st.Page("pages/dcf_szenarioanalyse.py", title="DCF- und Szenarioanalyse"),
    st.Page("pages/nachrichten_ereignisse.py", title="Nachrichten/Ereignisse"),
    st.Page("pages/watchlist_portfolio.py", title="Watchlist/Portfolio"),
    st.Page("pages/backtest.py", title="Backtest"),
    st.Page("pages/einstellungen.py", title="Einstellungen, Quellen und Prüfprotokoll"),
]


def main() -> None:
    st.set_page_config(page_title="Investment-Analysator", page_icon="📊", layout="wide")
    st.title("Investment-Analysator")

    ctx = get_context()

    if not check_database_ready(ctx.engine):
        st.error(
            "Die Datenbank ist noch nicht migriert. Bitte `start.ps1`/`start.bat` "
            "ausführen (führt `alembic upgrade head` vor dem Start der Oberfläche aus)."
        )
        st.stop()

    profil = ctx.profile_store.load_or_none()
    if profil is None or not profil.haftungsausschluss_akzeptiert:
        render_ersteinrichtungsdialog(ctx, vorbelegung=profil or default_profile())
        return

    navigation = st.navigation(_PAGES)
    navigation.run()


main()
