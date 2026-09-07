from __future__ import annotations

from datetime import date

import httpx
import pytest

from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.sec_edgar import (
    ALLOWED_HOSTS,
    SecEdgarConnector,
    build_config,
)


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("23.216.9.1", port or 443))]


TICKER_LIST_RESPONSE = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}

SUBMISSIONS_RESPONSE = {
    "cik": "320193",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "exchanges": ["Nasdaq"],
    "filings": {
        "recent": {
            "accessionNumber": ["0000320193-24-000123", "0000320193-24-000045"],
            "form": ["10-K", "10-Q"],
            "filingDate": ["2024-11-01", "2024-08-02"],
            "reportDate": ["2024-09-28", "2024-06-29"],
            "primaryDocument": ["aapl-20240928.htm", "aapl-20240629.htm"],
        }
    },
}

COMPANY_CONCEPT_RESPONSE = {
    "cik": 320193,
    "taxonomy": "us-gaap",
    "tag": "Revenues",
    "label": "Revenues",
    "description": "Umsatzerlöse.",
    "units": {
        "USD": [
            {
                "start": "2023-10-01",
                "end": "2023-12-30",
                "val": 119575000000,
                "fy": 2024,
                "fp": "Q1",
                "form": "10-Q",
                "filed": "2024-02-01",
                "accn": "0000320193-24-000010",
            },
            {
                "start": "2022-10-01",
                "end": "2022-12-31",
                "val": 117154000000,
                "fy": 2023,
                "fp": "Q1",
                "form": "10-Q",
                "filed": "2023-02-02",
                "accn": "0000320193-23-000012",
            },
        ]
    },
}


def _connector(handler) -> SecEdgarConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    return SecEdgarConnector(
        contact="kontakt@example.invalid",
        http_client=client,
        ssrf_resolver=_public_ip_resolver,
    )


def test_build_config_lehnt_leeren_kontakt_ab() -> None:
    with pytest.raises(ValueError, match="contact"):
        build_config(contact="  ")


def test_build_config_enthaelt_kontakt_im_user_agent() -> None:
    config = build_config(contact="kontakt@example.invalid")
    assert "kontakt@example.invalid" in config.default_headers["User-Agent"]
    assert config.allowed_hosts == ALLOWED_HOSTS


def test_default_rate_limit_ist_hoechstens_10_pro_sekunde() -> None:
    connector = _connector(lambda request: httpx.Response(200, json={}))
    assert connector._rate_limiter is not None  # type: ignore[attr-defined]
    assert connector._rate_limiter.max_calls == 10  # type: ignore[attr-defined]
    assert connector._rate_limiter.period_seconds == 1.0  # type: ignore[attr-defined]


def test_resolve_cik_by_ticker_findet_bekannten_ticker() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "www.sec.gov"
        return httpx.Response(200, json=TICKER_LIST_RESPONSE)

    connector = _connector(handler)
    mapping = connector.resolve_cik_by_ticker("aapl")

    assert mapping.cik == "0000320193"
    assert mapping.ticker == "AAPL"
    assert mapping.title == "Apple Inc."


def test_resolve_cik_by_ticker_unbekannter_ticker_wirft() -> None:
    connector = _connector(lambda request: httpx.Response(200, json=TICKER_LIST_RESPONSE))
    with pytest.raises(ConnectorValidationError, match="XYZ"):
        connector.resolve_cik_by_ticker("XYZ")


def test_get_submissions_liefert_geparste_filings() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "data.sec.gov"
        assert "CIK0000320193.json" in str(request.url)
        return httpx.Response(200, json=SUBMISSIONS_RESPONSE)

    connector = _connector(handler)
    submissions = connector.get_submissions("320193")

    assert submissions.cik == "0000320193"
    assert submissions.name == "Apple Inc."
    assert submissions.tickers == ("AAPL",)
    assert len(submissions.filings) == 2
    erster = submissions.filings[0]
    assert erster.accession_number == "0000320193-24-000123"
    assert erster.form == "10-K"
    assert erster.filing_date == date(2024, 11, 1)
    assert erster.report_date == date(2024, 9, 28)
    assert erster.primary_document == "aapl-20240928.htm"


def test_get_submissions_bei_kaputtem_format_wirft_validierungsfehler() -> None:
    connector = _connector(lambda request: httpx.Response(200, json={"cik": "1"}))
    with pytest.raises(ConnectorValidationError):
        connector.get_submissions("320193")


def test_get_company_concept_liefert_facts_mit_provenienz() -> None:
    connector = _connector(lambda request: httpx.Response(200, json=COMPANY_CONCEPT_RESPONSE))
    concept = connector.get_company_concept("320193", "Revenues")

    assert concept.tag == "Revenues"
    assert len(concept.facts) == 2
    neuester = concept.facts[0]
    assert neuester.value == 119575000000
    assert neuester.unit == "USD"
    assert neuester.end_date == date(2023, 12, 30)
    assert neuester.start_date == date(2023, 10, 1)
    assert neuester.filed_date == date(2024, 2, 1)
    assert neuester.accession_number == "0000320193-24-000010"
    assert neuester.form == "10-Q"
    assert neuester.fiscal_year == 2024


def test_get_company_concept_bei_kaputtem_format_wirft_validierungsfehler() -> None:
    connector = _connector(lambda request: httpx.Response(200, json={"units": {"USD": [{}]}}))
    with pytest.raises(ConnectorValidationError):
        connector.get_company_concept("320193", "Revenues")
