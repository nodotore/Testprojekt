"""GDELT-Connector (Nachrichten-Primärquelle, Auftrag §3 Stufe 5/6, Milestone 5).

Öffentliche, kostenlose Volltextsuche über die GDELT-DOC-2.0-API
(``https://api.gdeltproject.org/api/v2/doc/doc``). Kein API-Schlüssel
nötig. Liefert je Treffer Titel, Artikel-URL, Herkunftsdomain, Sprache
und Zeitstempel — bewusst KEINEN Artikel-Volltext (GDELT liefert diesen
ohnehin nicht; Volltextabruf einzelner Artikel ist nicht Teil dieses
Connectors, siehe ``news/sanitize.py`` für den Umgang mit dem, was wir
tatsächlich erhalten).

Wie bei Alpha Vantage (siehe ``alpha_vantage.py``) ist der HTTP-Status
allein keine verlässliche Fehlerquelle: eine unzulässige/leere Anfrage
liefert teils HTTP 200 mit einer HTML-Fehlerseite statt JSON — das
generische ``get_json()`` wirft in diesem Fall bereits
``ConnectorValidationError``, da die Antwort nicht als JSON parsbar ist
(Auftrag §4: „Fail loud, nicht silent").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from investment_analyzer.connectors.base import Connector, ConnectorConfig
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.ssrf import Resolver

GDELT_LICENSE_NOTE = (
    "GDELT Project — öffentlich, akademisch/frei nutzbar mit Attribution "
    "(https://www.gdeltproject.org/about.html#termsofuse). Großzügige, aber "
    "nicht dokumentiert-feste Rate Limits — konservativ gedrosselt (siehe "
    "DATA_SOURCES.md)."
)

ALLOWED_HOSTS = frozenset({"api.gdeltproject.org"})
BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

#: GDELT nennt keine festen Rate Limits (DATA_SOURCES.md: "großzügig, aber
#: Volumen beachten") — konservativer Standardwert, um die Quelle nicht zu
#: überlasten und Fair-Use zu wahren.
DEFAULT_MAX_CALLS_PER_MINUTE = 20

#: Nachrichtenergebnisse ändern sich laufend; kurze TTL vermeidet dennoch
#: redundante Anfragen bei mehreren Analysen kurz hintereinander.
DEFAULT_CACHE_TTL_SECONDS = 15 * 60

DEFAULT_MAX_RECORDS = 75


def build_config(*, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> ConnectorConfig:
    return ConnectorConfig(
        key="gdelt",
        display_name="GDELT Project",
        base_url=BASE_URL,
        allowed_hosts=ALLOWED_HOSTS,
        license_note=GDELT_LICENSE_NOTE,
        cache_ttl_seconds=cache_ttl_seconds,
    )


@dataclass(frozen=True)
class GdeltArticle:
    url: str
    title: str
    domain: str | None
    language: str | None
    source_country: str | None
    seen_at: datetime | None
    fetched_at_utc: datetime
    source_url: str


@dataclass(frozen=True)
class GdeltSearchResult:
    articles: tuple[GdeltArticle, ...]
    fetched_at_utc: datetime
    source_url: str


def _parse_seendate(raw: str | None) -> datetime | None:
    """GDELT liefert ``seendate`` als ``YYYYMMDDThhmmssZ`` (UTC)."""

    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError:
        # Unbekanntes Datumsformat wird NICHT geraten (Auftrag §11) — lieber
        # ein fehlendes Datum als ein falsches.
        return None


class GdeltConnector(Connector):
    """Connector für die GDELT-DOC-2.0-Volltextsuche."""

    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
        cache: FileCache | None = None,
        rate_limiter: RateLimiter | None = None,
        ssrf_resolver: Resolver | None = None,
    ) -> None:
        config = build_config()
        super().__init__(
            config,
            http_client=http_client,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter(DEFAULT_MAX_CALLS_PER_MINUTE, 60.0),
            ssrf_resolver=ssrf_resolver,
        )

    def search_articles(
        self,
        query: str,
        *,
        max_records: int = DEFAULT_MAX_RECORDS,
        timespan: str | None = None,
    ) -> GdeltSearchResult:
        """Volltextsuche nach ``query`` (z. B. Firmenname oder ``"Firmenname" ticker``).

        ``timespan`` folgt der GDELT-Syntax (z. B. ``"7d"``, ``"3m"``); ohne
        Angabe durchsucht GDELT den vollen verfügbaren Zeitraum (i. d. R.
        ca. die letzten Jahre, siehe GDELT-Dokumentation).
        """

        if not query.strip():
            raise ValueError("query darf nicht leer sein.")

        params: dict[str, Any] = {
            "query": query,
            "mode": "artlist",
            "maxrecords": str(max_records),
            "sort": "datedesc",
            "format": "json",
        }
        if timespan:
            params["timespan"] = timespan

        result = self.get_json(BASE_URL, params=params)
        data = result.data

        if not isinstance(data, dict):
            raise ConnectorValidationError(
                f"Unerwartete GDELT-Antwort für query={query!r} (kein JSON-Objekt)."
            )

        raw_articles = data.get("articles", [])
        if not isinstance(raw_articles, list):
            raise ConnectorValidationError(
                f"Unerwartetes GDELT-Antwortformat für query={query!r}: 'articles' ist keine Liste."
            )

        try:
            articles = tuple(
                GdeltArticle(
                    url=article["url"],
                    title=article.get("title") or article["url"],
                    domain=article.get("domain"),
                    language=article.get("language"),
                    source_country=article.get("sourcecountry"),
                    seen_at=_parse_seendate(article.get("seendate")),
                    fetched_at_utc=result.fetched_at_utc,
                    source_url=result.url,
                )
                for article in raw_articles
                if isinstance(article, dict) and article.get("url")
            )
        except (KeyError, TypeError) as exc:
            raise ConnectorValidationError(
                f"Unerwartetes GDELT-Artikelformat für query={query!r}: {exc}"
            ) from exc

        return GdeltSearchResult(
            articles=articles, fetched_at_utc=result.fetched_at_utc, source_url=result.url
        )
