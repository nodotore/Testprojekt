from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from investment_analyzer.connectors.alpha_vantage import AlphaVantageConnector, build_config
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import (
    ConnectorRateLimitedError,
    ConnectorValidationError,
)


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("104.18.10.1", port or 443))]


GLOBAL_QUOTE_RESPONSE = {
    "Global Quote": {
        "01. symbol": "IBM",
        "02. open": "230.0000",
        "03. high": "233.5000",
        "04. low": "229.8000",
        "05. price": "232.4200",
        "06. volume": "3465234",
        "07. latest trading day": "2024-09-06",
        "08. previous close": "230.0900",
        "09. change": "2.3300",
        "10. change percent": "1.0127%",
    }
}


def _connector(handler, *, cache_dir: Path | None = None, api_key: str = "TESTKEY") -> AlphaVantageConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cache = FileCache(cache_dir) if cache_dir is not None else None
    return AlphaVantageConnector(
        api_key=api_key, http_client=client, cache=cache, ssrf_resolver=_public_ip_resolver
    )


def test_build_config_hat_free_tier_ttl_und_allowlist() -> None:
    config = build_config()
    assert config.allowed_hosts == frozenset({"www.alphavantage.co"})
    assert config.key == "alpha_vantage"


def test_leerer_api_key_wird_abgelehnt() -> None:
    with pytest.raises(ValueError, match="api_key"):
        AlphaVantageConnector(api_key="  ")


def test_get_quote_liefert_geparsten_kurs(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "www.alphavantage.co"
        assert "apikey=TESTKEY" in str(request.url)
        assert "symbol=IBM" in str(request.url)
        return httpx.Response(200, json=GLOBAL_QUOTE_RESPONSE)

    connector = _connector(handler, cache_dir=tmp_path)
    quote = connector.get_quote("IBM")

    assert quote.symbol == "IBM"
    assert quote.price == Decimal("232.4200")
    assert quote.previous_close == Decimal("230.0900")
    assert quote.volume == 3465234
    assert quote.latest_trading_day.isoformat() == "2024-09-06"
    assert "apikey" not in quote.source_url
    assert "symbol=IBM" in quote.source_url


def test_default_rate_limit_ist_5_pro_minute() -> None:
    connector = _connector(lambda request: httpx.Response(200, json=GLOBAL_QUOTE_RESPONSE))
    assert connector._rate_limiter is not None  # type: ignore[attr-defined]
    assert connector._rate_limiter.max_calls == 5  # type: ignore[attr-defined]
    assert connector._rate_limiter.period_seconds == 60.0  # type: ignore[attr-defined]


def test_rate_limit_hinweis_im_200er_body_wird_erkannt() -> None:
    body = {
        "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is "
        "25 requests per day."
    }
    connector = _connector(lambda request: httpx.Response(200, json=body))
    with pytest.raises(ConnectorRateLimitedError, match="Rate-Limit"):
        connector.get_quote("IBM")


def test_information_hinweis_wird_wie_rate_limit_behandelt() -> None:
    body = {"Information": "Invalid API call, please check your API key."}
    connector = _connector(lambda request: httpx.Response(200, json=body))
    with pytest.raises(ConnectorRateLimitedError):
        connector.get_quote("IBM")


def test_error_message_wird_als_validierungsfehler_gemeldet() -> None:
    body = {"Error Message": "Invalid API call."}
    connector = _connector(lambda request: httpx.Response(200, json=body))
    with pytest.raises(ConnectorValidationError, match="Invalid API call"):
        connector.get_quote("NICHT-EXISTENT")


def test_leeres_kursobjekt_wird_als_validierungsfehler_gemeldet() -> None:
    connector = _connector(lambda request: httpx.Response(200, json={"Global Quote": {}}))
    with pytest.raises(ConnectorValidationError, match="unbekanntes Symbol"):
        connector.get_quote("XXXX")


def test_kaputtes_format_wird_als_validierungsfehler_gemeldet() -> None:
    connector = _connector(
        lambda request: httpx.Response(200, json={"Global Quote": {"01. symbol": "IBM"}})
    )
    with pytest.raises(ConnectorValidationError):
        connector.get_quote("IBM")


def test_api_key_landet_nie_im_dateisystem_cache(tmp_path: Path) -> None:
    connector = _connector(
        lambda request: httpx.Response(200, json=GLOBAL_QUOTE_RESPONSE),
        cache_dir=tmp_path,
        api_key="SUPER-GEHEIMER-SCHLUESSEL",
    )
    connector.get_quote("IBM")

    for cache_file in tmp_path.rglob("*.json"):
        assert "SUPER-GEHEIMER-SCHLUESSEL" not in cache_file.read_text(encoding="utf-8")
