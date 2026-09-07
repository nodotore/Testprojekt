"""Orchestrierung: ``NewsItem``-Zeilen aus der DB → geclusterter Bericht (Auftrag §6 „Nachrichten").

Analog zu ``fundamentals/report.py``/``valuation/report.py``: liest
provenienzbehaftete ``NewsItem``-Zeilen, wendet die reine
Clustering-Funktion (``news/clustering.py``) an und liefert einen
typisierten, sofort UI-/Export-fähigen Bericht.

**Bewusste, dokumentierte Lücke (Milestone 5):** Auftrag §6 nennt für das
Nachrichtenmodul auch eine „KI-Zusammenfassung mit Quellenverweis".
Diese Milestone liefert dafür die technische Grundlage — jeder
``NewsCluster`` referenziert jede zugrunde liegende Meldung zwingend über
``ClusterableNewsItem.url`` — ruft selbst aber KEIN Sprachmodell auf: in
dieser Entwicklungsumgebung ist weder eine Claude-API-Anbindung noch ein
dafür vorgesehener API-Schlüssel im ``SecretStore``-Rahmen vorhanden.
Eine künftige Zusammenfassungs-Integration (voraussichtlich UI-/
Reports-Schicht, Milestone 6+) MUSS jede Aussage an ``NewsCluster.items``
zurückbinden und den gesamten Eingabetext (Titel, ``summary_text``) als
nicht vertrauenswürdige Nutzdaten behandeln, nie als Anweisung (Auftrag
§12, siehe ``news/sanitize.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.news.clustering import ClusterableNewsItem, NewsCluster, cluster_news_items
from investment_analyzer.news.models import NewsItem

#: Ein unbegrenzter Bericht wäre bei aktiven Nachrichtenquellen praktisch
#: unhandhabbar groß und für eine Analyse auch nicht sinnvoll — begrenzt auf
#: die zuletzt bekannt gewordenen Meldungen.
DEFAULT_MAX_ITEMS = 200


@dataclass(frozen=True)
class NewsReport:
    entity_id: str
    generated_at: datetime
    clusters: tuple[NewsCluster, ...]
    total_items: int
    items_without_published_date: int


def _to_clusterable(item: NewsItem) -> ClusterableNewsItem:
    return ClusterableNewsItem(
        news_item_id=item.id,
        title=item.title,
        url=item.url,
        domain=item.domain,
        published_at=item.published_at,
        source_category=item.source_category,
        event_type=item.event_type,
    )


def build_news_report(
    session: Session, entity: Entity, *, max_items: int = DEFAULT_MAX_ITEMS
) -> NewsReport:
    """Liest die jüngsten ``NewsItem``-Zeilen einer Entity und clustert sie."""

    rows = session.scalars(
        select(NewsItem)
        .where(NewsItem.entity_id == entity.id)
        .order_by(NewsItem.published_at.desc())
        .limit(max_items)
    ).all()

    clusterable = [_to_clusterable(row) for row in rows]
    clusters = tuple(cluster_news_items(clusterable))

    return NewsReport(
        entity_id=entity.id,
        generated_at=utc_now(),
        clusters=clusters,
        total_items=len(rows),
        items_without_published_date=sum(1 for row in rows if row.published_at is None),
    )
