from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.gdelt import GdeltConnector, build_config


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("104.18.10.1", port or 443))]


ARTICLES_RESPONSE = {
    "articles": [
        {
            "url": "https://example-news.test/artikel-1",
            "title": "Firma E meldet Rekordumsatz",
            "domain": "example-news.test",
            "language": "German",
            "sourcecountry": "Germany",
            "seendate": "20260301T120000Z",
        },
        {
            "url": "https://another-outlet.test/artikel-2",
            "title": "Firma E: Analysten reagieren zurückhaltend",
            "domain": "another-outlet.test",
            "language": "English",
            "sourcecountry": "United States",
            "seendate": "20260301T150000Z",
        },
    ]
}


def _connector(handler, *, cache_dir: Path | None = None) -> GdeltConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cache = FileCache(cache_dir) if cache_dir is not None else None
    return GdeltConnector(http_client=client, cache=cache, ssrf_resolver=_public_ip_resolver)


def test_build_config_hat_erwartete_allowlist() -> None:
    config = build_config()
    assert config.allowed_hosts == frozenset({"api.gdeltproject.org"})
    assert config.key == "gdelt"


def test_leere_query_wird_abgelehnt() -> None:
    connector = _connector(lambda request: httpx.Response(200, json=ARTICLES_RESPONSE))
    with pytest.raises(ValueError, match="query"):
        connector.search_articles("  ")


def test_search_articles_liefert_geparste_artikel() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.gdeltproject.org"
        assert "query=Firma+E" in str(request.url) or "query=Firma%20E" in str(request.url)
        assert "format=json" in str(request.url)
        return httpx.Response(200, json=ARTICLES_RESPONSE)

    connector = _connector(handler)
    result = connector.search_articles("Firma E")

    assert len(result.articles) == 2
    first = result.articles[0]
    assert first.url == "https://example-news.test/artikel-1"
    assert first.title == "Firma E meldet Rekordumsatz"
    assert first.domain == "example-news.test"
    assert first.language == "German"
    assert first.seen_at is not None
    assert first.seen_at.isoformat() == "2026-03-01T12:00:00+00:00"


def test_artikel_ohne_url_wird_uebersprungen() -> None:
    body = {"articles": [{"title": "Ohne URL"}, ARTICLES_RESPONSE["articles"][0]]}
    connector = _connector(lambda request: httpx.Response(200, json=body))
    result = connector.search_articles("Firma E")
    assert len(result.articles) == 1


def test_fehlender_titel_faellt_auf_url_zurueck() -> None:
    body = {"articles": [{"url": "https://example-news.test/ohne-titel"}]}
    connector = _connector(lambda request: httpx.Response(200, json=body))
    result = connector.search_articles("Firma E")
    assert result.articles[0].title == "https://example-news.test/ohne-titel"


def test_unerwartetes_format_wird_als_validierungsfehler_gemeldet() -> None:
    connector = _connector(lambda request: httpx.Response(200, json={"articles": "kaputt"}))
    with pytest.raises(ConnectorValidationError, match="Liste"):
        connector.search_articles("Firma E")


def test_kein_json_wird_als_validierungsfehler_gemeldet() -> None:
    connector = _connector(lambda request: httpx.Response(200, text="<html>Fehlerseite</html>"))
    with pytest.raises(ConnectorValidationError):
        connector.search_articles("Firma E")


def test_unbekanntes_seendate_format_liefert_none_statt_falschem_datum() -> None:
    body = {
        "articles": [
            {
                "url": "https://example-news.test/artikel-3",
                "title": "Test",
                "seendate": "nicht-geparsbar",
            }
        ]
    }
    connector = _connector(lambda request: httpx.Response(200, json=body))
    result = connector.search_articles("Firma E")
    assert result.articles[0].seen_at is None


def test_timespan_wird_als_query_parameter_weitergereicht() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "timespan=7d" in str(request.url)
        return httpx.Response(200, json=ARTICLES_RESPONSE)

    connector = _connector(handler)
    connector.search_articles("Firma E", timespan="7d")


def test_default_rate_limit_ist_konservativ() -> None:
    connector = _connector(lambda request: httpx.Response(200, json=ARTICLES_RESPONSE))
    assert connector._rate_limiter is not None  # type: ignore[attr-defined]
    assert connector._rate_limiter.max_calls == 20  # type: ignore[attr-defined]
