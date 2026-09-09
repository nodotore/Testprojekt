"""Orchestrierung: Ticker/CIK → Entity → abgerufene, gespeicherte Kennzahlen.

Bindet bereits unabhängig getestete Bausteine (``connectors/``,
``entity_resolution/``, ``normalization/``) für den Marktscreener
(Auftrag §10, Seite 2) zusammen — siehe ``ingestion/pipeline.py``.
"""

from __future__ import annotations

from investment_analyzer.ingestion.pipeline import (
    AlphaVantageIngestResult,
    SecIngestResult,
    add_and_ingest_alpha_vantage_price,
    add_and_ingest_sec_edgar,
    resolve_ticker_to_cik,
)

__all__ = [
    "AlphaVantageIngestResult",
    "SecIngestResult",
    "add_and_ingest_alpha_vantage_price",
    "add_and_ingest_sec_edgar",
    "resolve_ticker_to_cik",
]
