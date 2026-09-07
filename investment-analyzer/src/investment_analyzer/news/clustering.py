"""Deterministisches Ereignis-Clustering (Auftrag §6 „Nachrichten": „mehrere
Berichte über dasselbe Ereignis zu einem Cluster verbinden").

Reine Funktionen ohne Datenbankzugriff — analog zum Muster in
``valuation/``/``scoring/`` (DB-Orchestrierung getrennt von der
eigentlichen Logik, siehe ``news/report.py``). Clustering-Kriterium:
gleicher Ereignistyp + zeitliche Nähe + Titel-Ähnlichkeit
(``difflib.SequenceMatcher``, Standardbibliothek) — kein Sprachmodell,
keine Embeddings (Auftrag §8a-Analogie: deterministisch, nachvollziehbar).

Dies ist eine grobe lexikalische Heuristik, kein semantisches
Verständnis: Zwei Meldungen mit sehr unterschiedlichem Wortlaut über
dasselbe Ereignis werden ggf. NICHT zusammengeführt — ein bewusst
konservativer Fehler in Richtung „zu viele Cluster" statt fälschlich
zusammengeführter, inhaltlich verschiedener Ereignisse (Auftrag §11).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

DEFAULT_TITLE_SIMILARITY_THRESHOLD = 0.6
DEFAULT_MAX_DAY_GAP = 2


@dataclass(frozen=True)
class ClusterableNewsItem:
    """Minimale, DB-unabhängige Sicht auf einen ``NewsItem`` fürs Clustering."""

    news_item_id: str
    title: str
    url: str
    domain: str | None
    published_at: datetime | None
    source_category: str
    event_type: str


@dataclass(frozen=True)
class NewsCluster:
    event_type: str
    items: tuple[ClusterableNewsItem, ...]

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def domains(self) -> frozenset[str]:
        return frozenset(item.domain for item in self.items if item.domain)

    @property
    def is_multi_source(self) -> bool:
        """Mehrere unabhängige Domains berichten über dasselbe Ereignis."""

        return len(self.domains) > 1

    @property
    def earliest_published_at(self) -> datetime | None:
        dated = [item.published_at for item in self.items if item.published_at is not None]
        return min(dated) if dated else None

    @property
    def latest_published_at(self) -> datetime | None:
        dated = [item.published_at for item in self.items if item.published_at is not None]
        return max(dated) if dated else None

    @property
    def representative_title(self) -> str:
        return self.items[0].title


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _within_day_gap(a: datetime | None, b: datetime | None, *, max_day_gap: int) -> bool:
    """Fehlendes Datum blockiert das Clustering NICHT.

    Ein fehlendes Datum ist eine fehlende Angabe, kein Ausschlussgrund
    für ein sonst (Ereignistyp + Titel-Ähnlichkeit) passendes Ereignis
    (Auftrag §11: keine Information wird durch eine Annahme ersetzt, aber
    ihr Fehlen darf auch nicht wie ein Widerspruch behandelt werden).
    """

    if a is None or b is None:
        return True
    return abs(a - b) <= timedelta(days=max_day_gap)


def cluster_news_items(
    items: Sequence[ClusterableNewsItem],
    *,
    title_similarity_threshold: float = DEFAULT_TITLE_SIMILARITY_THRESHOLD,
    max_day_gap: int = DEFAULT_MAX_DAY_GAP,
) -> list[NewsCluster]:
    """Greedy-Clustering: gleicher Ereignistyp + zeitliche Nähe + Titel-Ähnlichkeit.

    Deterministisch bei fester Eingabereihenfolge: Elemente werden nach
    Datum sortiert (fehlendes Datum zuletzt) verarbeitet; für jedes
    Element wird der ERSTE passende bestehende Cluster gewählt (nicht der
    ähnlichste) — einfach und nachvollziehbar, auf Kosten einer
    theoretisch optimaleren Zuordnung bei mehreren gleichzeitig
    passenden Clustern.
    """

    sorted_items = sorted(
        items, key=lambda item: (item.published_at is None, item.published_at or datetime.min)
    )

    clusters: list[list[ClusterableNewsItem]] = []
    for item in sorted_items:
        target: list[ClusterableNewsItem] | None = None
        for cluster in clusters:
            representative = cluster[0]
            if representative.event_type != item.event_type:
                continue
            if not _within_day_gap(
                representative.published_at, item.published_at, max_day_gap=max_day_gap
            ):
                continue
            if _title_similarity(representative.title, item.title) >= title_similarity_threshold:
                target = cluster
                break

        if target is None:
            clusters.append([item])
        else:
            target.append(item)

    return [
        NewsCluster(event_type=cluster[0].event_type, items=tuple(cluster)) for cluster in clusters
    ]
