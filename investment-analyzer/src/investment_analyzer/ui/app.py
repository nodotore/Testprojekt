"""Streamlit-Einstiegspunkt: Seite 1 „Start/Datenstatus" + Ersteinrichtungsdialog,
bindet weitere Auftrag-§10-Seiten über die Sidebar-Navigation ein.

Bereits gebaut: Marktscreener (``ui/screener.py``, ADR-26),
Kandidaten-Rangliste (``ui/ranking.py``, ADR-28), Unternehmensdetail
mit Quellenleiste (``ui/detail.py``, ADR-27), Peer-Vergleich
(``ui/peers.py``, ADR-29), DCF- und Szenarioanalyse (``ui/dcf.py``,
ADR-30), Nachrichten/Ereignisse (``ui/news.py``, ADR-31). Drei weitere
Auftrag-§10-Seiten (Watchlist/Portfolio, Backtest, Einstellungen/
Quellen/Prüfprotokoll) fehlen noch — sie werden bewusst NICHT als
leere Platzhalter vorgebaut, um keine Funktionalität vorzutäuschen,
die noch nicht existiert (siehe ``TODO.md``).

Start: ``streamlit run src/investment_analyzer/ui/app.py`` (siehe
``start.ps1``/``start.bat`` im Projektstamm für den vollständigen
Windows-Startvorgang inkl. Migrationen).
"""

from __future__ import annotations

import pydantic
import streamlit as st

from investment_analyzer.config.defaults import default_profile
from investment_analyzer.config.models import (
    Anlagehorizont,
    Anlagestil,
    Ausgabeformat,
    NutzerProfil,
    Risikoklasse,
)
from investment_analyzer.ui.bootstrap import AppContext, bootstrap, check_database_ready
from investment_analyzer.ui.components import DISCLAIMER, render_disclaimer
from investment_analyzer.ui.dcf import render_dcfanalyse
from investment_analyzer.ui.detail import render_unternehmensdetail
from investment_analyzer.ui.news import render_nachrichten
from investment_analyzer.ui.peers import render_peervergleich
from investment_analyzer.ui.profile_form import build_profile_from_form
from investment_analyzer.ui.ranking import render_kandidatenrangliste
from investment_analyzer.ui.screener import render_marktscreener
from investment_analyzer.ui.status import lade_datenstatus

__all__ = ["DISCLAIMER", "render_disclaimer"]

REGION_OPTIONEN = ["USA", "Deutschland", "Übriges Europa", "Weitere/global"]
BOERSEN_OPTIONEN = ["NYSE", "NASDAQ", "XETRA", "Euronext", "Sonstige"]


@st.cache_resource
def get_context() -> AppContext:
    return bootstrap()


