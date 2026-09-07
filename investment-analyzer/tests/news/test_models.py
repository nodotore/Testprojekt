from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.news.models import NewsEventType, NewsItem, NewsSourceCategory


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'news-model-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_news_item_kann_gespeichert_und_gelesen_werden(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        item = NewsItem(
            entity_id=entity.id,
            source_id=sources["gdelt"].id,
            title="Firma E meldet Rekordumsatz",
            url="https://example-news.test/artikel-1",
            domain="example-news.test",
            published_at=None,
            language="de",
            summary_text="Kurzfassung.",
            source_category=NewsSourceCategory.UNABHAENGIGER_BERICHT,
            event_type=NewsEventType.EARNINGS,
            content_hash="abc123",
        )
        session.add(item)
        session.commit()

    with session_factory() as session:
        rows = session.scalars(select(NewsItem)).all()
    assert len(rows) == 1
    assert rows[0].title == "Firma E meldet Rekordumsatz"
    assert rows[0].source_category == NewsSourceCategory.UNABHAENGIGER_BERICHT


def test_gleicher_source_und_content_hash_wird_abgelehnt(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        def _make_item() -> NewsItem:
            return NewsItem(
                entity_id=entity.id,
                source_id=sources["gdelt"].id,
                title="Titel",
                url="https://example-news.test/artikel-1",
                domain="example-news.test",
                published_at=None,
                language=None,
                summary_text=None,
                source_category=NewsSourceCategory.UNABHAENGIGER_BERICHT,
                event_type=NewsEventType.SONSTIGES,
                content_hash="duplicate-hash",
            )

        session.add(_make_item())
        session.commit()

        session.add(_make_item())
        with pytest.raises(IntegrityError):
            session.commit()
