from __future__ import annotations

from datetime import UTC, datetime

from investment_analyzer.news.clustering import ClusterableNewsItem, cluster_news_items
from investment_analyzer.news.models import NewsEventType, NewsSourceCategory


def _item(
    *,
    news_item_id: str,
    title: str,
    domain: str | None = "example.test",
    published_at: datetime | None = datetime(2026, 3, 1, tzinfo=UTC),
    event_type: str = NewsEventType.EARNINGS,
    source_category: str = NewsSourceCategory.UNABHAENGIGER_BERICHT,
) -> ClusterableNewsItem:
    return ClusterableNewsItem(
        news_item_id=news_item_id,
        title=title,
        url=f"https://{domain or 'unknown.test'}/{news_item_id}",
        domain=domain,
        published_at=published_at,
        source_category=source_category,
        event_type=event_type,
    )


def test_aehnliche_titel_gleicher_tag_werden_geclustert() -> None:
    items = [
        _item(news_item_id="1", title="Firma E meldet Rekordumsatz im ersten Quartal"),
        _item(
            news_item_id="2",
            domain="another.test",
            title="Firma E meldet Rekordumsatz im ersten Quartal 2026",
        ),
    ]
    clusters = cluster_news_items(items)
    assert len(clusters) == 1
    assert clusters[0].item_count == 2
    assert clusters[0].is_multi_source is True


def test_unterschiedlicher_ereignistyp_wird_nicht_geclustert() -> None:
    items = [
        _item(news_item_id="1", title="Firma E meldet Rekordumsatz", event_type=NewsEventType.EARNINGS),
        _item(
            news_item_id="2",
            title="Firma E meldet Rekordumsatz",
            event_type=NewsEventType.MERGER_ACQUISITION,
        ),
    ]
    clusters = cluster_news_items(items)
    assert len(clusters) == 2


def test_voellig_unterschiedliche_titel_werden_nicht_geclustert() -> None:
    items = [
        _item(news_item_id="1", title="Firma E meldet Rekordumsatz"),
        _item(news_item_id="2", title="Wettbewerber kündigt neues Produkt an"),
    ]
    clusters = cluster_news_items(items)
    assert len(clusters) == 2


def test_zeitlich_zu_weit_auseinander_wird_nicht_geclustert() -> None:
    items = [
        _item(
            news_item_id="1",
            title="Firma E meldet Rekordumsatz im ersten Quartal",
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        _item(
            news_item_id="2",
            title="Firma E meldet Rekordumsatz im ersten Quartal 2026",
            published_at=datetime(2026, 3, 1, tzinfo=UTC),
        ),
    ]
    clusters = cluster_news_items(items, max_day_gap=2)
    assert len(clusters) == 2


def test_fehlendes_datum_blockiert_clustering_nicht() -> None:
    items = [
        _item(
            news_item_id="1",
            title="Firma E meldet Rekordumsatz im ersten Quartal",
            published_at=None,
        ),
        _item(
            news_item_id="2",
            title="Firma E meldet Rekordumsatz im ersten Quartal 2026",
            published_at=datetime(2026, 3, 1, tzinfo=UTC),
        ),
    ]
    clusters = cluster_news_items(items)
    assert len(clusters) == 1


def test_einzelnes_element_bildet_eigenen_cluster() -> None:
    clusters = cluster_news_items([_item(news_item_id="1", title="Alleinstehende Meldung")])
    assert len(clusters) == 1
    assert clusters[0].item_count == 1
    assert clusters[0].is_multi_source is False


def test_leere_liste_liefert_keine_cluster() -> None:
    assert cluster_news_items([]) == []


def test_earliest_und_latest_published_at() -> None:
    items = [
        _item(
            news_item_id="1",
            title="Firma E meldet Rekordumsatz",
            published_at=datetime(2026, 3, 1, 8, tzinfo=UTC),
        ),
        _item(
            news_item_id="2",
            title="Firma E meldet Rekordumsatz 2026",
            published_at=datetime(2026, 3, 2, 10, tzinfo=UTC),
        ),
    ]
    cluster = cluster_news_items(items)[0]
    assert cluster.earliest_published_at == datetime(2026, 3, 1, 8, tzinfo=UTC)
    assert cluster.latest_published_at == datetime(2026, 3, 2, 10, tzinfo=UTC)


def test_similarity_threshold_ist_konfigurierbar() -> None:
    items = [
        _item(news_item_id="1", title="Firma E Umsatz steigt deutlich"),
        _item(news_item_id="2", title="Firma E Gewinn steigt leicht"),
    ]
    lockere_cluster = cluster_news_items(items, title_similarity_threshold=0.3)
    strenge_cluster = cluster_news_items(items, title_similarity_threshold=0.95)
    assert len(lockere_cluster) <= len(strenge_cluster)
