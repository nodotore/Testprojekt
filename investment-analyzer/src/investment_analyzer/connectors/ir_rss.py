"""IR-RSS-Connector (Unternehmens-Pressemitteilungen, Auftrag §3 Stufe 2/5-6, Milestone 5).

Investor-Relations-/Pressemitteilungs-RSS-Feeds sind laut
``DATA_SOURCES.md`` „global, uneinheitlich" — jedes Unternehmen betreibt
(falls überhaupt) seinen eigenen Feed unter seinem eigenen Host. Anders
als bei den übrigen Connectoren gibt es daher keine feste
``ConnectorConfig`` für „die" Quelle: Jede Instanz dieses Connectors ist
an genau eine konkrete Feed-URL gebunden; die Host-Allowlist wird dafür
zur Laufzeit aus dieser URL abgeleitet. Der SSRF-/DNS-Rebinding-Schutz
(``connectors/ssrf.py``) bleibt davon unabhängig vollständig aktiv —
auch ein zur Laufzeit „erlaubter" Host wird abgelehnt, sobald er auf
eine private/loopback-Adresse auflöst.

Welche Feed-URL zu welcher ``Entity`` gehört, ist NICHT Teil dieses
Connectors — das ist eine noch offene Frage (siehe ``NEXT_STEPS.md``),
da es keine verlässliche automatisierte Feed-Erkennung ohne zusätzliche
Quelle gibt. Dieser Connector liefert nur den robusten Abruf- und
Parse-Mechanismus für eine gegebene URL.

Unterstützt werden RSS 2.0 (``<rss><channel><item>``) und Atom
(``<feed><entry>``) — die beiden in der Praxis nahezu ausschließlich
verwendeten Formate für IR-Feeds. Der Feed-Inhalt (insbesondere
``description``/``summary``) ist unbereinigtes HTML aus einer externen
Quelle und wird als nicht vertrauenswürdig behandelt (Auftrag §12) —
die Bereinigung erfolgt in ``news/sanitize.py``, nicht hier.

**Sicherheitshinweis (Auftrag §12, Milestone-8-Security-Review):** Das
XML selbst kommt ebenfalls von einer nicht vertrauenswürdigen externen
Quelle. Die Stdlib ``xml.etree.ElementTree`` ist laut Python-
Dokumentation NICHT gegen böswillig konstruiertes XML gehärtet
(insbesondere „Billion Laughs"/Entity-Expansion-Angriffe — eine
wenige Bytes große Payload kann beim Parsen mehrere Gigabyte Speicher
belegen; die HTTP-Größenobergrenze aus ``connectors/base.py`` schützt
davor NICHT, da der Angriff erst beim Parsen entsteht, nicht beim
Download). Dieses Modul verwendet daher ``defusedxml`` statt der
Stdlib — Entity-Definitionen/-Expansion werden dort grundsätzlich
abgelehnt (``DefusedXmlException``) statt verarbeitet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from investment_analyzer.connectors.base import Connector, ConnectorConfig
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.ssrf import Resolver

IR_RSS_LICENSE_NOTE = (
    "Unternehmens-eigene Investor-Relations-/Pressemitteilungs-RSS-Feeds — "
    "öffentlich abrufbar, Fair Use (DATA_SOURCES.md). Je Emittent ein eigener "
    "Host; SSRF-Schutz (private/loopback-Ziele) bleibt unabhängig von der "
    "laufzeit-spezifischen Allowlist aktiv."
)

#: IR-Feeds ändern sich selten (typisch: einige Meldungen/Monat) — 30 Minuten
#: TTL vermeidet unnötige Anfragen ohne relevante Aktualität zu verlieren.
DEFAULT_CACHE_TTL_SECONDS = 30 * 60

#: Kein dokumentiertes Rate Limit einzelner IR-Feeds bekannt — konservativer
#: Standardwert zur Schonung fremder Infrastruktur (Fair Use, Auftrag §4).
DEFAULT_MAX_CALLS_PER_MINUTE = 30

_ATOM_NS = "{http://www.w3.org/2005/Atom}"


def build_config(feed_url: str, *, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> ConnectorConfig:
    host = (urlsplit(feed_url).hostname or "").lower()
    if not host:
        raise ValueError(f"feed_url {feed_url!r} enthält keinen gültigen Hostnamen.")

    return ConnectorConfig(
        key=f"ir_rss:{host}",
        display_name=f"IR-RSS ({host})",
        base_url=feed_url,
        allowed_hosts=frozenset({host}),
        license_note=IR_RSS_LICENSE_NOTE,
        cache_ttl_seconds=cache_ttl_seconds,
    )


@dataclass(frozen=True)
class RssItem:
    title: str
    url: str
    published_at: datetime | None
    summary_html: str | None


@dataclass(frozen=True)
class RssFeed:
    items: tuple[RssItem, ...]
    fetched_at_utc: datetime
    source_url: str


def _local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_rfc822_date(raw: str | None) -> datetime | None:
    """RSS-``pubDate`` (RFC 822, z. B. ``"Mon, 02 Jan 2026 15:04:05 GMT"``)."""

    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        # Unbekanntes/kaputtes Datumsformat wird NICHT geraten (Auftrag §11).
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_iso_date(raw: str | None) -> datetime | None:
    """Atom-``published``/``updated`` (ISO 8601, z. B. ``"2026-01-02T15:04:05Z"``)."""

    if not raw:
        return None
    normalized = raw.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_feed(raw_xml: str) -> tuple[RssItem, ...]:
    """Parst RSS 2.0 oder Atom zu einer einheitlichen Liste von ``RssItem``.

    Einträge ohne Link/URL werden übersprungen (ohne URL keine belastbare
    Provenienz, Auftrag §5). Ein unbekanntes Root-Element oder kaputtes XML
    löst ``ConnectorValidationError`` aus statt eines stillen Leerergebnisses.
    """

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise ConnectorValidationError(f"Feed ist kein gültiges XML: {exc}") from exc
    except DefusedXmlException as exc:
        # z. B. EntitiesForbidden ("Billion Laughs") — kein ParseError,
        # sondern eine eigene defusedxml-Exception-Hierarchie.
        raise ConnectorValidationError(
            f"Feed enthält nicht erlaubte XML-Konstrukte (z. B. Entity-Definitionen): {exc}"
        ) from exc

    root_tag = _local_tag(root.tag)
    items: list[RssItem] = []

    if root_tag == "rss":
        channel = root.find("channel")
        if channel is None:
            raise ConnectorValidationError("RSS-Feed ohne <channel>-Element.")
        for item in channel.findall("item"):
            link = (item.findtext("link") or "").strip()
            if not link:
                continue
            title = (item.findtext("title") or "").strip()
            items.append(
                RssItem(
                    title=title or link,
                    url=link,
                    published_at=_parse_rfc822_date(item.findtext("pubDate")),
                    summary_html=item.findtext("description"),
                )
            )
    elif root_tag == "feed":
        for entry in root.findall(f"{_ATOM_NS}entry"):
            link_el = entry.find(f"{_ATOM_NS}link")
            link = (link_el.get("href") or "").strip() if link_el is not None else ""
            if not link:
                continue
            title = (entry.findtext(f"{_ATOM_NS}title") or "").strip()
            published_raw = entry.findtext(f"{_ATOM_NS}published") or entry.findtext(
                f"{_ATOM_NS}updated"
            )
            summary = entry.findtext(f"{_ATOM_NS}summary") or entry.findtext(f"{_ATOM_NS}content")
            items.append(
                RssItem(
                    title=title or link,
                    url=link,
                    published_at=_parse_iso_date(published_raw),
                    summary_html=summary,
                )
            )
    else:
        raise ConnectorValidationError(f"Unbekanntes Feed-Format (Root-Element {root.tag!r}).")

    return tuple(items)


class IrRssConnector(Connector):
    """Connector für genau einen IR-/Pressemitteilungs-RSS-Feed."""

    def __init__(
        self,
        feed_url: str,
        *,
        http_client: httpx.Client | None = None,
        cache: FileCache | None = None,
        rate_limiter: RateLimiter | None = None,
        ssrf_resolver: Resolver | None = None,
    ) -> None:
        config = build_config(feed_url)
        super().__init__(
            config,
            http_client=http_client,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter(DEFAULT_MAX_CALLS_PER_MINUTE, 60.0),
            ssrf_resolver=ssrf_resolver,
        )
        self._feed_url = feed_url

    def fetch_feed(self) -> RssFeed:
        result = self.get_text(self._feed_url)
        items = parse_feed(result.data)
        return RssFeed(items=items, fetched_at_utc=result.fetched_at_utc, source_url=result.url)
