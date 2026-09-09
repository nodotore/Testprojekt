"""Unternehmensdetail mit Quellenleiste (Auftrag §10, Seite 4).

Rendert AUSSCHLIESSLICH aus einem bereits gebauten ``ReportBundle``
(``reports/bundle.py::build_report_bundle``) — genau wie der Excel-/
PDF-/JSON-Export (``reports/excel_export.py`` usw.) liest diese Seite
über ``report_bundle_to_dict()`` denselben Dict wie die Exportformate.
Das ist keine Zufallsübereinstimmung, sondern die in ADR-21
dokumentierte strukturelle Garantie: Export und Oberfläche können
dadurch nie unterschiedliche Werte zeigen (Auftrag-§15-Kriterium 8).

Erzeugt selbst KEINE neuen Werte (Auftrag §11) — reine Darstellung.
"""

from __future__ import annotations

import io

import streamlit as st

from investment_analyzer.config.models import NutzerProfil
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.reports import (
    ReportBundle,
    build_excel_workbook,
    build_pdf_bytes,
    build_report_bundle,
    report_bundle_to_dict,
    report_bundle_to_json,
)
from investment_analyzer.ui.bootstrap import AppContext
from investment_analyzer.ui.components import render_disclaimer
from investment_analyzer.ui.screener import list_entities


def _kennzahl(value: object, *, prozent: bool = False, nachkomma: int = 2) -> str:
    """Formatiert einen Kennzahlenwert für die Anzeige — ``None`` immer als
    „—", niemals als 0 oder eine sonstige geratene Zahl (Auftrag §11)."""

    if value is None:
        return "—"
    if isinstance(value, bool):  # bool ist eine int-Unterklasse -- vor int-Zweig behandeln
        return "Ja" if value else "Nein"
    if isinstance(value, int | float):
        if prozent:
            return f"{value:+.1%}" if abs(value) < 10 else f"{value:+.0%}"
        return f"{value:,.{nachkomma}f}"
    return str(value)


def _render_kopfzeile(header: dict) -> None:
    """Auftrag §10: „Jeder Bericht zeigt oben: Datenstand, Analysezeit,
    Marktdatenverzögerung, Datenabdeckung und Konfidenz."""

    st.caption(
        f"Datenstand (as_of): {header['as_of']} · Analysezeit: {header['generated_at_utc']} · "
        f"Datenabdeckung: {_kennzahl(header['data_completeness'], prozent=True)} · "
        f"Konfidenz (coverage): {_kennzahl(header['score_coverage'], prozent=True)} · "
        f"Klassifikation: {header['score_classification']}"
    )
    st.caption(header["market_data_delay_note"])
    st.info(header["disclaimer"])


