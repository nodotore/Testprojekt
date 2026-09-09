"""Kandidaten-Rangliste (Auftrag §10, Seite 3).

Sortierbare Tabelle aller bereits erfassten Unternehmen nach
``ScoreResult.total_score`` (``scoring/score.py``). Rendert — wie die
Unternehmensdetail-Seite (``ui/detail.py``, ADR-27) — ausschließlich
aus ``reports/bundle.py::build_report_bundle`` je Unternehmen, damit
Score, Datenabdeckung und Konfidenz auf dieser Seite garantiert
dieselben Werte zeigen wie auf der Detailseite und in den Exporten
(ADR-21).

Rankt bewusst NUR die bereits über den Marktscreener erfassten
Unternehmen, nicht eine größere Grundgesamtheit — eine automatische
Breitensuche über einen größeren Aktienuniversum existiert in diesem
Programm noch nicht (siehe ADR-28).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.reports import build_report_bundle
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer
from investment_analyzer.ui.screener import list_entities


def _rangliste_dataframe(ctx: AppContext, entities: list[Entity]) -> pd.DataFrame:
    zeilen = []
    with ctx.session_factory() as session:
        for kurzinfo in entities:
            entity = session.get(Entity, kurzinfo.id)
            assert entity is not None  # kam gerade erst aus list_entities()
            bundle = build_report_bundle(session, entity)
            zeilen.append(
                {
                    "Unternehmen": bundle.header.entity_name,
                    "Score (0–100)": bundle.score.total_score,
                    "Klassifikation": bundle.header.score_classification,
                    "Datenabdeckung (%)": round(bundle.header.data_completeness * 100, 1),
                    "Konfidenz (%)": round(bundle.header.score_coverage * 100, 1),
                }
            )

    df = pd.DataFrame(zeilen)
    return df.sort_values("Score (0–100)", ascending=False, na_position="last").reset_index(drop=True)


def render_kandidatenrangliste(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Kandidaten-Rangliste")
    render_disclaimer()

    entities = list_entities(ctx.session_factory)
    if not entities:
        st.info(
            'Noch keine Unternehmen erfasst. Über die Seite "Marktscreener" (Sidebar) '
            "zuerst mindestens ein Unternehmen hinzufügen."
        )
        return

    st.caption(
        f"{len(entities)} erfasste Unternehmen. Rangfolge nach Gesamtscore — Spalten sind "
        "per Klick auf die Kopfzeile sortierbar."
    )

    with st.spinner("Scores werden berechnet..."):
        df = _rangliste_dataframe(ctx, entities)

    ctx.audit_logger.log_report_generated(
        actor="ui.kandidatenrangliste", detail=f"Rangliste für {len(entities)} Unternehmen angezeigt"
    )

    unzureichend = int((df["Klassifikation"] == "Datenlage unzureichend").sum())
    if unzureichend:
        st.warning(
            f"{unzureichend} von {len(entities)} Unternehmen mit Klassifikation "
            "'Datenlage unzureichend': der Score dieser Unternehmen beruht auf zu wenigen "
            "tatsächlich vorhandenen Rohdaten, um belastbar zu sein (siehe "
            "Klassifikation-Spalte, Auftrag §11)."
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score (0–100)": st.column_config.NumberColumn(format="%.1f"),
            "Datenabdeckung (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Konfidenz (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
