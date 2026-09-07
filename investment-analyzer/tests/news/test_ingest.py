from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from investment_analyzer.connectors.gdelt import GdeltArticle
from investment_analyzer.connectors.ir_rss import RssItem
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.news.ingest import ingest_gdelt_articles, ingest_ir_rss_items
from investment_analyzer.news.models import NewsEventType, NewsItem, NewsSourceCategory


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'news-ingest-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _gdelt_article(*, url: str, title: str, domain: str = "example-news.test") -> GdeltArticle:
    return GdeltArticle(
        url=url,
        title=title,
        domain=domain,
        language="German",
        source_country="Germany",
        seen_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
        fetched_at_utc=datetime(2026, 3, 1, 12, 5, tzinfo=UTC),
        source_url="https://api.gdeltproject.org/api/v2/doc/doc?query=Firma+E",
    )


def test_ingest_gdelt_articles_erzeugt_klassifizierte_news_items(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        articles = (
            _gdelt_article(
                url="https://example-news.test/quartalszahlen",
                title="Firma E meldet starke Quartalszahlen",
            ),
        )
        created = ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()

    assert len(created) == 1
    item = created[0]
    assert item.source_category == NewsSourceCategory.UNABHAENGIGER_BERICHT
    assert item.event_type == NewsEventType.EARNINGS
    assert item.summary_text is None

    with session_factory() as session:
        rows = session.scalars(select(NewsItem)).all()
    assert len(rows) == 1


def test_ingest_gdelt_articles_ist_idempotent(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        articles = (_gdelt_article(url="https://example-news.test/artikel-1", title="Meldung"),)
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()

    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        articles = (_gdelt_article(url="https://example-news.test/artikel-1", title="Meldung"),)
        created = ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()

    assert created == []
    with session_factory() as session:
        rows = session.scalars(select(NewsItem)).all()
    assert len(rows) == 1


def test_tracking_parameter_werden_beim_dedup_ignoriert(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        first = (_gdelt_article(url="https://example-news.test/artikel-1?utm_source=twitter", title="Meldung"),)
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=first)
        session.commit()

    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        second = (_gdelt_article(url="https://example-news.test/artikel-1?utm_source=linkedin", title="Meldung"),)
        created = ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=second)
        session.commit()

    assert created == []  # dieselbe Meldung, nur andere Tracking-Parameter


def test_ingest_ir_rss_items_ist_immer_unternehmensmeldung(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        items = (
            RssItem(
                title="Firma E kündigt Dividende an",
                url="https://ir.firma-e.test/news/dividende",
                published_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                summary_html="<p>Firma E zahlt eine Dividende von 1,00 EUR je Aktie.</p>",
            ),
        )
        created = ingest_ir_rss_items(
            session,
            entity=entity,
            source=sources["ir_rss"],
            items=items,
            retrieved_at_utc=datetime(2026, 3, 1, 9, 5, tzinfo=UTC),
        )
        session.commit()

    assert len(created) == 1
    item = created[0]
    assert item.source_category == NewsSourceCategory.UNTERNEHMENSMELDUNG
    assert item.event_type == NewsEventType.CAPITAL_MARKETS
    assert item.domain == "ir.firma-e.test"
    assert item.summary_text == "Firma E zahlt eine Dividende von 1,00 EUR je Aktie."


def test_ingest_ir_rss_items_ist_idempotent(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    items = (
        RssItem(
            title="Meldung",
            url="https://ir.firma-e.test/news/meldung",
            published_at=None,
            summary_html=None,
        ),
    )
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()
        ingest_ir_rss_items(
            session,
            entity=entity,
            source=sources["ir_rss"],
            items=items,
            retrieved_at_utc=datetime(2026, 3, 1, 9, 5, tzinfo=UTC),
        )
        session.commit()

    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        created = ingest_ir_rss_items(
            session,
            entity=entity,
            source=sources["ir_rss"],
            items=items,
            retrieved_at_utc=datetime(2026, 3, 1, 9, 5, tzinfo=UTC),
        )
        session.commit()

    assert created == []
    with session_factory() as session:
        rows = session.scalars(select(NewsItem)).all()
    assert len(rows) == 1
