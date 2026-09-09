"""Peer-Vergleich (Auftrag §10, Seite 5).

Vergleicht ein ausgewähltes Unternehmen mit seinen laut
``fundamentals/peers.py::find_peers`` gefundenen Branchen-Peers
(identischer SIC-Code, siehe dortiger Docstring: reine Branchen-, noch
keine größenbereinigte Peer-Gruppe) in einer Tabelle nebeneinander.

Wie ``ui/detail.py``/``ui/ranking.py`` (ADR-27/ADR-28) baut diese Seite
für das ausgewählte Unternehmen UND jeden Peer den vollständigen
``ReportBundle`` und liest die Vergleichswerte ausschließlich daraus —
keine eigene Berechnung, keine Abweichung von den auf der
Unternehmensdetail-Seite gezeigten Werten für dasselbe Unternehmen.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.peers import find_peers
from investment_analyzer.reports import ReportBundle, build_report_bundle
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer
from investment_analyzer.ui.screener import list_entities


def _vergleichszeile(bundle: ReportBundle, *, ist_ausgewaehltes_unternehmen: bool) -> dict[str, object]:
    f = bundle.fundamentals
    v = bundle.valuation
    return {
        "Unternehmen": bundle.header.entity_name + (" (ausgewählt)" if ist_ausgewaehltes_unternehmen else ""),
        "Score (0–100)": bundle.score.total_score,
        "Klassifikation": bundle.header.score_classification,
        "Umsatzwachstum 1J (%)": _als_prozent(f.revenue_growth.horizon_1y),
        "Nettomarge (%)": _als_prozent(f.margins.net_margin),
        "ROE (%)": _als_prozent(f.returns.return_on_equity),
        "Nettoverbindlichkeiten/EBITDA": f.leverage.net_debt_to_ebitda,
        "KGV (P/E)": v.multiples.price_earnings_ratio,
        "EV/EBITDA": v.multiples.ev_to_ebitda,
    }


def _als_prozent(value: float | None) -> float | None:
    return None if value is None else round(value * 100, 1)


def _vergleichstabelle(session: Session, entity: Entity, peers: list[Entity]) -> pd.DataFrame:
    zeilen = [_vergleichszeile(build_report_bundle(session, entity), ist_ausgewaehltes_unternehmen=True)]
    zeilen.extend(
        _vergleichszeile(build_report_bundle(session, peer), ist_ausgewaehltes_unternehmen=False) for peer in peers
    )
    return pd.DataFrame(zeilen)


def render_peervergleich(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Peer-Vergleich")
    render_disclaimer()

    entities = list_entities(ctx.session_factory)
    if not entities:
        st.info(
            'Noch keine Unternehmen erfasst. Über die Seite "Marktscreener" (Sidebar) '
            "zuerst mindestens ein Unternehmen hinzufügen."
        )
        return

    namen_zu_id = {f"{e.name} ({e.id[:8]})": e.id for e in entities}
    auswahl = st.selectbox("Unternehmen", list(namen_zu_id))
    entity_id = namen_zu_id[auswahl]

    with st.spinner("Peer-Vergleich wird berechnet..."), ctx.session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None  # kam gerade erst aus list_entities()

        if not entity.sic_code:
            st.warning(
                f"Für '{entity.name}' ist noch kein SIC-Branchencode bekannt — Peers werden "
                "ausschließlich über einen identischen SIC-Code ermittelt (siehe "
                "DATA_SOURCES.md), es gibt bewusst keine Ersatz-Peer-Gruppe ohne "
                "Branchenklassifikation (Auftrag §11). Der SIC-Code wird beim Abruf über den "
                "Marktscreener automatisch aus SEC EDGAR übernommen."
            )
            return

        peers = find_peers(session, entity)
        if not peers:
            st.info(
                f"Keine anderen bereits erfassten Unternehmen mit demselben SIC-Code "
                f"({entity.sic_code}) gefunden. Peers werden nur unter den über den "
                "Marktscreener bereits hinzugefügten Unternehmen gesucht, nicht in einem "
                "größeren Aktienuniversum (siehe NEXT_STEPS.md)."
            )
            return

        df = _vergleichstabelle(session, entity, peers)

    st.caption(f"SIC-Code {entity.sic_code} · {len(peers)} Peer(s) gefunden.")

    ctx.audit_logger.log_report_generated(
        actor="ui.peervergleich", detail=f"Peer-Vergleich für {entity.name} mit {len(peers)} Peers angezeigt"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score (0–100)": st.column_config.NumberColumn(format="%.1f"),
            "Umsatzwachstum 1J (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Nettomarge (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "ROE (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Nettoverbindlichkeiten/EBITDA": st.column_config.NumberColumn(format="%.2f"),
            "KGV (P/E)": st.column_config.NumberColumn(format="%.1f"),
            "EV/EBITDA": st.column_config.NumberColumn(format="%.1f"),
        },
    )
