"""Fundamentalanalyse (Auftrag §6 „Fundamentaldaten").

``metrics.py`` definiert das kanonische Kennzahlen-Vokabular (verbindlich
ab Milestone 3, siehe ``normalization/models.py``). Weitere Bausteine
folgen in diesem Modul: Berechnungskern (``calculations.py``),
Zeitreihen-Repository (``series.py``), Peer-Gruppen (``peers.py``) und
die Orchestrierung zu einem ``FundamentalsReport`` (``report.py``).
"""

from investment_analyzer.fundamentals import calculations, series
from investment_analyzer.fundamentals.metrics import (
    FLOW_METRICS,
    SEC_US_GAAP_TAG_TO_METRIC,
    STOCK_METRICS,
    Metric,
    resolve_metric,
)
from investment_analyzer.fundamentals.peers import find_peers
from investment_analyzer.fundamentals.report import FundamentalsReport, build_fundamentals_report

__all__ = [
    "FLOW_METRICS",
    "SEC_US_GAAP_TAG_TO_METRIC",
    "STOCK_METRICS",
    "FundamentalsReport",
    "Metric",
    "build_fundamentals_report",
    "calculations",
    "find_peers",
    "resolve_metric",
    "series",
]
