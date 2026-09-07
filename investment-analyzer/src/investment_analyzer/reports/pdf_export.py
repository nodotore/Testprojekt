"""PDF-Export eines ``ReportBundle`` (Auftrag §2: Ausgabeformat PDF).

Lineare Darstellung derselben sieben Abschnitte wie der Excel-Export
(``excel_export.py``) — beide lesen aus ``report_bundle_to_dict()``
(``json_export.py``), damit kein Exportformat abweichende Werte zeigen
kann (siehe ``DECISIONS.md`` ADR-21).

**Sicherheitshinweis (Auftrag §12):** ``reportlab``s ``Paragraph``
interpretiert ein minimales HTML-ähnliches Markup im übergebenen Text.
Nachrichtentitel/-URLs (``news``-Modul) stammen aus externen, nicht
vertrauenswürdigen Quellen und werden deshalb bewusst NICHT über
``Paragraph`` gerendert — nur über einfache ``Table``-Zellen (kein
Markup-Parsing) oder gar nicht (aktuell: nur aggregierte Zahlen im
PDF, keine Einzeltitel). Nur intern deterministisch generierter Text
(Score-Begründungen, Annahmen-Hinweise) läuft durch ``Paragraph``.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from investment_analyzer.reports.bundle import ReportBundle
from investment_analyzer.reports.json_export import report_bundle_to_dict

_STYLES = getSampleStyleSheet()


def _heading(text: str) -> Paragraph:
    return Paragraph(text, _STYLES["Heading2"])


def _para(text: str) -> Paragraph:
    return Paragraph(text, _STYLES["BodyText"])


def _cell(value: Any) -> str:
    return "" if value is None else str(value)


def _key_value_table(rows: list[tuple[str, Any]]) -> Table:
    data = [[label, _cell(value)] for label, value in rows]
    table = Table(data, colWidths=[220, 260])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    return table


def _list_table(headers: list[str], rows: list[list[Any]]) -> Table:
    data = [headers] + [[_cell(v) for v in row] for row in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    return table


def _bullets(items: list[str]) -> list[Paragraph]:
    return [_para(f"- {item}") for item in items] if items else [_para("keine")]


def build_pdf_bytes(bundle: ReportBundle) -> bytes:
    """Baut das PDF vollständig im Speicher (keine temporäre Datei nötig)."""

    data = report_bundle_to_dict(bundle)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story: list[Any] = []

    header = data["header"]
    score = data["score"]
    story.append(_heading("Zusammenfassung"))
    story.append(
        _key_value_table(
            [
                ("Unternehmen", header["entity_name"]),
                ("Datenstand (as_of)", header["as_of"]),
                ("Analysezeit", header["generated_at_utc"]),
                ("Datenabdeckung", header["data_completeness"]),
                ("Score-Konfidenz (coverage)", header["score_coverage"]),
                ("Klassifikation", header["score_classification"]),
                ("Marktdatenverzögerung", header["market_data_delay_note"]),
                ("Gesamtscore (0-100)", score["total_score"]),
            ]
        )
    )
    story.append(Spacer(1, 12))
    story.append(_para("<b>Positive Faktoren:</b>"))
    story.extend(_bullets(score["top_positive_factors"]))
    story.append(_para("<b>Risiken:</b>"))
    story.extend(_bullets(score["top_risks"]))
    story.append(_para("<b>Gegenargumente:</b>"))
    story.extend(_bullets(score["counterarguments"]))
    story.append(Spacer(1, 20))

    f = data["fundamentals"]
    story.append(_heading("Kennzahlen"))
    story.append(
        _key_value_table(
            [
                ("Umsatzwachstum 3J", f["revenue_growth"]["horizon_3y"]),
                ("Bruttomarge", f["margins"]["gross_margin"]),
                ("Operative Marge", f["margins"]["operating_margin"]),
                ("Nettomarge", f["margins"]["net_margin"]),
                ("Eigenkapitalrendite (ROE)", f["returns"]["return_on_equity"]),
                ("ROIC", f["returns"]["return_on_invested_capital"]),
                ("Nettoverbindlichkeiten/EBITDA", f["leverage"]["net_debt_to_ebitda"]),
                ("Zinsdeckung", f["leverage"]["interest_coverage"]),
                ("Datenabdeckung", f["data_completeness"]),
            ]
        )
    )
    story.append(Spacer(1, 20))

    v = data["valuation"]
    story.append(_heading("Bewertung"))
    story.append(
        _key_value_table(
            [
                ("Kurs je Aktie", v["multiples"]["price_per_share"]),
                ("KGV (P/E)", v["multiples"]["price_earnings_ratio"]),
                ("EV/EBITDA", v["multiples"]["ev_to_ebitda"]),
                ("Fairer Wert unteres Band", v["fair_value_lower_band"]),
                ("Fairer Wert oberes Band", v["fair_value_upper_band"]),
                ("Sicherheitsmarge", v["safety_margin"]),
            ]
        )
    )
    if v["dcf_scenarios"]:
        story.append(Spacer(1, 8))
        story.append(
            _list_table(
                ["Szenario", "Fairer Wert/Aktie", "WACC", "Terminalwachstum"],
                [
                    [
                        name,
                        result["fair_value_per_share"],
                        result["assumptions"]["wacc"],
                        result["assumptions"]["terminal_growth_rate"],
                    ]
                    for name, result in v["dcf_scenarios"].items()
                ],
            )
        )
    story.append(Spacer(1, 20))

    story.append(_heading("Risiken"))
    if f["warning_signals"]:
        story.append(
            _list_table(
                ["Code", "Schweregrad", "Beschreibung"],
                [[w["code"], w["severity"], w["description"]] for w in f["warning_signals"]],
            )
        )
    else:
        story.append(_para("Keine zahlenbasierten Warnsignale ausgelöst."))
    story.append(Spacer(1, 20))

    n = data["news"]
    story.append(_heading("Nachrichten"))
    story.append(
        _para(
            f"{n['total_items']} Meldung(en) in {len(n['clusters'])} Ereignis-Cluster(n) "
            f"({n['items_without_published_date']} ohne bekanntes Datum)."
        )
    )
    story.append(Spacer(1, 20))

    story.append(_heading("Quellen"))
    story.append(
        _list_table(
            ["Key", "Anzeigename"],
            [[s["key"], s["display_name"]] for s in data["sources"]],
        )
    )
    story.append(Spacer(1, 20))

    story.append(_heading("Annahmen"))
    story.extend(_bullets(list(data["assumptions"])))

    doc.build(story)
    return buffer.getvalue()


def export_pdf(bundle: ReportBundle, path: str | Path) -> None:
    Path(path).write_bytes(build_pdf_bytes(bundle))
