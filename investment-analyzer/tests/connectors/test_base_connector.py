from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from investment_analyzer.connectors.base import Connector, ConnectorConfig
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import (
    ConnectorHTTPError,
    ConnectorRateLimitedError,
    ConnectorTimeoutError,
    ConnectorValidationError,
    SSRFBlockedError,
)
from investment_analyzer.connectors.rate_limiter import RateLimiter

ALLOWED_HOST = "api.example-connector.invalid"


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("93.184.216.1", port or 443))]


def _config(**overrides) -> ConnectorConfig:
    base = {
        "key": "test_connector",
        "display_name": "Testquelle",
        "base_url": f"https://{ALLOWED_HOST}",
        "allowed_hosts": frozenset({ALLOWED_HOST}),
        "license_note": "nur für Tests",
        "max_retries": 3,
        "backoff_base_seconds": 0.0,
    }
    base.update(overrides)
    return ConnectorConfig(**base)


def _make_connector(handler, *, cache_dir: Path | None = None, rate_limiter=None, sleeps=None):
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cache = FileCache(cache_dir) if cache_dir is not None else None
    sleep_fn = (sleeps.append if sleeps is not None else lambda s: None)
    return Connector(
        _config(),
        http_client=client,
        cache=cache,
        rate_limiter=rate_limiter,
        ssrf_resolver=_public_ip_resolver,
        sleep=sleep_fn,
    )


def test_erfolgreicher_abruf_liefert_daten_und_provenienzfelder(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"foo": "bar"})

    connector = _make_connector(handler, cache_dir=tmp_path)
    result = connector.get_json("/v1/data")

    assert result.data == {"foo": "bar"}
    assert result.from_cache is False
    assert result.status_code == 200
    assert result.url == f"https://{ALLOWED_HOST}/v1/data"
    assert len(calls) == 1


def test_zweiter_abruf_kommt_aus_dem_cache_ohne_erneuten_netzwerkaufruf(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"foo": "bar"})

    connector = _make_connector(handler, cache_dir=tmp_path)
    connector.get_json("/v1/data")
    zweites_ergebnis = connector.get_json("/v1/data")

    assert len(calls) == 1
    assert zweites_ergebnis.from_cache is True
    assert zweites_ergebnis.data == {"foo": "bar"}


def test_ssrf_schutz_blockiert_nicht_erlaubten_host(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - darf nie aufgerufen werden
        raise AssertionError("Transport hätte wegen SSRF-Block nie aufgerufen werden dürfen")

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(SSRFBlockedError):
        connector.get_json("https://evil.example.invalid/x")


def test_retry_bei_serverfehler_und_anschliessendem_erfolg(tmp_path: Path) -> None:
    responses = [httpx.Response(500), httpx.Response(500), httpx.Response(200, json={"ok": True})]

    def handler(request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    sleeps: list[float] = []
    connector = _make_connector(handler, cache_dir=tmp_path, sleeps=sleeps)
    result = connector.get_json("/v1/flaky")

    assert result.data == {"ok": True}
    assert len(sleeps) == 2  # zwei Wartezeiten vor den beiden Wiederholungen


def test_erschoepfte_retries_werfen_letzten_fehler(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorHTTPError):
        connector.get_json("/v1/immer-kaputt")


def test_timeout_wird_bis_zum_limit_wiederholt_und_dann_geworfen(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorTimeoutError):
        connector.get_json("/v1/timeout")


def test_429_wird_als_rate_limit_fehler_gemeldet(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorRateLimitedError):
        connector.get_json("/v1/rate-limited")


def test_4xx_ausser_429_wird_sofort_geworfen_ohne_retry(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404, text="not found")

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorHTTPError) as excinfo:
        connector.get_json("/v1/missing")

    assert excinfo.value.status_code == 404
    assert len(calls) == 1  # kein Retry bei einem 4xx-Client-Fehler


def test_ungueltiges_json_wirft_validierungsfehler_ohne_retry(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, content=b"das ist kein JSON")

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorValidationError):
        connector.get_json("/v1/kaputtes-json")

    assert len(calls) == 1


def test_rate_limiter_wird_vor_jedem_aufruf_konsultiert(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"ok": True})

    acquire_calls = []

    class RecordingLimiter(RateLimiter):
        def acquire(self) -> None:
            acquire_calls.append(1)
            super().acquire()

    limiter = RecordingLimiter(100, 60.0, sleep=lambda s: None)
    connector = _make_connector(handler, cache_dir=tmp_path, rate_limiter=limiter)
    connector.get_json("/v1/data")

    assert len(acquire_calls) == 1


def test_secret_params_landen_im_request_aber_nicht_in_der_provenienz_url(tmp_path: Path) -> None:
    received_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        received_urls.append(str(request.url))
        return httpx.Response(200, json={"ok": True})

    connector = _make_connector(handler, cache_dir=tmp_path)
    result = connector.get_json(
        "/v1/quote", params={"symbol": "IBM"}, secret_params={"apikey": "GEHEIM123"}
    )

    # Die tatsächliche Anfrage enthält den API-Schlüssel:
    assert "apikey=GEHEIM123" in received_urls[0]
    # Die zurückgegebene/gespeicherte Provenienz-URL enthält ihn NICHT:
    assert "GEHEIM123" not in result.url
    assert "symbol=IBM" in result.url

    # Auch im Cache auf der Festplatte darf der Schlüssel nirgends im Klartext stehen:
    for cache_file in tmp_path.rglob("*.json"):
        assert "GEHEIM123" not in cache_file.read_text(encoding="utf-8")


def test_cache_wird_nicht_fuer_fehlgeschlagene_abrufe_geschrieben(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    connector = _make_connector(handler, cache_dir=tmp_path)
    with pytest.raises(ConnectorHTTPError):
        connector.get_json("/v1/immer-kaputt")

    cache = FileCache(tmp_path)
    from investment_analyzer.connectors.cache import cache_key_for

    key = cache_key_for(f"https://{ALLOWED_HOST}/v1/immer-kaputt", None)
    assert cache.get("test_connector", key) is None
