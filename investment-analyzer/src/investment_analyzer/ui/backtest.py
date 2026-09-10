"""Backtest (Auftrag §10, Seite 9).

Führt die deterministische Top-N-Score-Strategie
(``backtesting/strategy.py``) über eine vom Nutzer gewählte Folge von
Rebalancing-Stichtagen aus (``backtesting/report.py::
build_backtest_report``, Milestone 7) und zeigt Gesamtrendite, CAGR,
Volatilität, Sharpe/Sortino, maximalen Drawdown, Turnover und die
NAV-Zeitreihe (Auftrag §9).

Erzeugt selbst KEIN neues Berechnungsergebnis — reine Darstellung der
vom Backend gelieferten Werte, inklusive der dort bereits dokumentierten
Lücken (``NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES``, u. a. kein
Benchmark-Vergleich mangels angebundener Indexkursquelle).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from investment_analyzer.backtesting.report import BacktestReport, build_backtest_report
from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.portfolio.assumptions import PortfolioAssumptions
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer

#: Anzeigename -> (Schrittweite, Perioden pro Jahr für die Annualisierung).
_INTERVALLE: dict[str, tuple[relativedelta, int]] = {
    "Monatlich": (relativedelta(months=1), 12),
    "Quartalsweise": (relativedelta(months=3), 4),
    "Jährlich": (relativedelta(years=1), 1),
}

_GAP_LABELS: dict[str, str] = {
    "benchmark_kursreihe": (
        "Vergleich gegen einen Index/eine Benchmark (Auftrag §9) — keine "
        "Benchmark-Kursquelle angebunden."
    ),
    "waehrungsumrechnung": "Währungsumrechnung bei gemischten Bestandswährungen — nicht implementiert.",
    "vollstaendiges_survivorship_universum": (
        "Vollständiges, survivorship-bereinigtes Aktienuniversum — umfasst nur bereits "
        "über den Marktscreener erfasste Unternehmen, nicht den gesamten historischen Markt."
    ),
}


def _zahl(value: float | None, *, nachkomma: int = 2) -> str:
    return "—" if value is None else f"{value:,.{nachkomma}f}"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:+.1%}"


def _rebalance_dates(start: date, end: date, schritt: relativedelta) -> list[datetime]:
    """Baut aufsteigend sortierte UTC-Rebalancing-Stichtage von ``start`` bis
    ``end`` (inklusive) im gewählten Intervall — als eigene reine Funktion
    testbar, unabhängig von der Streamlit-Formulareingabe."""

    termine: list[datetime] = []
    aktuell = start
    while aktuell <= end:
        termine.append(datetime.combine(aktuell, time.min, tzinfo=UTC))
        aktuell = aktuell + schritt
    return termine


def _entity_namen(session: Session, report: BacktestReport) -> dict[str, str]:
    ids = {eid for p in report.run.periods for eid in (*p.holdings, *p.excluded_holdings)}
    namen: dict[str, str] = {}
    for entity_id in ids:
        entity = session.get(Entity, entity_id)
        if entity is not None:
            namen[entity_id] = entity.name
    return namen


def _render_kennzahlen(report: BacktestReport) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtrendite", _pct(report.total_return))
    col2.metric("CAGR", _pct(report.cagr))
    col3.metric("Zeitraum (Jahre)", _zahl(report.years, nachkomma=1))

    col4, col5, col6 = st.columns(3)
    col4.metric("Annualisierte Volatilität", _pct(report.annualized_volatility))
    col5.metric("Sharpe Ratio", _zahl(report.sharpe_ratio))
    col6.metric("Sortino Ratio", _zahl(report.sortino_ratio))

    col7, col8, col9 = st.columns(3)
    col7.metric("Maximaler Drawdown", _pct(report.max_drawdown.max_drawdown_pct))
    col8.metric("Durchschnittlicher Turnover", _pct(report.average_turnover))
    col9.metric("Vergleich vs. Benchmark", _pct(report.benchmark_total_return))


def _render_nav_verlauf(report: BacktestReport) -> None:
    st.subheader("NAV-Verlauf")
    df = pd.DataFrame(
        {"NAV": [nav for _, nav in report.run.nav_series]},
        index=[moment for moment, _ in report.run.nav_series],
    )
    st.line_chart(df)
    st.caption("NAV startet bei 1.0 — reine Simulation, kein tatsächlich investierter Betrag (Auftrag §1).")


def _render_perioden_tabelle(report: BacktestReport, namen: dict[str, str]) -> None:
    st.subheader("Rebalancing-Perioden")

    def _liste(entity_ids: tuple[str, ...]) -> str:
        return ", ".join(namen.get(eid, eid) for eid in entity_ids) if entity_ids else "—"

    zeilen = [
        {
            "Start": p.start,
            "Ende": p.end,
            "Positionen": _liste(p.holdings),
            "Portfolio-Rendite (%)": None if p.portfolio_return is None else p.portfolio_return * 100,
            "Ausgeschlossen (fehlender Kurs)": _liste(p.excluded_holdings),
        }
        for p in report.run.periods
    ]
    st.dataframe(
        pd.DataFrame(zeilen),
        use_container_width=True,
        hide_index=True,
        column_config={"Portfolio-Rendite (%)": st.column_config.NumberColumn(format="%.1f%%")},
    )


def _render_gaps(report: BacktestReport) -> None:
    if not report.gaps:
        return
    with st.expander(f"Nicht berechenbare/umgesetzte Punkte ({len(report.gaps)}) — nicht geraten, ehrlich als fehlend markiert"):
        for gap in report.gaps:
            st.write(f"- {_GAP_LABELS.get(gap, gap)}")


def render_backtest(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Backtest")
    render_disclaimer()

    with st.form("backtest_form"):
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Startdatum", value=date.today().replace(year=date.today().year - 3))
        with col2:
            end = st.date_input("Enddatum", value=date.today())

        col3, col4 = st.columns(2)
        with col3:
            intervall_name = st.selectbox("Rebalancing-Intervall", list(_INTERVALLE))
        with col4:
            top_n = st.number_input("Top-N (Anzahl Positionen je Rebalancing)", min_value=1, max_value=50, value=5)

        abgeschickt = st.form_submit_button("Backtest ausführen")

    if not abgeschickt:
        st.info(
            'Zeitraum, Rebalancing-Intervall und Top-N wählen und auf "Backtest ausführen" '
            "klicken. Die Strategie wählt zu jedem Stichtag die Top-N-Unternehmen nach "
            "Gesamtscore aus bereits erfassten Unternehmen aus (deterministisch, kein "
            "auf den Zeitraum gefitteter Parameter — Auftrag §9)."
        )
        return

    if end <= start:
        st.error("Das Enddatum muss nach dem Startdatum liegen.")
        return

    schritt, periods_per_year = _INTERVALLE[intervall_name]
    rebalance_dates = _rebalance_dates(start, end, schritt)
    if len(rebalance_dates) < 2:
        st.error(
            "Zeitraum und Intervall ergeben weniger als zwei Rebalancing-Stichtage — "
            "bitte einen längeren Zeitraum oder ein feineres Intervall wählen."
        )
        return

    with st.spinner("Backtest wird berechnet..."), ctx.session_factory() as session:
        report = build_backtest_report(
            session, rebalance_dates, top_n=int(top_n),
            assumptions=PortfolioAssumptions(), periods_per_year=periods_per_year,
        )
        namen = _entity_namen(session, report)

    ctx.audit_logger.log_report_generated(
        actor="ui.backtest",
        detail=f"Backtest {start}–{end}, {intervall_name}, Top-{top_n}, "
        f"{len(report.run.periods)} Perioden ausgeführt",
    )

    _render_kennzahlen(report)
    _render_nav_verlauf(report)
    _render_perioden_tabelle(report, namen)
    _render_gaps(report)
