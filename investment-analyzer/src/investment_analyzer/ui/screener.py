"""Marktscreener: Unternehmen per CIK/Ticker hinzufügen und Daten abrufen
(Auftrag §10, Seite 2).

Bindet ausschließlich bereits unabhängig getestete Bausteine ein
(``connectors/``, ``ingestion/pipeline.py``) — erzeugt selbst keine
neuen Werte. Netzwerkfehler jeder Art (Timeout, SSRF-Block, ungültiges
Antwortformat, SEC-/Alpha-Vantage-Fehlermeldung) werden NICHT
verschluckt: sie erscheinen als klarer Fehler auf der Seite und werden
im Audit-Log vermerkt (Auftrag §4 „Fail loud, nicht silent").

``list_entities`` ist bewusst als reine, Streamlit-freie Funktion
gehalten (testbar ohne Streamlit-Laufzeitkontext, siehe
``tests/ui/test_screener.py``), analog zu ``ui/status.py::
lade_datenstatus``.
"""

from __future__ import annotations

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.connectors.alpha_vantage import API_KEY_SECRET_NAME, AlphaVantageConnector
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorError
from investment_analyzer.connectors.sec_edgar import SecEdgarConnector
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.ingestion.pipeline import (
    add_and_ingest_alpha_vantage_price,
    add_and_ingest_sec_edgar,
    resolve_ticker_to_cik,
)
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer


def list_entities(session_factory: sessionmaker[Session], *, suchtext: str = "") -> list[Entity]:
    """Liefert bereits erfasste Unternehmen, optional nach Namen gefiltert (Auftrag §10: „Filter")."""

    with session_factory() as session:
        query = select(Entity).order_by(Entity.name)
        if suchtext.strip():
            query = query.where(Entity.name.ilike(f"%{suchtext.strip()}%"))
        entities = session.scalars(query).all()
        # Identifier innerhalb der Session laden, damit sie nach dem Schließen
        # noch zugreifbar sind (kein DetachedInstanceError beim Rendern).
        for entity in entities:
            _ = list(entity.identifiers)
        return list(entities)


def _sec_connector(ctx: AppContext, *, kontakt_email: str) -> SecEdgarConnector:
    return SecEdgarConnector(
        contact=kontakt_email,
        cache=FileCache(ctx.settings.cache_dir),
    )


def _alpha_vantage_connector(ctx: AppContext, *, api_key: str) -> AlphaVantageConnector:
    return AlphaVantageConnector(api_key=api_key, cache=FileCache(ctx.settings.cache_dir))


