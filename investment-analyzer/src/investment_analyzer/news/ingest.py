"""Ingestion: Connector-Rohdaten → provenienzbehaftete ``NewsItem``-Zeilen (Auftrag §5).

Analog zu ``normalization/ingest.py`` für Fundamentaldaten: jede Funktion
hier nimmt das typisierte Ergebnis eines Connectors (``GdeltArticle``,
``RssItem``) entgegen und erzeugt daraus ``NewsItem``-Zeilen mit
vollständiger Provenienz (Quelle, Artikel-URL, Abrufzeitpunkt UTC, Hash,
regelbasierte Klassifikation). Idempotent: ein bei einem früheren Abruf
bereits gespeicherter Treffer (gleiche Quelle + normalisierte URL) wird
nicht erneut eingefügt (eindeutig über ``NewsItem.content_hash`` je
``source_id``, siehe ``news/models.py``).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.connectors.gdelt import GdeltArticle
from investment_analyzer.connectors.ir_rss import RssItem
from investment_analyzer.connectors.models import Source
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.news.classification import classify_event_type, classify_source_category
from investment_analyzer.news.models import NewsItem
from investment_analyzer.news.sanitize import sanitize_html_to_text

#: Tracking-Parameter, die dieselbe Meldung unter unterschiedlichen URLs
#: erscheinen lassen würden — werden vor dem Dedup-Hashing entfernt.
_TRACKING_QUERY_KEYS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
)


def _normalize_url(url: str) -> str:
    """Entfernt Fragment und bekannte Tracking-Parameter für den Dedup-Hash.

    Bewusst konservativ: nur ein kleiner, dokumentierter Satz an
    Tracking-Parametern wird entfernt, keine generische Query-String-
    Bereinigung (die könnte legitim unterschiedliche Artikel unter
    derselben Basis-URL fälschlich zusammenführen).
    """

    parts = urlsplit(url)
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_QUERY_KEYS
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(filtered_query), "")
    )


def _content_hash(url: str) -> str:
    return hashlib.sha256(_normalize_url(url).encode("utf-8")).hexdigest()


def _existing_hashes(session: Session, source: Source) -> set[str]:
    return set(
        session.scalars(select(NewsItem.content_hash).where(NewsItem.source_id == source.id)).all()
    )


def ingest_gdelt_articles(
    session: Session, *, entity: Entity, source: Source, articles: tuple[GdeltArticle, ...]
) -> list[NewsItem]:
    """Wandelt GDELT-Suchtreffer in ``NewsItem``-Zeilen um (idempotent).

    GDELT liefert im ``artlist``-Modus keinen Artikel-Ausschnitt —
    ``summary_text`` bleibt entsprechend ``None`` statt eines erfundenen
    Platzhaltertexts (Auftrag §11).
    """

    existing_hashes = _existing_hashes(session, source)

    created: list[NewsItem] = []
    for article in articles:
        content_hash = _content_hash(article.url)
        if content_hash in existing_hashes:
            continue

        item = NewsItem(
            entity_id=entity.id,
            source_id=source.id,
            title=article.title,
            url=article.url,
            domain=article.domain,
            published_at=article.seen_at,
            retrieved_at_utc=article.fetched_at_utc,
            language=article.language,
            summary_text=None,
            source_category=classify_source_category(source_key=source.key, domain=article.domain),
            event_type=classify_event_type(article.title),
            content_hash=content_hash,
        )
        session.add(item)
        created.append(item)
        existing_hashes.add(content_hash)

    return created


def ingest_ir_rss_items(
    session: Session,
    *,
    entity: Entity,
    source: Source,
    items: tuple[RssItem, ...],
    retrieved_at_utc: datetime,
) -> list[NewsItem]:
    """Wandelt IR-RSS-Feed-Einträge in ``NewsItem``-Zeilen um (idempotent).

    ``retrieved_at_utc`` kommt vom Aufrufer (aus ``RssFeed.fetched_at_utc``),
    da ein einzelner ``RssItem`` selbst keinen Abrufzeitpunkt trägt.
    """

    existing_hashes = _existing_hashes(session, source)

    created: list[NewsItem] = []
    for rss_item in items:
        content_hash = _content_hash(rss_item.url)
        if content_hash in existing_hashes:
            continue

        item_domain = urlsplit(rss_item.url).hostname
        summary_text = sanitize_html_to_text(rss_item.summary_html)

        item = NewsItem(
            entity_id=entity.id,
            source_id=source.id,
            title=rss_item.title,
            url=rss_item.url,
            domain=item_domain,
            published_at=rss_item.published_at,
            retrieved_at_utc=retrieved_at_utc,
            language=None,
            summary_text=summary_text,
            source_category=classify_source_category(source_key=source.key, domain=item_domain),
            event_type=classify_event_type(rss_item.title, summary_text),
            content_hash=content_hash,
        )
        session.add(item)
        created.append(item)
        existing_hashes.add(content_hash)

    return created
