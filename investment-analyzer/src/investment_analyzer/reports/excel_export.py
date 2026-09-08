"""Excel-Export eines ``ReportBundle`` (Auftrag §10: „Export nach Excel
enthält Tabellenblätter Zusammenfassung, Kennzahlen, Bewertung, Risiken,
Nachrichten, Quellen und Annahmen").

Baut auf demselben ``report_bundle_to_dict()`` wie der JSON-Export
(``json_export.py``) auf — ein Wert kann dadurch strukturell nicht
zwischen den beiden Exportformaten auseinanderlaufen (siehe
``DECISIONS.md`` ADR-21).

**Sicherheitshinweis (Auftrag §12):** Nachrichtentitel/-URLs/-Domains
stammen aus externen, nicht vertrauenswürdigen Quellen (``news``-Modul).
Ein Zellwert, der mit ``=``, ``+``, ``-`` oder ``@`` beginnt, könnte von
manchen Tabellenkalkulationen bzw. Re-Import-Pfaden als Formel
interpretiert werden („Formula Injection") — jeder Zellwert wird daher
über ``_sanitize_excel_string`` geführt, bevor er geschrieben wird.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from investment_analyzer.reports.bundle import ReportBundle
from investment_analyzer.reports.json_export import report_bundle_to_dict

_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@")


def _sanitize_excel_string(value: str) -> str:
    if value and value[0] in _FORMULA_TRIGGER_CHARS:
        return "'" + value
    return value


def _excel_safe(value: Any) -> Any:
    if isinstance(value, dict | list):
        return str(value)
    if isinstance(value, str):
        return _sanitize_excel_string(value)
    return value


def _write_key_value_rows(ws: Worksheet, rows: list[tuple[str, Any]], *, start_row: int = 1) -> int:
    row = start_row
    for label, value in rows:
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=_excel_safe(value))
        row += 1
    return row


def _write_table(
    ws: Worksheet, headers: list[str], rows: list[list[Any]], *, start_row: int = 1
) -> int:
    row = start_row
    for col, header in enumerate(headers, start=1):
        ws.cell(row=row, column=col, value=header)
    row += 1
    for data_row in rows:
        for col, value in enumerate(data_row, start=1):
            ws.cell(row=row, column=col, value=_excel_safe(value))
        row += 1
    return row


def _write_bullet_list(ws: Worksheet, title: str, items: list[str], *, start_row: int) -> int:
    row = start_row
    ws.cell(row=row, column=1, value=title)
    row += 1
    for item in items:
        ws.cell(row=row, column=1, value=f"- {item}")
        row += 1
    return row + 1


def _sheet_zusammenfassung(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.active
    assert ws is not None
    ws.title = "Zusammenfassung"
    header = data["header"]
    score = data["score"]

    row = _write_key_value_rows(
        ws,
        [
            ("Unternehmen", header["entity_name"]),
            ("Datenstand (as_of)", header["as_of"]),
            ("Analysezeit (generated_at_utc)", header["generated_at_utc"]),
            ("Datenabdeckung (data_completeness)", header["data_completeness"]),
            ("Score-Konfidenz (coverage)", header["score_coverage"]),
            ("Klassifikation", header["score_classification"]),
            ("Marktdatenverzögerung", header["market_data_delay_note"]),
            ("Gesamtscore (0-100)", score["total_score"]),
        ],
    ) + 1

    row = _write_bullet_list(ws, "Positive Faktoren", score["top_positive_factors"], start_row=row)
    row = _write_bullet_list(ws, "Risiken", score["top_risks"], start_row=row)
    row = _write_bullet_list(ws, "Gegenargumente", score["counterarguments"], start_row=row)
    row = _write_bullet_list(
        ws, "Bedingungen für Ungültigkeit der These", score["invalidation_conditions"], start_row=row
    )

    ws.cell(row=row, column=1, value="Hinweis")
    ws.cell(row=row, column=2, value=_excel_safe(header["disclaimer"]))


def _sheet_kennzahlen(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Kennzahlen")
    f = data["fundamentals"]

    row = _write_key_value_rows(
        ws,
        [
            ("Umsatzwachstum 1J", f["revenue_growth"]["horizon_1y"]),
            ("Umsatzwachstum 3J", f["revenue_growth"]["horizon_3y"]),
            ("Umsatzwachstum 5J", f["revenue_growth"]["horizon_5y"]),
            ("Umsatzwachstum 10J", f["revenue_growth"]["horizon_10y"]),
            ("Nettogewinnwachstum 1J", f["net_income_growth"]["horizon_1y"]),
            ("Nettogewinnwachstum 3J", f["net_income_growth"]["horizon_3y"]),
            ("Nettogewinnwachstum 5J", f["net_income_growth"]["horizon_5y"]),
            ("Nettogewinnwachstum 10J", f["net_income_growth"]["horizon_10y"]),
            ("EPS-Wachstum 1J", f["eps_diluted_growth"]["horizon_1y"]),
            ("EPS-Wachstum 3J", f["eps_diluted_growth"]["horizon_3y"]),
            ("EPS-Wachstum 5J", f["eps_diluted_growth"]["horizon_5y"]),
            ("EPS-Wachstum 10J", f["eps_diluted_growth"]["horizon_10y"]),
            ("FCF-Wachstum 1J", f["free_cash_flow_growth"]["horizon_1y"]),
            ("FCF-Wachstum 3J", f["free_cash_flow_growth"]["horizon_3y"]),
            ("FCF-Wachstum 5J", f["free_cash_flow_growth"]["horizon_5y"]),
            ("FCF-Wachstum 10J", f["free_cash_flow_growth"]["horizon_10y"]),
            ("Bruttomarge", f["margins"]["gross_margin"]),
            ("Operative Marge", f["margins"]["operating_margin"]),
            ("Nettomarge", f["margins"]["net_margin"]),
            ("Bruttomarge-Stabilität", f["margins"]["gross_margin_stability"]),
            ("Operative-Marge-Stabilität", f["margins"]["operating_margin_stability"]),
            ("Nettomarge-Stabilität", f["margins"]["net_margin_stability"]),
            ("Eigenkapitalrendite (ROE)", f["returns"]["return_on_equity"]),
            ("ROIC", f["returns"]["return_on_invested_capital"]),
            ("ROIC-Steuersatz-Annahme", f["returns"]["roic_tax_rate_assumption"]),
            ("Cash Conversion", f["cashflow"]["cash_conversion"]),
            ("Investitionsquote (Capex/Umsatz)", f["cashflow"]["capex_ratio"]),
            ("Working Capital", f["cashflow"]["working_capital"]),
            ("Nettoverbindlichkeiten", f["leverage"]["net_debt"]),
            ("EBITDA", f["leverage"]["ebitda"]),
            ("Nettoverbindlichkeiten/EBITDA", f["leverage"]["net_debt_to_ebitda"]),
            ("Zinsdeckung", f["leverage"]["interest_coverage"]),
            ("Ausschüttungsquote", f["shareholder"]["dividend_payout_ratio"]),
            ("Verwässerung 3J", f["shareholder"]["shares_diluted_growth"]["horizon_3y"]),
            ("Datenabdeckung (data_completeness)", f["data_completeness"]),
        ],
    ) + 1

    _write_bullet_list(ws, "Fehlende Felder (missing_fields)", f["missing_fields"], start_row=row)


def _sheet_bewertung(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Bewertung")
    v = data["valuation"]
    m = v["multiples"]

    row = _write_key_value_rows(
        ws,
        [
            ("Kurs je Aktie", m["price_per_share"]),
            ("Marktkapitalisierung", m["market_cap"]),
            ("Enterprise Value", m["enterprise_value"]),
            ("KGV (P/E)", m["price_earnings_ratio"]),
            ("EV/EBITDA", m["ev_to_ebitda"]),
            ("EV/EBIT", m["ev_to_ebit"]),
            ("KBV (P/B)", m["price_to_book"]),
            ("KCFV (P/FCF)", m["price_to_free_cash_flow"]),
            ("FCF-Rendite", m["free_cash_flow_yield"]),
            ("Fairer Wert unteres Band", v["fair_value_lower_band"]),
            ("Fairer Wert oberes Band", v["fair_value_upper_band"]),
            ("Sicherheitsmarge", v["safety_margin"]),
        ],
    ) + 1

    ws.cell(row=row, column=1, value="DCF-Szenarien")
    row += 1
    scenario_rows = [
        [
            name,
            result["fair_value_per_share"],
            result["enterprise_value"],
            result["equity_value"],
            result["assumptions"]["revenue_growth_rate"],
            result["assumptions"]["fcf_margin"],
            result["assumptions"]["wacc"],
            result["assumptions"]["terminal_growth_rate"],
        ]
        for name, result in v["dcf_scenarios"].items()
    ]
    row = _write_table(
        ws,
        [
            "Szenario", "Fairer Wert/Aktie", "Enterprise Value", "Equity Value",
            "Umsatzwachstum", "FCF-Marge", "WACC", "Terminalwachstum",
        ],
        scenario_rows,
        start_row=row,
    ) + 1

    ws.cell(row=row, column=1, value="Peer-Multiples")
    row += 1
    peer_rows = [
        [peer["entity_name"], peer["price_earnings_ratio"], peer["ev_to_ebitda"]]
        for peer in v["peer_multiples"]
    ]
    row = _write_table(ws, ["Peer", "KGV", "EV/EBITDA"], peer_rows, start_row=row) + 1

    _write_bullet_list(ws, "Offene Punkte (missing_data_notes)", v["missing_data_notes"], start_row=row)


def _sheet_risiken(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Risiken")
    f = data["fundamentals"]
    s = data["score"]

    ws.cell(row=1, column=1, value="Zahlenbasierte Warnsignale")
    row = _write_table(
        ws,
        ["Code", "Schweregrad", "Beschreibung", "Beleg"],
        [[w["code"], w["severity"], w["description"], w["evidence"]] for w in f["warning_signals"]],
        start_row=2,
    ) + 1

    row = _write_bullet_list(
        ws, "Nicht implementierbare Warnsignale (dokumentierte Lücke)",
        list(f["not_yet_implementable_signals"]), start_row=row,
    )

    ws.cell(row=row, column=1, value="Score-Risikoabzüge")
    row += 1
    row = _write_table(
        ws,
        ["Code", "Schweregrad", "Punkte", "Beschreibung"],
        [[r["code"], r["severity"], r["points"], r["description"]] for r in s["risk_deductions"]],
        start_row=row,
    ) + 1

    _write_bullet_list(ws, "Bedingungen für Ungültigkeit der These", s["invalidation_conditions"], start_row=row)


def _sheet_nachrichten(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Nachrichten")
    n = data["news"]

    row = _write_key_value_rows(
        ws,
        [
            ("Gesamtanzahl Meldungen", n["total_items"]),
            ("Ohne bekanntes Datum", n["items_without_published_date"]),
            ("Anzahl Ereignis-Cluster", len(n["clusters"])),
        ],
    ) + 1

    rows: list[list[Any]] = []
    for cluster in n["clusters"]:
        for item in cluster["items"]:
            rows.append(
                [
                    cluster["event_type"],
                    item["title"],
                    item["url"],
                    item["domain"],
                    item["source_category"],
                    item["published_at"],
                ]
            )
    _write_table(
        ws,
        ["Ereignistyp", "Titel", "URL", "Domain", "Quellqualität", "Veröffentlicht am"],
        rows,
        start_row=row,
    )


def _sheet_quellen(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Quellen")
    _write_table(
        ws,
        ["Key", "Anzeigename", "Lizenzhinweis"],
        [[s["key"], s["display_name"], s["license_note"]] for s in data["sources"]],
    )


def _sheet_annahmen(wb: Workbook, data: dict[str, Any]) -> None:
    ws = wb.create_sheet("Annahmen")
    for row, note in enumerate(data["assumptions"], start=1):
        ws.cell(row=row, column=1, value=_excel_safe(note))


def build_excel_workbook(bundle: ReportBundle) -> Workbook:
    """Baut die vollständige Arbeitsmappe mit allen sieben Auftrag-§10-Tabellenblättern."""

    data = report_bundle_to_dict(bundle)
    wb = Workbook()
    _sheet_zusammenfassung(wb, data)
    _sheet_kennzahlen(wb, data)
    _sheet_bewertung(wb, data)
    _sheet_risiken(wb, data)
    _sheet_nachrichten(wb, data)
    _sheet_quellen(wb, data)
    _sheet_annahmen(wb, data)
    return wb


def export_excel(bundle: ReportBundle, path: str | Path) -> None:
    build_excel_workbook(bundle).save(path)
