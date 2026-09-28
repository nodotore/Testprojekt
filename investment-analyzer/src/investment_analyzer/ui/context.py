"""Gemeinsamer, über ``st.cache_resource`` zwischengespeicherter Anwendungskontext.

Ausgelagert aus ``app.py`` (dem Router für ``st.navigation()``), damit jede
Seiten-Datei unter ``ui/pages/`` denselben ``AppContext`` erhält, ohne
``app.py`` zu importieren — ein solcher Import würde dessen Modul-Ebenen-
Aufruf von ``main()`` ein zweites Mal auslösen (siehe ADR-35).
"""

from __future__ import annotations

import streamlit as st

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.ui.bootstrap import AppContext, bootstrap


@st.cache_resource
def get_context() -> AppContext:
    return bootstrap()


def require_profile(ctx: AppContext) -> NutzerProfil:
    """Lädt das aktive Nutzerprofil für eine Seiten-Datei unter ``ui/pages/``.

    Der Router (``app.py``) lässt ``st.navigation()`` erst laufen, nachdem
    ein akzeptiertes Profil bestätigt wurde — an dieser Stelle ist ein
    fehlendes Profil daher ein Programmierfehler, kein Nutzerzustand, den es
    freundlich abzufangen gälte.
    """

    profil = ctx.profile_store.load_or_none()
    assert profil is not None and profil.haftungsausschluss_akzeptiert
    return profil
