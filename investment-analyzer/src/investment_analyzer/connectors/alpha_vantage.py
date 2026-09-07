"""Alpha-Vantage-Connector (Marktdaten, Kostenlos-Paket — Free Tier).

Kostenlose Marktdaten-API mit engen Rate Limits (Free Tier: 5 Anfragen
pro Minute, siehe ``DATA_SOURCES.md``). Besonderheit dieser API: Rate-
Limit- und Fehlermeldungen kommen NICHT als HTTP-Fehlerstatus, sondern
als HTTP 200 mit einem ``"Note"``/``"Information"``/``"Error Message"``-
Feld im JSON-Body. Das generische Connector-Grundgerüst (``base.py``)
prüft nur den HTTP-Status — dieser Connector validiert den
Antwortinhalt daher zusätzlich selbst (Auftrag §4: „Datenvalidierung").

Der API-Schlüssel wird ausschließlich als ``secret_params`` an
``Connector.get_json`` übergeben und landet dadurch nie in der
gespeicherten Provenienz-URL, im Cache oder in Logs (siehe ``base.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from investment_analyzer.connectors.base import Connector, ConnectorConfig
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import (
    ConnectorRateLimitedError,
    ConnectorValidationError,
)
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.ssrf import Resolver

ALPHA_VANTAGE_LICENSE_NOTE = (
    "Offizielle API, Nutzung gemäß Alpha-Vantage-Nutzungsbedingungen (Free Tier). "
    "Kein Redistributionsverbot für Eigenanwendung. Rate Limit Free Tier: "
    "5 Anfragen/Minute, 25–500 Anfragen/Tag."
)

ALLOWED_HOSTS = frozenset({"www.alphavantage.co"})
BASE_URL = "https://www.alphavantage.co"

#: Free-Tier-Limit (DATA_SOURCES.md). Bei bezahltem Tarif per rate_limiter-Parameter überschreibbar.
FREE_TIER_MAX_CALLS_PER_MINUTE = 5

#: Marktdaten sind naturgemäß kurzlebig; 15 Minuten TTL vermeidet unnötige
#: Anfragen gegen das enge Free-Tier-Limit, ohne "veraltet wirkende aktuelle" Daten zu riskieren
#: (die Oberfläche zeigt ohnehin immer fetched_at_utc/Datenalter an, Auftrag §10).
DEFAULT_CACHE_TTL_SECONDS = 15 * 60


def build_config(*, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> ConnectorConfig:
    return ConnectorConfig(
        key="alpha_vantage",
        display_name="Alpha Vantage",
        base_url=BASE_URL,
        allowed_hosts=ALLOWED_HOSTS,
        license_note=ALPHA_VANTAGE_LICENSE_NOTE,
        cache_ttl_seconds=cache_ttl_seconds,
    )


@dataclass(frozen=True)
class AlphaVantageQuote:
    symbol: str
    price: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: str
    volume: int
    latest_trading_day: date
    fetched_at_utc: datetime
    source_url: str


class AlphaVantageConnector(Connector):
    """Connector für Alpha Vantage (aktuell: ``GLOBAL_QUOTE``, Kurs-Snapshot)."""

    def __init__(
        self,
        *,
        api_key: str,
        http_client: httpx.Client | None = None,
        cache: FileCache | None = None,
        rate_limiter: RateLimiter | None = None,
        ssrf_resolver: Resolver | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key darf nicht leer sein.")
        self._api_key = api_key
        config = build_config()
        super().__init__(
            config,
            http_client=http_client,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter(FREE_TIER_MAX_CALLS_PER_MINUTE, 60.0),
            ssrf_resolver=ssrf_resolver,
        )

    def get_quote(self, symbol: str) -> AlphaVantageQuote:
        """Aktueller Kurs-Snapshot (``GLOBAL_QUOTE``) für ein Symbol."""

        result = self.get_json(
            "/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol},
            secret_params={"apikey": self._api_key},
        )
        data = result.data
        self._raise_if_embedded_error(data, symbol=symbol)

        try:
            quote = data["Global Quote"]
            if not quote:
                raise ConnectorValidationError(
                    f"Alpha Vantage lieferte für Symbol {symbol!r} kein Kursobjekt "
                    "(unbekanntes Symbol oder leere Antwort)."
                )
            return AlphaVantageQuote(
                symbol=quote["01. symbol"],
                price=Decimal(quote["05. price"]),
                previous_close=Decimal(quote["08. previous close"]),
                change=Decimal(quote["09. change"]),
                change_percent=quote["10. change percent"],
                volume=int(quote["06. volume"]),
                latest_trading_day=date.fromisoformat(quote["07. latest trading day"]),
                fetched_at_utc=result.fetched_at_utc,
                source_url=result.url,
            )
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ConnectorValidationError(
                f"Unerwartetes GLOBAL_QUOTE-Format für Symbol {symbol!r}: {exc}"
            ) from exc

    @staticmethod
    def _raise_if_embedded_error(data: Any, *, symbol: str) -> None:
        if not isinstance(data, dict):
            raise ConnectorValidationError(
                f"Unerwartete Alpha-Vantage-Antwort für Symbol {symbol!r} (kein JSON-Objekt)."
            )
        if "Error Message" in data:
            raise ConnectorValidationError(
                f"Alpha Vantage meldet einen Fehler für Symbol {symbol!r}: {data['Error Message']}"
            )
        note = data.get("Note") or data.get("Information")
        if note:
            raise ConnectorRateLimitedError(f"Alpha Vantage Rate-Limit/Hinweis: {note}")
