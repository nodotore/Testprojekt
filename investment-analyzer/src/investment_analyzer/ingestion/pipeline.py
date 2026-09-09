"""Orchestrierung: Ticker/CIK → Entity → abgerufene, gespeicherte Kennzahlen
(Marktscreener, Auftrag §10 Seite 2).

Bindet bereits unabhängig getestete Bausteine zusammen
(``connectors.sec_edgar``/``connectors.alpha_vantage``,
``entity_resolution.service``, ``normalization.ingest``) — erzeugt selbst
KEINE neuen Werte, reine Orchestrierung (Auftrag §11).

Nimmt bereits konstruierte Connector-Instanzen entgegen (keine eigene
HTTP-Client-/Cache-/Rate-Limiter-Konfiguration) — das hält dieses Modul
vollständig testbar ohne echten Netzwerkzugriff (siehe
``tests/ingestion/test_pipeline.py``, analog zum bestehenden Testmuster
in ``tests/connectors/``) und lässt die Aufrufer (UI, künftig auch ein
CLI-Werkzeug) entscheiden, wie der Connector konfiguriert wird (Cache-
Verzeichnis, Rate-Limiter, SSRF-Resolver).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from investment_analyzer.connectors.alpha_vantage import AlphaVantageConnector
from investment_analyzer.connectors.errors import ConnectorHTTPError
from investment_analyzer.connectors.sec_edgar import SecEdgarConnector
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import SEC_US_GAAP_TAG_TO_METRIC, Metric
from investment_analyzer.normalization.ingest import (
    ingest_alpha_vantage_quote,
    ingest_sec_company_concept,
    update_entity_classification,
)
from investment_analyzer.normalization.models import DataPoint


def _tag_candidates_by_metric() -> dict[Metric, tuple[str, ...]]:
    """Gruppiert ``SEC_US_GAAP_TAG_TO_METRIC`` umgekehrt: Kennzahl → mögliche XBRL-Tags.

    Manche Kennzahl kann von verschiedenen Unternehmen unter unter-
    schiedlichen, gleichbedeutenden XBRL-Tags gemeldet werden (z. B.
    ``Revenues`` vs. ``RevenueFromContractWithCustomer...``) — beim Abruf
    werden alle Kandidaten der Reihe nach versucht.
    """

    grouped: dict[Metric, list[str]] = defaultdict(list)
    for tag, metric in SEC_US_GAAP_TAG_TO_METRIC.items():
        grouped[metric].append(tag)
    return {metric: tuple(tags) for metric, tags in grouped.items()}


#: Einmal beim Modulimport berechnet -- ``SEC_US_GAAP_TAG_TO_METRIC`` ist statisch.
TAG_CANDIDATES_BY_METRIC: dict[Metric, tuple[str, ...]] = _tag_candidates_by_metric()


@dataclass(frozen=True)
class SecIngestResult:
    """Ergebnis eines SEC-EDGAR-Abrufs für eine Entity — für die Anzeige im Marktscreener."""

    entity: Entity
    neue_datenpunkte: int
    abgefragte_kennzahlen: tuple[str, ...]
    nicht_gemeldete_kennzahlen: tuple[str, ...]


@dataclass(frozen=True)
class AlphaVantageIngestResult:
    entity: Entity
    data_point: DataPoint


def resolve_ticker_to_cik(connector: SecEdgarConnector, ticker: str) -> str:
    """Löst einen US-Ticker über die offizielle SEC-Ticker-Liste zu einer CIK auf.

    Wirft ``ConnectorValidationError``, falls der Ticker nicht bekannt ist
    (siehe ``SecEdgarConnector.resolve_cik_by_ticker``) — kein Raten einer
    CIK (Auftrag §11).
    """

    return connector.resolve_cik_by_ticker(ticker).cik


def add_and_ingest_sec_edgar(session: Session, connector: SecEdgarConnector, *, cik: str) -> SecIngestResult:
    """Legt eine Entity per CIK an/findet die bestehende und ruft alle im
    Kennzahlen-Vokabular (``fundamentals/metrics.py``) bekannten XBRL-
    Kennzahlen ab.

    Ein XBRL-Tag, den dieses Unternehmen nie gemeldet hat, liefert von der
    SEC HTTP 404 — das gilt hier NICHT als Fehlschlag der gesamten
    Ingestion, sondern wird als „nicht gemeldet" vermerkt (fehlende
    Kennzahlen erscheinen später ehrlich als ``None``/in
    ``FundamentalsReport.missing_fields``, statt die Ingestion vorzeitig
    abzubrechen). Jeder andere Fehler (Timeout, 5xx, ungültiges Format)
    wird NICHT abgefangen — er soll sichtbar bis zur Oberfläche
    durchschlagen (Auftrag §4: „Fail loud, nicht silent").
    """

    sources = ensure_default_sources(session)
    source = sources["sec_edgar"]

    submissions = connector.get_submissions(cik)

    identifiers = [IdentifierSpec(id_type=IdentifierType.CIK, id_value=submissions.cik)]
    identifiers.extend(
        IdentifierSpec(id_type=IdentifierType.TICKER, id_value=ticker) for ticker in submissions.tickers
    )

    entity = find_or_create_entity(
        session,
        name=submissions.name,
        identifiers=identifiers,
        country="US",  # SEC EDGAR deckt ausschließlich US-Einreicher ab (DATA_SOURCES.md).
        primary_exchange=submissions.exchanges[0] if submissions.exchanges else None,
    )
    update_entity_classification(entity, submissions)

    neue_datenpunkte = 0
    abgefragte_kennzahlen: list[str] = []
    nicht_gemeldete_kennzahlen: list[str] = []

    for metric in sorted(TAG_CANDIDATES_BY_METRIC, key=lambda m: m.value):
        gefunden = False
        for tag in TAG_CANDIDATES_BY_METRIC[metric]:
            try:
                concept = connector.get_company_concept(submissions.cik, tag)
            except ConnectorHTTPError as exc:
                if exc.status_code == 404:
                    continue  # dieses Unternehmen meldet diesen konkreten Tag nicht -- nächster Kandidat
                raise
            created = ingest_sec_company_concept(
                session, entity=entity, source=source, concept=concept, metric=metric
            )
            neue_datenpunkte += len(created)
            abgefragte_kennzahlen.append(metric.value)
            gefunden = True
            break
        if not gefunden:
            nicht_gemeldete_kennzahlen.append(metric.value)

    return SecIngestResult(
        entity=entity,
        neue_datenpunkte=neue_datenpunkte,
        abgefragte_kennzahlen=tuple(abgefragte_kennzahlen),
        nicht_gemeldete_kennzahlen=tuple(nicht_gemeldete_kennzahlen),
    )


def add_and_ingest_alpha_vantage_price(
    session: Session, connector: AlphaVantageConnector, *, entity: Entity, symbol: str
) -> AlphaVantageIngestResult:
    """Ruft einen aktuellen Kurs-Snapshot (``GLOBAL_QUOTE``) ab und speichert ihn.

    ``entity`` muss bereits existieren (siehe ``add_and_ingest_sec_edgar``)
    — dieses Modul rät keine Entity-Zuordnung allein aus einem Kurssymbol,
    das wäre keine stabile Kennung (Auftrag §5).
    """

    sources = ensure_default_sources(session)
    source = sources["alpha_vantage"]
    quote = connector.get_quote(symbol)
    data_point = ingest_alpha_vantage_quote(session, entity=entity, source=source, quote=quote)
    return AlphaVantageIngestResult(entity=entity, data_point=data_point)