def _render_kennzahlen(f: dict) -> None:
    st.subheader("Kennzahlen")
    horizonte = ["horizon_1y", "horizon_3y", "horizon_5y", "horizon_10y"]
    labels = ["1 Jahr", "3 Jahre", "5 Jahre", "10 Jahre"]
    wachstum_zeilen = [
        ("Umsatzwachstum", f["revenue_growth"]),
        ("Nettogewinnwachstum", f["net_income_growth"]),
        ("EPS-Wachstum", f["eps_diluted_growth"]),
        ("FCF-Wachstum", f["free_cash_flow_growth"]),
    ]
    st.table(
        {
            label: {name: _kennzahl(werte[h], prozent=True) for name, werte in wachstum_zeilen}
            for label, h in zip(labels, horizonte, strict=True)
        }
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Margen**")
        st.write(f"Bruttomarge: {_kennzahl(f['margins']['gross_margin'], prozent=True)}")
        st.write(f"Operative Marge: {_kennzahl(f['margins']['operating_margin'], prozent=True)}")
        st.write(f"Nettomarge: {_kennzahl(f['margins']['net_margin'], prozent=True)}")
    with col2:
        st.markdown("**Renditen**")
        st.write(f"ROE: {_kennzahl(f['returns']['return_on_equity'], prozent=True)}")
        st.write(f"ROIC: {_kennzahl(f['returns']['return_on_invested_capital'], prozent=True)}")
        st.caption(f"ROIC-Steuersatz-Annahme: {_kennzahl(f['returns']['roic_tax_rate_assumption'], prozent=True)}")
    with col3:
        st.markdown("**Verschuldung**")
        st.write(f"Nettoverbindlichkeiten/EBITDA: {_kennzahl(f['leverage']['net_debt_to_ebitda'])}")
        st.write(f"Zinsdeckung: {_kennzahl(f['leverage']['interest_coverage'])}")

    if f["missing_fields"]:
        with st.expander(f"Fehlende Kennzahlen ({len(f['missing_fields'])}) — nicht geraten, ehrlich als fehlend markiert"):
            st.write(", ".join(f["missing_fields"]))


def _render_bewertung(v: dict) -> None:
    st.subheader("Bewertung")
    m = v["multiples"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Kurs je Aktie", _kennzahl(m["price_per_share"]))
    col2.metric("KGV (P/E)", _kennzahl(m["price_earnings_ratio"]))
    col3.metric("EV/EBITDA", _kennzahl(m["ev_to_ebitda"]))

    col4, col5, col6 = st.columns(3)
    col4.metric("Fairer Wert unteres Band", _kennzahl(v["fair_value_lower_band"]))
    col5.metric("Fairer Wert oberes Band", _kennzahl(v["fair_value_upper_band"]))
    col6.metric("Sicherheitsmarge", _kennzahl(v["safety_margin"], prozent=True))

    if v["dcf_scenarios"]:
        st.markdown("**DCF-Szenarien**")
        st.table(
            {
                name: {
                    "Fairer Wert/Aktie": _kennzahl(result["fair_value_per_share"]),
                    "WACC": _kennzahl(result["assumptions"]["wacc"], prozent=True),
                    "Terminalwachstum": _kennzahl(result["assumptions"]["terminal_growth_rate"], prozent=True),
                }
                for name, result in v["dcf_scenarios"].items()
            }
        )

    if v["peer_multiples"]:
        st.markdown("**Peer-Vergleich**")
        st.table(
            [
                {"Peer": p["entity_name"], "KGV": _kennzahl(p["price_earnings_ratio"]), "EV/EBITDA": _kennzahl(p["ev_to_ebitda"])}
                for p in v["peer_multiples"]
            ]
        )

    if v["missing_data_notes"]:
        with st.expander("Offene Punkte zur Bewertung"):
            for note in v["missing_data_notes"]:
                st.write(f"- {note}")


def _render_score(score: dict, f: dict) -> None:
    st.subheader("Score")
    col1, col2 = st.columns(2)
    col1.metric("Gesamtscore (0–100)", _kennzahl(score["total_score"], nachkomma=1))
    col2.metric("Klassifikation", score["classification"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Positive Faktoren**")
        for item in score["top_positive_factors"] or ["keine"]:
            st.write(f"- {item}")
        st.markdown("**Risiken**")
        for item in score["top_risks"] or ["keine"]:
            st.write(f"- {item}")
    with col_b:
        st.markdown("**Gegenargumente**")
        for item in score["counterarguments"] or ["keine"]:
            st.write(f"- {item}")
        st.markdown("**Bedingungen für Ungültigkeit der These**")
        for item in score["invalidation_conditions"] or ["keine"]:
            st.write(f"- {item}")

    if score["risk_deductions"]:
        st.markdown("**Risikoabzüge**")
        st.table(
            [
                {"Code": d["code"], "Schweregrad": d["severity"], "Punkte": d["points"], "Beschreibung": d["description"]}
                for d in score["risk_deductions"]
            ]
        )

    if f["not_yet_implementable_signals"]:
        st.caption(
            "Nicht implementierbare Warnsignale (dokumentierte Lücke, keine "
            f"vorgetäuschte Vollständigkeit): {', '.join(f['not_yet_implementable_signals'])}"
        )


def _render_nachrichten(n: dict) -> None:
    st.subheader("Nachrichten")
    st.write(
        f"{n['total_items']} Meldung(en) in {len(n['clusters'])} Ereignis-Cluster(n) "
        f"({n['items_without_published_date']} ohne bekanntes Datum)."
    )
    for cluster in n["clusters"]:
        with st.expander(f"{cluster['event_type']} ({len(cluster['items'])} Meldung(en))"):
            st.table(
                [
                    {
                        "Titel": item["title"],
                        "Domain": item["domain"],
                        "Quellqualität": item["source_category"],
                        "Veröffentlicht": item["published_at"],
                    }
                    for item in cluster["items"]
                ]
            )


def _render_quellenleiste(sources: list[dict]) -> None:
    """Auftrag §10: „Unternehmensdetail MIT Quellenleiste"."""

    st.subheader("Quellen")
    st.table([{"Quelle": s["display_name"], "Lizenzhinweis": s["license_note"]} for s in sources])


def _render_annahmen(assumptions: list[str]) -> None:
    st.subheader("Annahmen")
    for note in assumptions:
        st.write(f"- {note}")


def _render_exportbuttons(bundle: ReportBundle) -> None:
    st.subheader("Export")
    entity_slug = bundle.header.entity_id
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "JSON herunterladen",
        data=report_bundle_to_json(bundle).encode("utf-8"),
        file_name=f"bericht-{entity_slug}.json",
        mime="application/json",
    )

    excel_buffer = io.BytesIO()
    build_excel_workbook(bundle).save(excel_buffer)
    col2.download_button(
        "Excel herunterladen",
        data=excel_buffer.getvalue(),
        file_name=f"bericht-{entity_slug}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    col3.download_button(
        "PDF herunterladen",
        data=build_pdf_bytes(bundle),
        file_name=f"bericht-{entity_slug}.pdf",
        mime="application/pdf",
    )


def render_unternehmensdetail(ctx: AppContext, profil: NutzerProfil) -> None:
    st.header("Unternehmensdetail")
    render_disclaimer()

    entities = list_entities(ctx.session_factory)
    if not entities:
        st.info(
            'Noch keine Unternehmen erfasst. Über die Seite "Marktscreener" (Sidebar) '
            "zuerst ein Unternehmen hinzufügen."
        )
        return

    namen_zu_id = {f"{e.name} ({e.id[:8]})": e.id for e in entities}
    auswahl = st.selectbox("Unternehmen", list(namen_zu_id))
    entity_id = namen_zu_id[auswahl]
    entity_name = next(e.name for e in entities if e.id == entity_id)

    with st.spinner("Bericht wird berechnet..."), ctx.session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None  # kam gerade erst aus list_entities()
        bundle = build_report_bundle(session, entity)
        data = report_bundle_to_dict(bundle)

    ctx.audit_logger.log_report_generated(
        actor="ui.unternehmensdetail", detail=f"Bericht für {entity_name} angezeigt"
    )

    _render_kopfzeile(data["header"])

    if data["header"]["score_classification"] == "Datenlage unzureichend":
        st.warning(
            "Datenlage unzureichend für eine belastbare Bewertung — es werden nur die "
            "tatsächlich vorhandenen Rohdaten gezeigt, keine geratenen Kennzahlen."
        )

    _render_kennzahlen(data["fundamentals"])
    _render_bewertung(data["valuation"])
    _render_score(data["score"], data["fundamentals"])
    _render_nachrichten(data["news"])
    _render_quellenleiste(data["sources"])
    _render_annahmen(data["assumptions"])
    _render_exportbuttons(bundle)
