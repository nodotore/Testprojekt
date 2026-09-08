"""Gemeinsame Connector-Basisklasse (Auftrag §4).

Jeder Connector bekommt darüber: Timeout, Retry mit exponentiellem
Backoff, Rate Limiting, Cache (mit TTL, nie stillschweigend veraltet),
SSRF-Schutz mit URL-Allowlist und ein einheitliches Fehlerprotokoll.
Konkrete Connectoren (``sec_edgar.py``, ``alpha_vantage.py``) bauen auf
``Connector.get_json()`` auf und fügen nur noch die Endpunkt-spezifische
URL-Konstruktion und Antwort-Validierung hinzu.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from investment_analyzer.connectors.cache import CacheEntry, FileCache, cache_key_for
from investment_analyzer.connectors.errors import (
    ConnectorError,
    ConnectorHTTPError,
    ConnectorRateLimitedError,
    ConnectorTimeoutError,
    ConnectorValidationError,
)
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.ssrf import Resolver, assert_safe_url
from investment_analyzer.db.types import utc_now


@dataclass(frozen=True)
class ConnectorConfig:
    """Statische Metadaten eines Connectors — spiegelt eine Zeile aus ``DATA_SOURCES.md``."""

    key: str
    display_name: str
    base_url: str
    allowed_hosts: frozenset[str]
    license_note: str
    default_headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_base_seconds: float = 0.5
    cache_ttl_seconds: int = 3600
    #: Obergrenze für die Antwortgröße (Auftrag §12: „Downloadgrößen begrenzen").
    #: Verhindert, dass eine kompromittierte/böswillige Quelle (v. a. relevant
    #: bei IR-RSS, dessen Host je Emittent variiert) eine übergroße Antwort
    #: zur Verarbeitung/Speicherung zwingt. 10 MB ist großzügig genug für
    #: JSON-/XML-Antworten aller angebundenen Quellen.
    max_response_bytes: int = 10 * 1024 * 1024


@dataclass(frozen=True)
class FetchResult:
    """Ergebnis eines Connector-Abrufs inkl. Provenienz-relevanter Metadaten (Auftrag §5)."""

    data: Any
    url: str
    fetched_at_utc: datetime
    from_cache: bool
    status_code: int


class Connector:
    """Basisklasse für alle Datenquellen-Connectoren."""

    def __init__(
        self,
        config: ConnectorConfig,
        *,
        http_client: httpx.Client | None = None,
        cache: FileCache | None = None,
        rate_limiter: RateLimiter | None = None,
        ssrf_resolver: Resolver | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.config = config
        self._client = http_client or httpx.Client(timeout=config.timeout_seconds)
        self._owns_client = http_client is None
        self._cache = cache
        self._rate_limiter = rate_limiter
        self._ssrf_resolver = ssrf_resolver
        self._sleep = sleep
        self._clock = clock

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Connector:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _build_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("https://") or path_or_url.startswith("http://"):
            return path_or_url
        return self.config.base_url.rstrip("/") + "/" + path_or_url.lstrip("/")

    @staticmethod
    def _with_query(url: str, extra_params: dict[str, Any]) -> str:
        if not extra_params:
            return url
        parts = urlsplit(url)
        combined = [*parse_qsl(parts.query, keep_blank_values=True), *extra_params.items()]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(combined), parts.fragment))

    def get_json(
        self,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        secret_params: dict[str, Any] | None = None,
        cache_ttl_seconds: int | None = None,
    ) -> FetchResult:
        """Ruft JSON von ``path_or_url`` ab — mit Cache, Rate-Limit, Retry und SSRF-Schutz.

        ``params`` landet in der gespeicherten/zurückgegebenen URL (Provenienz,
        Auftrag §5). ``secret_params`` (z. B. API-Schlüssel) wird NUR an die
        tatsächliche HTTP-Anfrage angehängt und taucht niemals in
        ``FetchResult.url``, im Cache oder in Logs auf — API-Schlüssel dürfen
        nicht in der Provenienz-URL landen (Auftrag §12).

        Wirft eine Unterklasse von ``ConnectorError``, falls der Live-Abruf
        endgültig scheitert. Es gibt in diesem Fall KEINEN Fallback auf
        einen abgelaufenen Cache-Eintrag (Auftrag §4).
        """

        return self._get(
            path_or_url,
            params=params,
            secret_params=secret_params,
            cache_ttl_seconds=cache_ttl_seconds,
            parse=lambda response: response.json(),
        )

    def get_text(
        self,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        secret_params: dict[str, Any] | None = None,
        cache_ttl_seconds: int | None = None,
    ) -> FetchResult:
        """Wie ``get_json``, liefert aber den rohen Antworttext statt geparstem JSON.

        Für Quellen ohne JSON-API (z. B. RSS-/Atom-Feeds, ``news/``-Modul,
        Milestone 5). Dieselben Provenienz-, Cache-, Retry- und
        SSRF-Garantien gelten unverändert.
        """

        return self._get(
            path_or_url,
            params=params,
            secret_params=secret_params,
            cache_ttl_seconds=cache_ttl_seconds,
            parse=lambda response: response.text,
        )

    def _get(
        self,
        path_or_url: str,
        *,
        params: dict[str, Any] | None,
        secret_params: dict[str, Any] | None,
        cache_ttl_seconds: int | None,
        parse: Callable[[httpx.Response], Any],
    ) -> FetchResult:
        public_url = self._with_query(self._build_url(path_or_url), params or {})
        ttl = cache_ttl_seconds if cache_ttl_seconds is not None else self.config.cache_ttl_seconds
        # secret_params fließt nur in den Hash ein (Cache-Schlüssel), nie im Klartext gespeichert.
        cache_key = cache_key_for(public_url, secret_params)

        if self._cache is not None:
            cached = self._cache.get(self.config.key, cache_key)
            if cached is not None:
                return FetchResult(
                    data=cached.data,
                    url=public_url,
                    fetched_at_utc=cached.fetched_at_utc,
                    from_cache=True,
                    status_code=cached.status_code,
                )

        if self._ssrf_resolver is not None:
            assert_safe_url(public_url, self.config.allowed_hosts, resolver=self._ssrf_resolver)
        else:
            assert_safe_url(public_url, self.config.allowed_hosts)

        request_url = self._with_query(public_url, secret_params or {})
        data, status_code = self._request_with_retry(request_url, parse)
        fetched_at = self._clock()

        if self._cache is not None:
            self._cache.set(
                self.config.key,
                cache_key,
                CacheEntry(data=data, fetched_at_utc=fetched_at, ttl_seconds=ttl, status_code=status_code),
            )

        return FetchResult(
            data=data, url=public_url, fetched_at_utc=fetched_at, from_cache=False, status_code=status_code
        )

    def _request_with_retry(self, url: str, parse: Callable[[httpx.Response], Any]) -> tuple[Any, int]:
        last_error: ConnectorError | None = None

        for attempt in range(1, self.config.max_retries + 1):
            if self._rate_limiter is not None:
                self._rate_limiter.acquire()

            try:
                response = self._client.get(url, headers=self.config.default_headers)
            except httpx.TimeoutException as exc:
                last_error = ConnectorTimeoutError(f"Timeout bei {url}: {exc}")
            except httpx.TransportError as exc:
                last_error = ConnectorError(f"Transportfehler bei {url}: {exc}")
            else:
                content_length = len(response.content)
                if content_length > self.config.max_response_bytes:
                    # Fail loud statt eine übergroße Antwort zu verarbeiten/zu
                    # cachen (Auftrag §12) — kein Retry, da eine Wiederholung
                    # dieselbe übergroße Antwort nicht kleiner macht.
                    raise ConnectorValidationError(
                        f"Antwort von {url} überschreitet die Größenobergrenze "
                        f"({content_length} > {self.config.max_response_bytes} Bytes) — "
                        "Verarbeitung abgelehnt."
                    )
                if response.status_code == 429:
                    last_error = ConnectorRateLimitedError(
                        f"Rate-Limit von {url} überschritten (HTTP 429)."
                    )
                elif response.status_code >= 500:
                    last_error = ConnectorHTTPError(response.status_code, f"Serverfehler bei {url}")
                elif response.status_code >= 400:
                    # 4xx außer 429 sind i. d. R. nicht durch Wiederholen behebbar.
                    raise ConnectorHTTPError(
                        response.status_code, f"Client-Fehler bei {url}: {response.text[:200]}"
                    )
                else:
                    try:
                        return parse(response), response.status_code
                    except ValueError as exc:
                        raise ConnectorValidationError(
                            f"Antwort von {url} konnte nicht verarbeitet werden: {exc}"
                        ) from exc

            if attempt < self.config.max_retries:
                backoff_seconds = self.config.backoff_base_seconds * (2 ** (attempt - 1))
                self._sleep(backoff_seconds)

        assert last_error is not None  # für mypy: die Schleife setzt last_error immer, bevor sie endet
        raise last_error
