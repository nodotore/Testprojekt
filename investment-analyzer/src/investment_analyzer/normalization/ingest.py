"""Ingestion: Connector-Rohdaten → provenienzbehaftete ``DataPoint``-Zeilen (Auftrag §5).

Jede Funktion hier nimmt das typisierte Ergebnis eines Connectors
(``SecCompanyConcept``, ``AlphaVantageQuote``, siehe ``connectors/``)
entgegen und erzeugt daraus ``DataPoint``-Zeilen mit vollständiger
Provenienz (Quelle, direkte URL, Dokumenttyp, Rohwert/normalisierter
Wert, geschätzt/gemeldet/berechnet, Abrufzeitpunkt UTC, Hash).

``DataPoint`` ist append-only (ADR-6): Ein bereits als identisch
erkannter Fakt (dieselbe Entity/Quelle/Kennzahl/Berichtsperiode/
Einreichung) wird nicht dupliziert. Neue Beobachtungen (z. B. ein
späterer Kurs-Snapshot, eine neue Einreichung mit anderer Accession
Number) werden dagegen immer als neue Zeile gespeichert — genau das
macht Point-in-time-Abfragen und Restatement-Historie erst möglich.
"""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.connectors.alpha_vantage import AlphaVantageQuote
from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.sec_edgar import SecCompanyConcept, SecSubmissions
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.metrics import Metric, resolve_metric
from investment_analyzer.normalization.models import DataPoint, ValueKind


def _sha256(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _sec_filing_index_url(cik: str, accession_number: str) -> str:
    """Baut die URL zur EDGAR-Einreichungsübersicht (das eigentliche Belegdokument)."""

    cik_no_leading_zeros = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/"
        f"{accession_no_dashes}/{accession_number}-index.htm"
    )


def ingest_sec_company_concept(
    session: Session,
    *,
    entity: Entity,
    source: Source,
    concept: SecCompanyConcept,
    metric: Metric | None = None,
) -> list[DataPoint]:
    """Wandelt eine ``SecCompanyConcept`` (eine XBRL-Kennzahl, alle Perioden) in DataPoints um.

    Der XBRL-Tag (``concept.tag``) wird auf eine kanonische Kennzahl
    (``fundamentals.metrics.Metric``) abgebildet — entweder automatisch
    über ``resolve_metric`` oder explizit über ``metric`` (z. B. für
    Tags, die (noch) nicht im Mapping stehen). Ist keines von beiden
    möglich, wird ein ``ValueError`` ausgelöst statt die Kennzahl unter
    einem uneinheitlichen Rohnamen zu speichern (Auftrag §6: verbindliches
    Kennzahlen-Vokabular ab Milestone 3).

    Jede von der SEC gemeldete Periode/Einreichung wird zu einer Zeile mit
    ``value_kind=REPORTED``. Bereits vorhandene (Entity, Kennzahl,
    Berichtsperiode, Einreichung) werden nicht erneut eingefügt.
    """

    resolved_metric = metric or resolve_metric(concept.tag)
    if resolved_metric is None:
        raise ValueError(
            f"XBRL-Tag {concept.tag!r} ist nicht im Kennzahlen-Mapping "
            "(fundamentals/metrics.py) bekannt. Entweder das Mapping ergänzen "
            "oder den Parameter 'metric' explizit angeben."
        )

    existing_keys = {
        (period_end, document_id)
        for period_end, document_id in session.execute(
            select(DataPoint.period_end, DataPoint.document_id).where(
                DataPoint.entity_id == entity.id,
                DataPoint.source_id == source.id,
                DataPoint.metric_name == resolved_metric.value,
            )
        ).all()
    }

    created: list[DataPoint] = []
    for fact in concept.facts:
        key = (fact.end_date, fact.accession_number)
        if key in existing_keys:
            continue

        data_point = DataPoint(
            entity_id=entity.id,
            source_id=source.id,
            metric_name=resolved_metric.value,
            period_start=fact.start_date,
            period_end=fact.end_date,
            fiscal_year=fact.fiscal_year,
            published_at=fact.filed_date,
            retrieved_at_utc=concept.fetched_at_utc,
            value_raw=str(fact.value),
            value_normalized=fact.value,
            unit=fact.unit,
            currency=fact.unit if fact.unit.upper() == "USD" else None,
            value_kind=ValueKind.REPORTED,
            quality_score=0.95,
            confidence_score=0.95,
            document_url=_sec_filing_index_url(concept.cik, fact.accession_number),
            document_type=fact.form,
            content_hash=_sha256(
                resolved_metric.value,
                fact.unit,
                str(fact.value),
                fact.end_date.isoformat(),
                fact.accession_number,
            ),
            document_id=fact.accession_number,
        )
        session.add(data_point)
        created.append(data_point)
        existing_keys.add(key)

    return created


def ingest_alpha_vantage_quote(
    session: Session, *, entity: Entity, source: Source, quote: AlphaVantageQuote
) -> DataPoint:
    """Wandelt einen Alpha-Vantage-``GLOBAL_QUOTE``-Snapshot in einen DataPoint um.

    Bekannte Einschränkung: ``GLOBAL_QUOTE`` liefert keine Währungsangabe.
    Statt eine Währung zu raten (verboten, Auftrag §11 „Wurde eine Annahme
    als Tatsache formuliert?"), wird ``currency`` explizit auf ``None``
    gesetzt und Qualität/Konfidenz entsprechend reduziert. Die Auflösung
    der tatsächlichen Notierungswährung über Börsen-Metadaten ist als
    offener Punkt in ``TODO.md`` vermerkt (Milestone 3).
    """

    data_point = DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name="price_close",
        period_start=None,
        period_end=quote.latest_trading_day,
        fiscal_year=None,
        published_at=quote.latest_trading_day,
        retrieved_at_utc=quote.fetched_at_utc,
        value_raw=str(quote.price),
        value_normalized=float(quote.price),
        unit="price_per_share",
        currency=None,
        value_kind=ValueKind.REPORTED,
        quality_score=0.6,
        confidence_score=0.6,
        document_url=quote.source_url,
        document_type="market_data_snapshot",
        content_hash=_sha256(quote.symbol, str(quote.price), quote.latest_trading_day.isoformat()),
        document_id=None,
    )
    session.add(data_point)
    return data_point


def update_entity_classification(entity: Entity, submissions: SecSubmissions) -> None:
    """Aktualisiert die SIC-Branchenklassifikation einer Entity aus SEC-Submissions.

    Grundlage für die Peer-Gruppen-Zuordnung (Auftrag §6,
    ``fundamentals/peers.py``). Ändert nur das übergebene ``Entity``-
    Objekt in-memory; der Aufrufer committed die Session. Überschreibt
    einen vorhandenen Wert nur, wenn die Antwort tatsächlich einen neuen
    liefert — eine unvollständige Antwort löscht keine bereits bekannte
    Klassifikation.
    """

    if submissions.sic:
        entity.sic_code = submissions.sic
    if submissions.sic_description:
        entity.sic_description = submissions.sic_description
