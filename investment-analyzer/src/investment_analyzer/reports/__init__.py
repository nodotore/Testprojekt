"""PDF-/Excel-/JSON-Export (Auftrag §2, §10). Siehe ADR-3 in DECISIONS.md
für Modulgrenzen und ADR-21 für die ReportBundle-Designentscheidung."""

from investment_analyzer.reports.bundle import (
    ReportBundle,
    ReportHeader,
    SourceInfo,
    build_report_bundle,
)
from investment_analyzer.reports.excel_export import build_excel_workbook, export_excel
from investment_analyzer.reports.json_export import report_bundle_to_dict, report_bundle_to_json
from investment_analyzer.reports.pdf_export import build_pdf_bytes, export_pdf

__all__ = [
    "ReportBundle",
    "ReportHeader",
    "SourceInfo",
    "build_excel_workbook",
    "build_pdf_bytes",
    "build_report_bundle",
    "export_excel",
    "export_pdf",
    "report_bundle_to_dict",
    "report_bundle_to_json",
]
