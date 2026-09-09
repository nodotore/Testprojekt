from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from investment_analyzer.connectors.alpha_vantage import AlphaVantageConnector
from investment_analyzer.connectors.errors import ConnectorHTTPError, ConnectorValidationError
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.sec_edgar import SecEdgarConnector
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.ingestion.pipeline import (
    TAG_CANDIDATES_BY_METRIC,
    add_and_ingest_alpha_vantage_price,
    add_and_ingest_sec_edgar,
    resolve_ticker_to_cik,
)


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("23.216.9.1", port or 443))]


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'ingestion-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _sec_connector(handler) -> SecEdgarConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    # Ein Ingestion-Lauf über alle bekannten Kennzahlen (TAG_CANDIDATES_BY_METRIC)
    # feuert deutlich mehr als 10 Anfragen ab -- ein großzügiger Test-Rate-Limiter
    # vermeidet echtes time.sleep() im Standard-Rate-Limiter der SEC-Konfiguration.
    return SecEdgarConnector(
        contact="kontakt@example.invalid",
        http_client=client,
        ssrf_resolver=_public_ip_resolver,
        rate_limiter=RateLimiter(1000, 1.0, sleep=lambda seconds: None),
    )


def _av_connector(handler) -> AlphaVantageConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    return AlphaVantageConnector(
        api_key="TESTKEY", http_client=client, ssrf_resolver=_public_ip_resolver
    )


SUBMISSIONS_RESPONSE = {
    "cik": "320193",
    "name": "Apple Inc. (Testfixtur)",
    "tickers": ["AAPL"],
    "exchanges": ["Nasdaq"],
    "sic": "3571",
    "sicDescription": "Electronic Computers",
    "filings": {"recent": {"accessionNumber": [], "form": [], "filingDate": [], "reportDate": [], "primaryDocument": []}},
}


def _company_concept_json(tag: str, value: float) -> dict:
    return {
        "cik": 320193,
        "taxonomy": "us-gaap",
        "tag": tag,
        "label": tag,
        "description": None,
        "units": {
            "USD": [
                {
                    "start": "2023-01-01",
                    "end": "2023-12-31",
                    "val": value,
                    "fy": 2023,
                    "fp": "FY",
                    "form": "10-K",
                    "filed": "2024-02-01",
                    "accn": "0000320193-24-000010",
                }
            ]
        },
    }


def _sec_handler_with_two_reported_tags(request: httpx.Request) -> httpx.Response:
    """Simuliert eine reale SEC-Antwort: Submissions + genau zwei gemeldete
    XBRL-Tags (Revenues, NetIncomeLoss), alle anderen abgefragten Tags
    liefern HTTP 404 (vom Unternehmen nicht gemeldet)."""

    path = request.url.path
    if path.endswith("/submissions/CIK0000320193.json"):
        return httpx.Response(200, json=SUBMISSIONS_RESPONSE)
    if path.endswith("/Revenues.json"):
        return httpx.Response(200, json=_company_concept_json("Revenues", 1000.0))
    if path.endswith("/NetIncomeLoss.json"):
        return httpx.Response(200, json=_company_concept_json("NetIncomeLoss", 100.0))
    return httpx.Response(404)


