"""Streamlit-Einstiegspunkt: Router für ``st.navigation()``.

Prüft Datenbank-Migration und Nutzerprofil (Auftrag §2) und wählt je nach
Zustand eine von drei Seitenlisten für ``st.navigation()`` — Ersteinrichtung
(``ui/pages/ersteinrichtung.py``), eine Fehlerseite (DB nicht migriert) oder
alle zehn Auftrag-§10-Seiten unter ``ui/pages/``. ``st.navigation()`` wird
dabei in JEDEM Zweig aufgerufen, nie nur bedingt: Streamlit aktiviert seine
alte, ordnerbasierte „automatische pages/-Erkennung" (jede Datei unter
``ui/pages/`` als eigene, roh benannte Seite) erst dann dauerhaft ab, wenn
irgendeine Session in diesem Serverprozess ``st.navigation()`` tatsächlich
ausgeführt hat. Rief ein früherer Entwurf ``st.navigation()`` nur NACH
bestandener Profilprüfung auf, blieb die alte Ordner-Erkennung für jede
Session ohne Profil aktiv — sichtbar als rohe Dateinamen in der Seitenleiste
UND anklickbar, obwohl die einzelnen Seiten-Dateien ein bereits akzeptiertes
Profil voraussetzen (``require_profile()`` wirft dort einen
``AssertionError``). Live beim allerersten Start ohne vorhandenes Profil
gefunden und hier behoben (siehe ADR-36).

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

from investment_analyzer.ui.bootstrap import check_database_ready
from investment_analyzer.ui.context import get_context

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

_ERSTEINRICHTUNG_PAGES = [
    st.Page("pages/ersteinrichtung.py", title="Ersteinrichtung", default=True),
]


def _render_db_fehler() -> None:
    st.error(
        "Die Datenbank ist noch nicht migriert. Bitte `start.ps1`/`start.bat` "
        "ausführen (führt `alembic upgrade head` vor dem Start der Oberfläche aus)."
    )


_DB_FEHLER_PAGES = [st.Page(_render_db_fehler, title="Fehler", default=True)]


def main() -> None:
    st.set_page_config(page_title="Investment-Analysator", page_icon="📊", layout="wide")
    st.title("Investment-Analysator")

    ctx = get_context()

    if not check_database_ready(ctx.engine):
        st.navigation(_DB_FEHLER_PAGES).run()
        return

    profil = ctx.profile_store.load_or_none()
    if profil is None or not profil.haftungsausschluss_akzeptiert:
        st.navigation(_ERSTEINRICHTUNG_PAGES).run()
        return

    st.navigation(_PAGES).run()


main()
