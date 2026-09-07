"""Normalisierung und provenienzbehaftete Datenpunkte (Auftrag §5, §6).

``models.py`` enthält das ``DataPoint``-Kernmodell (roh + normalisiert,
append-only). ``ingest.py`` wandelt Connector-Rohergebnisse in
``DataPoint``-Zeilen um (ab Milestone 2: SEC EDGAR, Alpha Vantage;
weitere Normalisierungsschritte — Einheiten, Geschäftsjahresabgleich,
Split-/Dividenden-Anpassung — folgen in Milestone 3).
"""

from investment_analyzer.normalization.ingest import (
    ingest_alpha_vantage_quote,
    ingest_sec_company_concept,
    update_entity_classification,
)
from investment_analyzer.normalization.models import DataPoint, ValueKind

__all__ = [
    "DataPoint",
    "ValueKind",
    "ingest_alpha_vantage_quote",
    "ingest_sec_company_concept",
    "update_entity_classification",
]