def render_ersteinrichtungsdialog(ctx: AppContext, vorbelegung: NutzerProfil) -> None:
    st.header("Ersteinrichtung")
    st.write(
        "Bevor der Investment-Analysator genutzt werden kann, wird einmalig ein "
        "Analyseprofil angelegt (Auftrag §2). Alle Angaben sind später über diese "
        "Seite jederzeit änderbar."
    )
    render_disclaimer()

    with st.form("ersteinrichtungsdialog"):
        profil_name = st.text_input("Profilname", value=vorbelegung.profil_name)

        st.subheader("Märkte")
        anlageregionen = st.multiselect(
            "Anlageregionen", REGION_OPTIONEN, default=vorbelegung.anlageregionen
        )
        boersen = st.multiselect("Börsen", BOERSEN_OPTIONEN, default=vorbelegung.boersen)

        st.subheader("Branchen")
        branchen = st.text_area("Branchen (leer = alle, kommagetrennt)", value="")
        ausschlussbranchen = st.text_area(
            "Ausschlussbranchen (kommagetrennt)",
            value=", ".join(vorbelegung.ausschlussbranchen),
        )
        ausschlusswerte = st.text_area(
            "Ausschlusswerte — Ticker/ISIN (kommagetrennt)",
            value=", ".join(vorbelegung.ausschlusswerte),
        )

        st.subheader("Anlagepräferenzen")
        col1, col2 = st.columns(2)
        with col1:
            anlagehorizont = st.selectbox(
                "Anlagehorizont",
                list(Anlagehorizont),
                index=list(Anlagehorizont).index(vorbelegung.anlagehorizont),
                format_func=lambda v: v.value,
            )
            risikoklasse = st.selectbox(
                "Risikoklasse",
                list(Risikoklasse),
                index=list(Risikoklasse).index(vorbelegung.risikoklasse),
                format_func=lambda v: v.value,
            )
        with col2:
            stil = st.multiselect(
                "Bevorzugter Stil", list(Anlagestil), default=vorbelegung.stil,
                format_func=lambda v: v.value,
            )
            waehrung = st.text_input("Referenzwährung", value=vorbelegung.waehrung)
        vergleichsindex = st.text_input("Vergleichsindex", value=vorbelegung.vergleichsindex)

        st.subheader("Marktkapitalisierung, Position, Kandidaten")
        col3, col4, col5 = st.columns(3)
        with col3:
            marktkap_min_mio = st.number_input(
                "Mindestmarktkap. (Mio.)",
                min_value=0.0,
                value=float(vorbelegung.marktkap_min_mio or 0.0),
                step=100.0,
            )
        with col4:
            marktkap_max_mio_raw = st.number_input(
                "Höchstmarktkap. (Mio., 0 = keine Grenze)",
                min_value=0.0,
                value=float(vorbelegung.marktkap_max_mio or 0.0),
                step=1000.0,
            )
        with col5:
            kandidatenzahl_ziel = st.number_input(
                "Gewünschte Kandidatenzahl",
                min_value=1,
                max_value=50,
                value=vorbelegung.kandidatenzahl_ziel,
            )
        positionsgroesse_max_prozent = st.slider(
            "Maximale Positionsgröße (% Portfolio, unverbindliche Bandbreite)",
            min_value=1.0,
            max_value=25.0,
            value=vorbelegung.positionsgroesse_max_prozent,
        )

        st.subheader("Standard-Ausschlüsse (Auftrag §2)")
        col6, col7, col8 = st.columns(3)
        with col6:
            microcaps_ausschliessen = st.checkbox(
                "Microcaps ausschließen", value=vorbelegung.microcaps_ausschliessen
            )
        with col7:
            pennystocks_ausschliessen = st.checkbox(
                "Pennystocks ausschließen", value=vorbelegung.pennystocks_ausschliessen
            )
        with col8:
            illiquide_ausschliessen = st.checkbox(
                "Illiquide Werte ausschließen", value=vorbelegung.illiquide_ausschliessen
            )

        st.subheader("Datenquellen")
        sec_edgar_kontakt_email = st.text_input(
            "Kontakt-E-Mail für SEC-EDGAR-Abrufe",
            value=vorbelegung.sec_edgar_kontakt_email or "",
            help=(
                "SEC-Pflichtangabe für jeden Datenabruf über den Marktscreener "
                "(Fair-Access-Policy der SEC, siehe DATA_SOURCES.md). Wird nur an "
                "SEC EDGAR übertragen, sonst nirgends."
            ),
        )

        st.subheader("Ausgabe")
        speicherort = st.text_input("Speicherort für Berichte/Exporte", value=str(vorbelegung.speicherort))
        ausgabeformate = st.multiselect(
            "Ausgabeformate", list(Ausgabeformat), default=vorbelegung.ausgabeformate,
            format_func=lambda v: v.value,
        )

        st.subheader("Rechtliches")
        haftungsausschluss_akzeptiert = st.checkbox(
            "Ich habe den Hinweis oben gelesen und verstanden: allgemeine Information, "
            "keine Anlageberatung, Verluste bis zum Totalverlust möglich."
        )

        abgeschickt = st.form_submit_button("Profil speichern und starten")

    if not abgeschickt:
        return

    if not haftungsausschluss_akzeptiert:
        st.error("Der Hinweis muss bestätigt werden, bevor das Profil gespeichert werden kann.")
        return

    form_daten = {
        "profil_name": profil_name,
        "anlageregionen": anlageregionen,
        "boersen": boersen,
        "branchen": branchen,
        "ausschlussbranchen": ausschlussbranchen,
        "ausschlusswerte": ausschlusswerte,
        "anlagehorizont": anlagehorizont,
        "risikoklasse": risikoklasse,
        "stil": stil,
        "waehrung": waehrung,
        "vergleichsindex": vergleichsindex,
        "marktkap_min_mio": marktkap_min_mio,
        "marktkap_max_mio": marktkap_max_mio_raw or None,
        "positionsgroesse_max_prozent": positionsgroesse_max_prozent,
        "kandidatenzahl_ziel": int(kandidatenzahl_ziel),
        "microcaps_ausschliessen": microcaps_ausschliessen,
        "pennystocks_ausschliessen": pennystocks_ausschliessen,
        "illiquide_ausschliessen": illiquide_ausschliessen,
        "speicherort": speicherort,
        "ausgabeformate": ausgabeformate,
        "konfigurierte_quellen": vorbelegung.konfigurierte_quellen,
        "sec_edgar_kontakt_email": sec_edgar_kontakt_email,
        "haftungsausschluss_akzeptiert": haftungsausschluss_akzeptiert,
    }

    try:
        profil = build_profile_from_form(form_daten)
    except pydantic.ValidationError as exc:
        st.error(f"Profil ungültig: {exc}")
        return

    ctx.profile_store.save(profil)
    ctx.audit_logger.log_config_changed(actor="ui.ersteinrichtung", detail="Nutzerprofil angelegt")
    st.success("Profil gespeichert.")
    st.rerun()