def _render_hinzufuegen_formular(ctx: AppContext, profil: NutzerProfil) -> None:
    st.subheader("Unternehmen hinzufügen")

    if not profil.sec_edgar_kontakt_email:
        st.error(
            "Für SEC-EDGAR-Abrufe ist eine Kontakt-E-Mail-Adresse Pflicht (SEC-Vorgabe). "
            'Bitte unter "Start / Datenstatus" -> "Profil bearbeiten" -> "Datenquellen" eintragen.'
        )
        return

    eingabeart = st.radio(
        "Kennung", ["CIK (SEC-eigene Kennung)", "US-Ticker"], horizontal=True
    )
    wert = st.text_input(
        "CIK" if eingabeart.startswith("CIK") else "Ticker",
        help=(
            "Die CIK ist SEC EDGARs eigene, stabile Unternehmenskennung "
            "(zu finden über die SEC-EDGAR-Firmensuche)."
            if eingabeart.startswith("CIK")
            else "US-Börsenkürzel, z. B. AAPL — wird intern über die SEC-Ticker-Liste zu einer CIK aufgelöst."
        ),
    )

    hat_av_schluessel = ctx.secret_store is not None and bool(
        ctx.secret_store.get_secret(API_KEY_SECRET_NAME)
    )
    av_symbol = ""
    if hat_av_schluessel:
        av_symbol = st.text_input(
            "Alpha-Vantage-Symbol für Kursabruf (optional, leer lassen zum Überspringen)",
            value=wert if eingabeart == "US-Ticker" else "",
        )
    else:
        st.caption(
            "Kein Alpha-Vantage-API-Schlüssel hinterlegt — es werden nur SEC-EDGAR-"
            "Fundamentaldaten abgerufen, kein Kurs. (Schlüsselverwaltung folgt in der "
            "künftigen Einstellungen-Seite, siehe TODO.md.)"
        )

    if not st.button("Hinzufügen und Daten abrufen"):
        return
    if not wert.strip():
        st.error("Bitte eine CIK oder einen Ticker eingeben.")
        return

    with st.spinner("Rufe Daten ab..."):
        try:
            sec_connector = _sec_connector(ctx, kontakt_email=profil.sec_edgar_kontakt_email)
            if eingabeart.startswith("CIK"):
                cik = wert.strip()
            else:
                cik = resolve_ticker_to_cik(sec_connector, wert.strip())

            with ctx.session_factory() as session:
                sec_result = add_and_ingest_sec_edgar(session, sec_connector, cik=cik)
                session.commit()
                entity_id = sec_result.entity.id
                entity_name = sec_result.entity.name

            ctx.audit_logger.log_data_fetch(
                actor="ui.marktscreener",
                source_key="sec_edgar",
                entity_id=entity_id,
                detail=f"{sec_result.neue_datenpunkte} neue Datenpunkte für CIK {cik}",
            )
            st.success(
                f'"{entity_name}" hinzugefügt/aktualisiert: {sec_result.neue_datenpunkte} neue '
                f"Datenpunkte über {len(sec_result.abgefragte_kennzahlen)} Kennzahlen."
            )
            if sec_result.nicht_gemeldete_kennzahlen:
                st.caption(
                    f"{len(sec_result.nicht_gemeldete_kennzahlen)} Kennzahlen wurden von diesem "
                    "Unternehmen nicht gemeldet (ehrlich als fehlend markiert, nicht geraten)."
                )
        except ConnectorError as exc:
            ctx.audit_logger.log_data_fetch_error(
                actor="ui.marktscreener", source_key="sec_edgar", detail=str(exc)
            )
            st.error(f"SEC-EDGAR-Abruf fehlgeschlagen: {exc}")
            return

        if hat_av_schluessel and av_symbol.strip():
            assert ctx.secret_store is not None
            api_key = ctx.secret_store.get_secret(API_KEY_SECRET_NAME)
            ctx.audit_logger.log_secret_accessed(
                actor="ui.marktscreener", secret_name=API_KEY_SECRET_NAME
            )
            try:
                av_connector = _alpha_vantage_connector(ctx, api_key=api_key)  # type: ignore[arg-type]
                with ctx.session_factory() as session:
                    entity = session.get(Entity, entity_id)
                    assert entity is not None
                    av_result = add_and_ingest_alpha_vantage_price(
                        session, av_connector, entity=entity, symbol=av_symbol.strip()
                    )
                    session.commit()
                ctx.audit_logger.log_data_fetch(
                    actor="ui.marktscreener", source_key="alpha_vantage", entity_id=entity_id,
                    detail=f"Kurs {av_result.data_point.value_normalized} zum {av_result.data_point.period_end}",
                )
                st.success(f"Kurs abgerufen: {av_result.data_point.value_normalized}.")
            except ConnectorError as exc:
                ctx.audit_logger.log_data_fetch_error(
                    actor="ui.marktscreener", source_key="alpha_vantage", detail=str(exc)
                )
                st.error(f"Alpha-Vantage-Abruf fehlgeschlagen: {exc}")


def render_marktscreener(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Marktscreener")
    render_disclaimer()
    st.write(
        "Unternehmen hinzufügen und über SEC EDGAR (Fundamentaldaten, nur US-Emittenten) "
        "sowie optional Alpha Vantage (Kurs) abrufen. SEC EDGAR benötigt keinen API-"
        "Schlüssel, nur eine Kontaktadresse (siehe unten)."
    )

    _render_hinzufuegen_formular(ctx, profil)

    st.subheader("Bereits erfasste Unternehmen")
    suchtext = st.text_input("Suche nach Name (Filter)", value="")
    entities = list_entities(ctx.session_factory, suchtext=suchtext)
    if not entities:
        st.info("Noch keine Unternehmen in der Datenbank.")
        return

    st.table(
        [
            {
                "Name": e.name,
                "Land": e.country or "—",
                "Börse": e.primary_exchange or "—",
                "SIC": e.sic_code or "—",
                "Kennungen": ", ".join(f"{i.id_type}:{i.id_value}" for i in e.identifiers),
            }
            for e in entities
        ]
    )
