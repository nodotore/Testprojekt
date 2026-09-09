"""DCF- und Szenarioanalyse (Auftrag §10, Seite 6).

Zeigt für ein ausgewähltes Unternehmen den vollständigen DCF-Teil des
``ReportBundle`` (``ui/detail.py`` zeigt davon nur eine verdichtete
Zusammenfassungstabelle): die drei Szenarien Basis/Optimistisch/
Pessimistisch mit Annahmen und Jahr-für-Jahr-Cashflow-Projektion sowie
die beiden Sensitivitätsmatrizen (Wachstum×WACC, Marge×Terminal-
wachstum, Auftrag §6). Erzeugt selbst KEIN neues DCF-Ergebnis — alle
Zahlen kommen unverändert aus ``reports/bundle.py::build_report_bundle``
→ ``ValuationReport`` (Milestone 4), genau wie bei ``ui/detail.py``
(ADR-27), ``ui/ranking.py`` (ADR-28) und ``ui/peers.py`` (ADR-29).
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
from investment_analyzer.valuation.dcf import DCFResult, SensitivityMatrix

_SENSITIVITY_LABELS: dict[str, str] = {
    "revenue_growth_rate": "Umsatzwachstum",
    "fcf_margin": "FCF-Marge",
    "wacc": "WACC",
    "terminal_growth_rate": "Terminalwachstum",
}


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:+.1%}"


def _zahl(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f}"


def _render_annahmen(result: DCFResult) -> None:
    a = result.assumptions
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Umsatzwachstum p. a.", _pct(a.revenue_growth_rate))
    col2.metric("FCF-Marge", _pct(a.fcf_margin))
    col3.metric("WACC", _pct(a.wacc))
    col4.metric("Terminalwachstum", _pct(a.terminal_growth_rate))
    st.caption(f"Projektionshorizont: {a.projection_years} Jahre.")


def _render_cashflow_tabelle(result: DCFResult) -> None:
    jahre = list(range(1, len(result.projected_fcf) + 1))
    df = pd.DataFrame(
        {
            "Jahr": jahre,
            "Projizierter FCF": result.projected_fcf,
            "Diskontierter FCF": result.discounted_fcf,
        }
    )
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Projizierter FCF": st.column_config.NumberColumn(format="%.2f"),
            "Diskontierter FCF": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Terminalwert (diskontiert)", _zahl(result.terminal_value_discounted))
    col2.metric("Unternehmenswert (EV)", _zahl(result.enterprise_value))
    col3.metric("Eigenkapitalwert", _zahl(result.equity_value))
    col4.metric("Fairer Wert/Aktie", _zahl(result.fair_value_per_share))


def _render_szenario(name: str, result: DCFResult) -> None:
    titel = f"Szenario '{name}' — Fairer Wert/Aktie: {_zahl(result.fair_value_per_share)}"
    with st.expander(titel, expanded=(name == "Basis")):
        _render_annahmen(result)
        _render_cashflow_tabelle(result)


def _sensitivitaetstabelle(matrix: SensitivityMatrix) -> pd.DataFrame:
    zeilen_label = _SENSITIVITY_LABELS.get(matrix.row_parameter, matrix.row_parameter)
    spalten_labels = [
        f"{_SENSITIVITY_LABELS.get(matrix.column_parameter, matrix.column_parameter)} {v:+.1%}"
        for v in matrix.column_values
    ]
    df = pd.DataFrame(matrix.fair_value_per_share, columns=spalten_labels)
    df.insert(0, zeilen_label, [f"{v:+.1%}" for v in matrix.row_values])
    return df


def _render_sensitivitaet(titel: str, matrix: SensitivityMatrix | None) -> None:
    st.markdown(f"**{titel}**")
    if matrix is None:
        st.caption("Nicht berechenbar — siehe Hinweise oben.")
        return
    df = _sensitivitaetstabelle(matrix)
    spaltenformat = {
        spalte: st.column_config.NumberColumn(format="%.2f")
        for spalte in df.columns
        if spalte != df.columns[0]
    }
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=spaltenformat)
    st.caption(
        "Zellenwert: fairer Wert je Aktie in diesem Szenario. '—' bedeutet: rechnerisch "
        "unzulässige Annahmenkombination (WACC <= Terminalwachstum oder WACC <= 0)."
    )


def render_dcfanalyse(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("DCF- und Szenarioanalyse")
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

    with st.spinner("DCF-Modell wird berechnet..."), ctx.session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None  # kam gerade erst aus list_entities()
        bundle = build_report_bundle(session, entity)

    ctx.audit_logger.log_report_generated(
        actor="ui.dcfanalyse", detail=f"DCF-/Szenarioanalyse für {entity.name} angezeigt"
    )

    v = bundle.valuation
    st.caption(f"Datenstand (as_of): {bundle.header.as_of} · Analysezeit: {bundle.header.generated_at_utc}")

    if v.missing_data_notes:
        for note in v.missing_data_notes:
            st.warning(note)

    if not v.dcf_scenarios:
        st.info(
            "Für dieses Unternehmen ist aktuell kein DCF-Szenario berechenbar — siehe "
            "Hinweise oben. Es werden bewusst keine geratenen Annahmen ergänzt (Auftrag §11)."
        )
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Fairer Wert unteres Band", _zahl(v.fair_value_lower_band))
    col2.metric("Fairer Wert oberes Band", _zahl(v.fair_value_upper_band))
    col3.metric("Sicherheitsmarge", _pct(v.safety_margin))

    st.subheader("Szenarien")
    for name in ("Basis", "Optimistisch", "Pessimistisch"):
        result = v.dcf_scenarios.get(name)
        if result is not None:
            _render_szenario(name, result)

    st.subheader("Sensitivitätsanalyse")
    _render_sensitivitaet("Umsatzwachstum × WACC", v.sensitivity_growth_wacc)
    _render_sensitivitaet("FCF-Marge × Terminalwachstum", v.sensitivity_margin_terminal_growth)