def render_datenstatus(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Start / Datenstatus")
    render_disclaimer()

    status = lade_datenstatus(ctx.session_factory)
    st.caption(
        f"Analysezeit: {status.letzte_aktivitaet_utc or 'noch keine Aktivität'} (UTC) · "
        f"Umgebung: {ctx.settings.environment} · "
        "Marktdatenverzögerung: nicht verfügbar — noch keine Marktdatenquelle angebunden "
        "(folgt in Milestone 2)."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Unternehmen in der Datenbank", status.anzahl_unternehmen)
    col2.metric("Konfigurierte Datenquellen", status.anzahl_quellen)
    col3.metric("Gespeicherte Datenpunkte", status.anzahl_datenpunkte)

    if status.anzahl_datenpunkte == 0:
        st.info(
            'Noch keine Analysedaten vorhanden. Über die Seite "Marktscreener" (Sidebar) '
            "lässt sich ein Unternehmen hinzufügen und echte Daten abrufen. Diese Seite hier "
            "zeigt bewusst keine Beispiel- oder Platzhalterzahlen, die wie echte Marktdaten "
            "aussehen könnten (Auftrag §16)."
        )

    with st.expander("Aktuelles Analyseprofil", expanded=False):
        st.json(profil.model_dump(mode="json"))

    with st.expander("Profil bearbeiten"):
        render_ersteinrichtungsdialog(ctx, vorbelegung=profil)


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

    # Einfache Sidebar-Navigation statt st.navigation()/st.Page(): mit nur
    # zwei Seiten bleibt eine feste Auswahl klarer und lässt sich unverändert
    # mit AppTest.from_file testen (siehe tests/ui/test_app_smoke.py).
    # Sobald weitere der neun Auftrag-§10-Seiten dazukommen, ist der Wechsel
    # auf st.navigation() vorgesehen (siehe NEXT_STEPS.md).
    seite = st.sidebar.radio(
        "Seite",
        [
            "Start / Datenstatus",
            "Marktscreener",
            "Kandidaten-Rangliste",
            "Unternehmensdetail",
            "Peer-Vergleich",
            "DCF- und Szenarioanalyse",
            "Nachrichten/Ereignisse",
        ],
    )
    if seite == "Marktscreener":
        render_marktscreener(ctx, profil)
    elif seite == "Kandidaten-Rangliste":
        render_kandidatenrangliste(ctx, profil)
    elif seite == "Unternehmensdetail":
        render_unternehmensdetail(ctx, profil)
    elif seite == "Peer-Vergleich":
        render_peervergleich(ctx, profil)
    elif seite == "DCF- und Szenarioanalyse":
        render_dcfanalyse(ctx, profil)
    elif seite == "Nachrichten/Ereignisse":
        render_nachrichten(ctx, profil)
    else:
        render_datenstatus(ctx, profil)


main()
