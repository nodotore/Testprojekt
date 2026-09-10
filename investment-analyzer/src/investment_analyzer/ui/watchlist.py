"""Watchlist/Portfolio (Auftrag §10, Seite 8).

Zwei Bereiche als Tabs: **Watchlist** (beobachtete, nicht gehaltene
Unternehmen) und **Portfolio** (tatsächlich gehaltene Positionen mit
Konzentrations-, Korrelations-, Drawdown- und Positionsgrößen-Analyse).
Beide unterstützen CSV-Import (``portfolio/csv_import.py``, Auftrag §8)
zusätzlich zur Anzeige des aktuellen Bestands.

Rendert die Portfolio-Analyse ausschließlich aus
``portfolio/report.py::build_portfolio_report`` — derselben
Orchestrierung, die auch für einen künftigen Portfolio-Export
verwendet würde (ADR-21-Prinzip: eine Berechnung, eine Datenquelle).
Erzeugt selbst keine neuen Werte (Auftrag §11) und niemals eine
konkrete Kauf-/Verkaufsmenge — nur die bereits im Backend als
unverbindliche Bandbreite gekennzeichneten Positionsgrößen (Auftrag §1).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.portfolio.concentration import ConcentrationBreakdown
from investment_analyzer.portfolio.csv_import import (
    CsvImportResult,
    import_portfolio_csv,
    import_watchlist_csv,
)
from investment_analyzer.portfolio.models import WatchlistEntry
from investment_analyzer.portfolio.report import PortfolioReport, build_portfolio_report
from investment_analyzer.portfolio.risk_metrics import DrawdownResult
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer


def _zahl(value: float | None, *, nachkomma: int = 2) -> str:
    return "—" if value is None else f"{value:,.{nachkomma}f}"


def _list_watchlist(session: Session) -> list[dict[str, object]]:
    rows = session.scalars(select(WatchlistEntry).order_by(WatchlistEntry.added_at.desc())).all()
    ergebnis = []
    for row in rows:
        entity = session.get(Entity, row.entity_id)
        ergebnis.append(
            {
                "Unternehmen": entity.name if entity is not None else row.entity_id,
                "Notiz": row.note or "",
                "Hinzugefügt am": row.added_at,
            }
        )
    return ergebnis


def _render_import_ergebnis(result: CsvImportResult) -> None:
    if result.errors:
        st.warning(f"{len(result.errors)} Zeile(n) mit Fehlern übersprungen (Zeile/Fehlergrund):")
        st.dataframe(
            pd.DataFrame([{"Zeile": e.row_number, "Fehler": e.message} for e in result.errors]),
            use_container_width=True,
            hide_index=True,
        )
    st.success(f"{result.created} neu angelegt, {result.updated} aktualisiert.")


def _render_watchlist_tab(ctx: AppContext) -> None:
    st.subheader("Watchlist per CSV importieren")
    st.caption("Erwartete Spalten: id_type,id_value,name,note — id_type ist isin/lei/cik.")
    upload = st.file_uploader("Watchlist-CSV", type="csv", key="watchlist_csv_upload")
    if upload is not None:
        text = upload.getvalue().decode("utf-8")
        with ctx.session_factory() as session:
            result = import_watchlist_csv(session, text)
            session.commit()
        ctx.audit_logger.log_config_changed(
            actor="ui.watchlist",
            detail=f"Watchlist-CSV importiert: {result.created} neu, {result.updated} aktualisiert, "
            f"{len(result.errors)} Fehler",
        )
        _render_import_ergebnis(result)

    st.subheader("Aktuelle Watchlist")
    with ctx.session_factory() as session:
        eintraege = _list_watchlist(session)

    if not eintraege:
        st.info("Noch keine Watchlist-Einträge.")
        return

    st.dataframe(pd.DataFrame(eintraege), use_container_width=True, hide_index=True)


def _konzentration_dataframe(breakdown: ConcentrationBreakdown) -> pd.DataFrame:
    """Prozentanteile (0..1) aus ``ConcentrationBreakdown.by_key`` als bereits
    auf 0..100 skalierte, absteigend sortierte Tabelle — als eigene reine
    Funktion testbar, damit eine fehlende ×100-Skalierung vor der Anzeige
    (echter Fehler beim ersten Live-Test dieser Seite) künftig ein Test statt
    erst ein Screenshot fängt."""

    sortiert = sorted(breakdown.by_key.items(), key=lambda kv: kv[1], reverse=True)
    return pd.DataFrame([(gruppe, anteil * 100) for gruppe, anteil in sortiert], columns=["Gruppe", "Anteil (%)"])


def _render_konzentration(titel: str, breakdown: ConcentrationBreakdown) -> None:
    st.markdown(f"**{titel}**")
    if not breakdown.computable:
        st.caption(breakdown.note or "Nicht berechenbar.")
        return
    if not breakdown.by_key:
        st.caption("Keine klassifizierten Positionen.")
        return
    st.dataframe(
        _konzentration_dataframe(breakdown), use_container_width=True, hide_index=True,
        column_config={"Anteil (%)": st.column_config.NumberColumn(format="%.1f%%")},
    )
    if breakdown.unclassified_value:
        st.caption(f"Nicht klassifizierbarer Wert: {_zahl(breakdown.unclassified_value)}.")


def _render_portfolio_tabelle(report: PortfolioReport) -> None:
    zeilen = [
        {
            "Unternehmen": p.entity_name,
            "Menge": p.quantity,
            "Währung": p.currency,
            "Letzter Kurs": p.latest_price,
            "Marktwert": p.market_value,
        }
        for p in report.positions
    ]
    st.dataframe(
        pd.DataFrame(zeilen),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Letzter Kurs": st.column_config.NumberColumn(format="%.2f"),
            "Marktwert": st.column_config.NumberColumn(format="%.2f"),
        },
    )


def _render_positionsgroessen(report: PortfolioReport) -> None:
    if not report.position_size_bands:
        return
    st.markdown("**Positionsgrößen-Bandbreite** (unverbindlich, kein Kaufsignal — Auftrag §1)")
    name_by_id = {p.entity_id: p.entity_name for p in report.positions}
    zeilen = [
        {
            "Unternehmen": name_by_id.get(entity_id, entity_id),
            "Max. Positionswert (Limit)": band.max_position_value,
            "Zusätzlich möglich (min.)": band.min_additional_value,
            "Zusätzlich möglich (max.)": band.max_additional_value,
        }
        for entity_id, band in report.position_size_bands.items()
    ]
    st.dataframe(
        pd.DataFrame(zeilen),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Max. Positionswert (Limit)": st.column_config.NumberColumn(format="%.2f"),
            "Zusätzlich möglich (min.)": st.column_config.NumberColumn(format="%.2f"),
            "Zusätzlich möglich (max.)": st.column_config.NumberColumn(format="%.2f"),
        },
    )


def _drawdown_dataframe(
    berechenbare_drawdowns: dict[str, DrawdownResult], name_by_id: dict[str, str]
) -> pd.DataFrame:
    """``max_drawdown_pct`` ist trotz des Namens eine Bruchzahl (0..-1), keine
    bereits auf 0..100 skalierte Prozentangabe — als eigene reine Funktion
    testbar, siehe ``_konzentration_dataframe()``."""

    return pd.DataFrame(
        [
            {
                "Unternehmen": name_by_id.get(eid, eid),
                "Max. Drawdown (%)": None if d.max_drawdown_pct is None else d.max_drawdown_pct * 100,
                "Höchststand": d.peak_date,
                "Tiefststand": d.trough_date,
            }
            for eid, d in berechenbare_drawdowns.items()
        ]
    )


def _render_drawdowns_und_korrelation(report: PortfolioReport) -> None:
    name_by_id = {p.entity_id: p.entity_name for p in report.positions}

    berechenbare_drawdowns = {eid: d for eid, d in report.drawdowns.items() if d.computable}
    if berechenbare_drawdowns:
        st.markdown("**Maximaler Drawdown je Position**")
        st.dataframe(
            _drawdown_dataframe(berechenbare_drawdowns, name_by_id),
            use_container_width=True,
            hide_index=True,
            column_config={"Max. Drawdown (%)": st.column_config.NumberColumn(format="%.1f%%")},
        )

    berechenbare_korrelationen = {
        paar: r for paar, r in report.correlations.items() if r.computable
    }
    if berechenbare_korrelationen:
        st.markdown("**Korrelation zwischen Positionen**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Unternehmen A": name_by_id.get(a, a),
                        "Unternehmen B": name_by_id.get(b, b),
                        "Korrelation": r.correlation,
                        "Überlappende Datenpunkte": r.overlapping_points,
                    }
                    for (a, b), r in berechenbare_korrelationen.items()
                ]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={"Korrelation": st.column_config.NumberColumn(format="%.2f")},
        )


def _render_portfolio_tab(ctx: AppContext, profil: NutzerProfil) -> None:
    st.subheader("Portfolio per CSV importieren")
    st.caption(
        "Erwartete Spalten: id_type,id_value,name,quantity,average_cost,currency,note "
        "— id_type ist isin/lei/cik."
    )
    upload = st.file_uploader("Portfolio-CSV", type="csv", key="portfolio_csv_upload")
    if upload is not None:
        text = upload.getvalue().decode("utf-8")
        with ctx.session_factory() as session:
            result = import_portfolio_csv(session, text)
            session.commit()
        ctx.audit_logger.log_config_changed(
            actor="ui.portfolio",
            detail=f"Portfolio-CSV importiert: {result.created} neu, {result.updated} aktualisiert, "
            f"{len(result.errors)} Fehler",
        )
        _render_import_ergebnis(result)

    st.subheader("Portfolio-Übersicht")
    with ctx.session_factory() as session:
        report = build_portfolio_report(session, profil)

    if not report.positions:
        st.info("Noch keine Portfolio-Positionen.")
        return

    ctx.audit_logger.log_report_generated(
        actor="ui.portfolio", detail=f"Portfolio-Übersicht mit {len(report.positions)} Position(en) angezeigt"
    )

    st.metric("Gesamtwert (bekannter Anteil)", _zahl(report.total_market_value))
    _render_portfolio_tabelle(report)

    col1, col2 = st.columns(2)
    with col1:
        _render_konzentration("Branchenkonzentration", report.sector_concentration)
    with col2:
        _render_konzentration("Länderkonzentration", report.country_concentration)

    if report.currency_exposure.value_by_currency:
        st.markdown("**Währungsexposure** (Rohwerte je Bestandswährung, keine Umrechnung — siehe DECISIONS.md ADR-20)")
        st.dataframe(
            pd.DataFrame(
                list(report.currency_exposure.value_by_currency.items()), columns=["Währung", "Wert"]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={"Wert": st.column_config.NumberColumn(format="%.2f")},
        )

    _render_positionsgroessen(report)
    _render_drawdowns_und_korrelation(report)

    if report.gaps:
        with st.expander(f"Nicht berechenbare Kennzahlen ({len(report.gaps)}) — nicht geraten, ehrlich als fehlend markiert"):
            for gap in report.gaps:
                st.write(f"- {gap}")


def render_watchlist_portfolio(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Watchlist/Portfolio")
    render_disclaimer()

    tab_watchlist, tab_portfolio = st.tabs(["Watchlist", "Portfolio"])
    with tab_watchlist:
        _render_watchlist_tab(ctx)
    with tab_portfolio:
        _render_portfolio_tab(ctx, profil)
