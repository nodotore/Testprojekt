"""Nachrichten/Ereignisse (Auftrag §10, Seite 7).

Zeigt für ein ausgewähltes Unternehmen die bereits in der Datenbank
gespeicherten Nachrichtenmeldungen, gruppiert in Ereignis-Cluster
(``news/clustering.py``, Milestone 5) — inklusive der Auftrag-§3-
relevanten Information, ob ein Cluster von mehreren unabhängigen
Domains bestätigt wird oder nur aus einer einzelnen Quelle stammt.

Rendert wie ``ui/detail.py``/``ui/ranking.py``/``ui/peers.py``/
``ui/dcf.py`` (ADR-27/28/29/30) ausschließlich aus dem bereits
vorhandenen ``ReportBundle`` (``bundle.news`` = derselbe
``NewsReport``, den auch die Exporte verwenden) — keine eigene
Berechnung.

**Wichtige, ehrliche Einschränkung:** Diese Seite zeigt nur bereits
gespeicherte Meldungen. Ein automatischer Abruf über die GDELT-/
IR-RSS-Connectoren ist bislang in KEINER Oberflächenseite eingebunden
(anders als SEC EDGAR/Alpha Vantage über den Marktscreener, ADR-26) —
siehe ``NEXT_STEPS.md``. Ohne einen solchen Abrufweg bleibt diese Seite
in der Praxis leer, was hier bewusst offen kommuniziert wird statt
verschwiegen zu werden (Auftrag §16).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.news.clustering import NewsCluster
from investment_analyzer.reports import build_report_bundle
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer
from investment_analyzer.ui.screener import list_entities


def _cluster_tabelle(cluster: NewsCluster) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Titel": item.title,
                "Domain": item.domain or "—",
                "Quellqualität": item.source_category,
                "Veröffentlicht": item.published_at,
                "Quelle": item.url,
            }
            for item in cluster.items
        ]
    )


def _render_cluster(cluster: NewsCluster) -> None:
    bestaetigung = (
        f"mehrquellenbestätigt ({len(cluster.domains)} unabhängige Domains)"
        if cluster.is_multi_source
        else "nur eine Quelle — noch nicht unabhängig bestätigt"
    )
    titel = f"{cluster.event_type} — {cluster.item_count} Meldung(en), {bestaetigung}"
    with st.expander(titel):
        st.caption(
            f"Früheste Meldung: {cluster.earliest_published_at or 'unbekannt'} · "
            f"Jüngste Meldung: {cluster.latest_published_at or 'unbekannt'}"
        )
        st.dataframe(
            _cluster_tabelle(cluster),
            use_container_width=True,
            hide_index=True,
            column_config={"Quelle": st.column_config.LinkColumn("Quelle")},
        )


def render_nachrichten(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Nachrichten/Ereignisse")
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

    with st.spinner("Nachrichten werden geladen..."), ctx.session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None  # kam gerade erst aus list_entities()
        bundle = build_report_bundle(session, entity)

    ctx.audit_logger.log_report_generated(
        actor="ui.nachrichten", detail=f"Nachrichten/Ereignisse für {entity.name} angezeigt"
    )

    news = bundle.news
    st.caption(f"Datenstand (as_of): {bundle.header.as_of} · Analysezeit: {bundle.header.generated_at_utc}")

    if news.total_items == 0:
        st.info(
            "Noch keine Nachrichtenmeldungen für dieses Unternehmen gespeichert. Ein "
            "automatischer Abruf über GDELT/IR-RSS ist in der Oberfläche noch nicht "
            "eingebunden (siehe NEXT_STEPS.md) — anders als beim SEC-EDGAR-/Alpha-Vantage-"
            "Abruf über den Marktscreener."
        )
        return

    st.write(
        f"{news.total_items} Meldung(en) in {len(news.clusters)} Ereignis-Cluster(n) "
        f"({news.items_without_published_date} ohne bekanntes Veröffentlichungsdatum)."
    )

    for cluster in news.clusters:
        _render_cluster(cluster)