def test_add_and_ingest_sec_edgar_legt_entity_mit_cik_und_ticker_an(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        connector = _sec_connector(_sec_handler_with_two_reported_tags)
        result = add_and_ingest_sec_edgar(session, connector, cik="0000320193")
        session.commit()

        assert result.entity.name == "Apple Inc. (Testfixtur)"
        assert result.entity.country == "US"
        assert result.entity.primary_exchange == "Nasdaq"
        assert result.entity.sic_code == "3571"

        identifiers = {(i.id_type, i.id_value) for i in result.entity.identifiers}
        assert (IdentifierType.CIK, "0000320193") in identifiers
        assert (IdentifierType.TICKER, "AAPL") in identifiers


def test_add_and_ingest_sec_edgar_meldet_gefundene_und_fehlende_kennzahlen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        connector = _sec_connector(_sec_handler_with_two_reported_tags)
        result = add_and_ingest_sec_edgar(session, connector, cik="0000320193")

    assert Metric.REVENUE.value in result.abgefragte_kennzahlen
    assert Metric.NET_INCOME.value in result.abgefragte_kennzahlen
    # Kennzahlen, für die die Testfixtur nur 404 liefert, gelten als "nicht
    # gemeldet" -- kein Abbruch der gesamten Ingestion an einer einzelnen fehlenden Kennzahl.
    assert Metric.TOTAL_EQUITY.value in result.nicht_gemeldete_kennzahlen
    # Jede im Mapping bekannte Kennzahl landet in genau einer der beiden Listen.
    alle_kennzahlen = set(result.abgefragte_kennzahlen) | set(result.nicht_gemeldete_kennzahlen)
    assert alle_kennzahlen == {m.value for m in TAG_CANDIDATES_BY_METRIC}


def test_add_and_ingest_sec_edgar_speichert_datenpunkte_mit_provenienz(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        connector = _sec_connector(_sec_handler_with_two_reported_tags)
        result = add_and_ingest_sec_edgar(session, connector, cik="0000320193")
        session.commit()

    assert result.neue_datenpunkte == 2  # ein Datenpunkt je gemeldeter Kennzahl (Revenue, NetIncome)


def test_add_and_ingest_sec_edgar_ist_idempotent_bei_wiederholtem_abruf(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        connector = _sec_connector(_sec_handler_with_two_reported_tags)
        add_and_ingest_sec_edgar(session, connector, cik="0000320193")
        session.commit()

    with session_factory() as session:
        connector = _sec_connector(_sec_handler_with_two_reported_tags)
        zweiter_lauf = add_and_ingest_sec_edgar(session, connector, cik="0000320193")
        session.commit()

    assert zweiter_lauf.neue_datenpunkte == 0  # dieselben Fakten -- keine Duplikate


def test_add_and_ingest_sec_edgar_gibt_serverfehler_ungefiltert_weiter(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/submissions/CIK0000320193.json"):
            return httpx.Response(200, json=SUBMISSIONS_RESPONSE)
        return httpx.Response(500)

    session_factory = _session_factory(tmp_path)
    with session_factory() as session, pytest.raises(ConnectorHTTPError):
        add_and_ingest_sec_edgar(session, _sec_connector(handler), cik="0000320193")


def test_resolve_ticker_to_cik() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
        )

    cik = resolve_ticker_to_cik(_sec_connector(handler), "AAPL")
    assert cik == "0000320193"


def test_resolve_ticker_to_cik_unbekannter_ticker_wirft() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with pytest.raises(ConnectorValidationError):
        resolve_ticker_to_cik(_sec_connector(handler), "NICHT-VORHANDEN")


def test_add_and_ingest_alpha_vantage_price_speichert_kurs(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sec_connector = _sec_connector(_sec_handler_with_two_reported_tags)
        sec_result = add_and_ingest_sec_edgar(session, sec_connector, cik="0000320193")
        session.commit()
        entity_id = sec_result.entity.id

    def av_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "Global Quote": {
                    "01. symbol": "AAPL",
                    "05. price": "190.50",
                    "08. previous close": "189.00",
                    "09. change": "1.50",
                    "10. change percent": "0.79%",
                    "06. volume": "1000000",
                    "07. latest trading day": "2024-03-01",
                }
            },
        )

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        av_connector = _av_connector(av_handler)
        result = add_and_ingest_alpha_vantage_price(session, av_connector, entity=entity, symbol="AAPL")
        session.commit()

    assert result.data_point.metric_name == Metric.PRICE_CLOSE.value
    assert result.data_point.value_normalized == pytest.approx(190.50)
    assert result.data_point.period_end == date(2024, 3, 1)
