"""Streamlit-Einstiegspunkt: Seite 1 „Start/Datenstatus" + Ersteinrichtungsdialog.

Weitere neun Seiten aus Auftrag §10 (Marktscreener, Kandidaten-Rangliste,
Unternehmensdetail, Peer-Vergleich, DCF/Szenarioanalyse, Nachrichten/
Ereignisse, Watchlist/Portfolio, Backtest, Einstellungen/Quellen/
Prüfprotokoll) folgen in den jeweils zuständigen späteren Milestones
(siehe ``PLAN.md``) — sie werden hier bewusst NICHT als leere
Platzhalter vorgebaut, um keine Funktionalität vorzutäuschen, die noch
nicht existiert.

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
from investment_analyzer.ui.profile_form import build_profile_from_form
from investment_analyzer.ui.status import lade_datenstatus

DISCLAIMER = (
    "⚠️ **Nur allgemeine Information — keine Anlageberatung.** Dieses Programm "
    "liefert Research-Ergebnisse im Simulationsmodus, keine individuelle Anlage-, "
    "Steuer- oder Rechtsberatung und keine Kauf-/Verkaufsempfehlung. Es werden keine "
    "Wertpapiere automatisch gehandelt. Investitionen in Wertpapiere können bis zum "
    "Totalverlust des eingesetzten Kapitals führen."
)

REGION_OPTIONEN = ["USA", "Deutschland", "Übriges Europa", "Weitere/global"]
BOERSEN_OPTIONEN = ["NYSE", "NASDAQ", "XETRA", "Euronext", "Sonstige"]


@st.cache_resource
def get_context() -> AppContext:
    return bootstrap()


def render_disclaimer() -> None:
    st.warning(DISCLAIMER)


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
            "Noch keine Analysedaten vorhanden: Milestone 2 (Datenbeschaffung) wurde noch "
            "nicht ausgeführt. Diese Seite zeigt bewusst keine Beispiel- oder Platzhalterzahlen, "
            "die wie echte Marktdaten aussehen könnten (Auftrag §16)."
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
    else:
        render_datenstatus(ctx, profil)


main()
