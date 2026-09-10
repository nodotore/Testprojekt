"""Einstellungen, Quellen und Prüfprotokoll (Auftrag §10, Seite 10).

Drei Bereiche als Tabs:

- **Schlüsselverwaltung:** setzt/löscht den Alpha-Vantage-API-Schlüssel
  über ``AppContext.secret_store`` (nie den Wert selbst anzeigen oder
  loggen, Auftrag §12) — und richtet, falls kein OS-Keyring verfügbar
  ist, den verschlüsselten Datei-Fallback per Master-Passwort ein
  (``config/secrets.py::EncryptedFileSecretStore``, ADR-5). Damit wird
  der Alpha-Vantage-Kursabruf im Marktscreener erstmals nutzbar, ohne
  den Schlüssel vorher manuell im OS-Keyring hinterlegt zu haben.
- **Quellen:** reine Anzeige aller registrierten ``Source``-Zeilen
  (Auftrag §3: Quellen-/Lizenzübersicht).
- **Prüfprotokoll:** reine Anzeige der zuletzt geschriebenen
  ``AuditLogEntry``-Zeilen (Auftrag §12: vollständiges Audit-Log).

Erzeugt selbst keine neuen Werte — die Schlüsselverwaltung ruft
ausschließlich bereits vorhandene ``SecretStore``-Methoden auf.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select

from investment_analyzer.audit.models import AuditLogEntry
from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.config.secrets import SecretStoreUnavailableError, get_secret_store
from investment_analyzer.connectors.alpha_vantage import API_KEY_SECRET_NAME
from investment_analyzer.connectors.models import Source
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer

_ALLE_EREIGNISTYPEN = "Alle"


def _render_secret_store_einrichten(ctx: AppContext) -> None:
    st.warning(
        "Kein OS-Keyring verfügbar. Ohne einen Secret-Store kann kein "
        "Alpha-Vantage-API-Schlüssel gespeichert werden. Alternativ lässt sich "
        "ein verschlüsselter Datei-Fallback mit einem selbst gewählten "
        "Master-Passwort einrichten (ADR-5) — das Passwort wird nirgends im "
        "Klartext gespeichert und ist bei jedem Neustart erneut einzugeben."
    )
    with st.form("secret_store_setup_form"):
        master_password = st.text_input("Master-Passwort", type="password")
        bestaetigung = st.text_input("Master-Passwort bestätigen", type="password")
        abgeschickt = st.form_submit_button("Verschlüsselten Datei-Fallback einrichten")

    if not abgeschickt:
        return
    if not master_password:
        st.error("Master-Passwort darf nicht leer sein.")
        return
    if master_password != bestaetigung:
        st.error("Die beiden Eingaben stimmen nicht überein.")
        return

    try:
        store = get_secret_store(path=ctx.settings.secrets_path, master_password=master_password)
    except SecretStoreUnavailableError as exc:
        st.error(f"Einrichtung fehlgeschlagen: {exc}")
        return

    ctx.secret_store = store
    ctx.audit_logger.log_config_changed(
        actor="ui.einstellungen", detail="Verschlüsselter Datei-Fallback für Secrets eingerichtet"
    )
    st.success("Eingerichtet.")
    st.rerun()


def _render_alpha_vantage_schluessel(ctx: AppContext) -> None:
    assert ctx.secret_store is not None
    vorhanden = bool(ctx.secret_store.get_secret(API_KEY_SECRET_NAME))

    if vorhanden:
        st.success(
            "Ein Alpha-Vantage-API-Schlüssel ist hinterlegt — der Kursabruf im "
            "Marktscreener ist nutzbar."
        )
    else:
        st.info(
            "Kein Alpha-Vantage-API-Schlüssel hinterlegt — der optionale Kursabruf im "
            "Marktscreener bleibt so lange deaktiviert. Ein kostenloser Schlüssel lässt "
            "sich bei Alpha Vantage registrieren (siehe DATA_SOURCES.md)."
        )

    with st.form("alpha_vantage_key_form", clear_on_submit=True):
        neuer_schluessel = st.text_input("Alpha-Vantage-API-Schlüssel", type="password")
        col1, col2 = st.columns(2)
        speichern = col1.form_submit_button("Speichern")
        loeschen = col2.form_submit_button("Löschen", disabled=not vorhanden)

    if speichern:
        if not neuer_schluessel:
            st.error("Bitte einen Schlüssel eingeben.")
            return
        ctx.secret_store.set_secret(API_KEY_SECRET_NAME, neuer_schluessel)
        ctx.audit_logger.log_config_changed(
            actor="ui.einstellungen", detail="Alpha-Vantage-API-Schlüssel gesetzt"
        )
        st.success("Gespeichert.")
        st.rerun()

    if loeschen:
        ctx.secret_store.delete_secret(API_KEY_SECRET_NAME)
        ctx.audit_logger.log_config_changed(
            actor="ui.einstellungen", detail="Alpha-Vantage-API-Schlüssel gelöscht"
        )
        st.success("Gelöscht.")
        st.rerun()


def _render_schluesselverwaltung(ctx: AppContext) -> None:
    st.subheader("Schlüsselverwaltung")
    if ctx.secret_store is None:
        _render_secret_store_einrichten(ctx)
        return
    _render_alpha_vantage_schluessel(ctx)


def _render_quellen(ctx: AppContext) -> None:
    st.subheader("Quellen")
    with ctx.session_factory() as session:
        quellen = session.scalars(select(Source).order_by(Source.display_name)).all()
        zeilen = [
            {
                "Quelle": s.display_name,
                "Schlüssel": s.key,
                "Aktiv": s.is_active,
                "Lizenzhinweis": s.license_note,
                "Basis-URL": s.base_url,
            }
            for s in quellen
        ]

    if not zeilen:
        st.info("Noch keine Quellen registriert.")
        return
    st.dataframe(pd.DataFrame(zeilen), use_container_width=True, hide_index=True)


def _render_pruefprotokoll(ctx: AppContext) -> None:
    st.subheader("Prüfprotokoll")
    st.caption(
        "Die letzten 200 Einträge des Audit-Logs (Auftrag §12) — unveränderliches, "
        "fortlaufend geschriebenes Protokoll, keine nachträgliche Bearbeitung möglich."
    )

    with ctx.session_factory() as session:
        eintraege = session.scalars(
            select(AuditLogEntry).order_by(AuditLogEntry.timestamp_utc.desc()).limit(200)
        ).all()
        zeilen = [
            {
                "Zeitpunkt (UTC)": e.timestamp_utc,
                "Ereignistyp": e.event_type,
                "Akteur": e.actor,
                "Unternehmen": e.entity_id,
                "Quelle": e.source_key,
                "Detail": e.detail,
            }
            for e in eintraege
        ]

    if not zeilen:
        st.info("Noch keine Prüfprotokoll-Einträge.")
        return

    ereignistypen = [_ALLE_EREIGNISTYPEN] + sorted({e.event_type for e in eintraege})
    auswahl = st.selectbox("Nach Ereignistyp filtern", ereignistypen)
    if auswahl != _ALLE_EREIGNISTYPEN:
        zeilen = [z for z in zeilen if z["Ereignistyp"] == auswahl]

    st.dataframe(pd.DataFrame(zeilen), use_container_width=True, hide_index=True)


def render_einstellungen(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Einstellungen, Quellen und Prüfprotokoll")
    render_disclaimer()

    tab_schluessel, tab_quellen, tab_protokoll = st.tabs(["Schlüsselverwaltung", "Quellen", "Prüfprotokoll"])
    with tab_schluessel:
        _render_schluesselverwaltung(ctx)
    with tab_quellen:
        _render_quellen(ctx)
    with tab_protokoll:
        _render_pruefprotokoll(ctx)
