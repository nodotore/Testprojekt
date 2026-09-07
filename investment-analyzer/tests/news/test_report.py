from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from investment_analyzer.connectors.gdelt import GdeltArticle
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.news.ingest import ingest_gdelt_articles
from investment_analyzer.news.report import build_news_report


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'news-report-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _article(*, url: str, title: str, domain: str, seen_at: datetime) -> GdeltArticle:
    return GdeltArticle(
        url=url,
        title=title,
        domain=domain,
        language="German",
        source_country="Germany",
        seen_at=seen_at,
        fetched_at_utc=seen_at,
        source_url="https://api.gdeltproject.org/api/v2/doc/doc?query=Firma+E",
    )


def test_build_news_report_gruppiert_aehnliche_meldungen(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        articles = (
            _article(
                url="https://outlet-a.test/artikel-1",
                title="Firma E meldet Rekordumsatz im ersten Quartal",
                domain="outlet-a.test",
                seen_at=datetime(2026, 3, 1, 8, tzinfo=UTC),
            ),
            _article(
                url="https://outlet-b.test/artikel-2",
                title="Firma E meldet Rekordumsatz im ersten Quartal 2026",
                domain="outlet-b.test",
                seen_at=datetime(2026, 3, 1, 10, tzinfo=UTC),
            ),
            _article(
                url="https://outlet-c.test/artikel-3",
                title="Firma E kündigt Aktienrückkauf an",
                domain="outlet-c.test",
                seen_at=datetime(2026, 2, 15, tzinfo=UTC),
            ),
        )
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()

        report = build_news_report(session, entity)

    assert report.entity_id == entity.id
    assert report.total_items == 3
    assert report.items_without_published_date == 0
    assert len(report.clusters) == 2

    multi_source_clusters = [c for c in report.clusters if c.is_multi_source]
    assert len(multi_source_clusters) == 1
    assert multi_source_clusters[0].item_count == 2


def test_build_news_report_ohne_daten_liefert_leeren_bericht(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma Ohne News", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000002")]
        )
        session.flush()
        report = build_news_report(session, entity)

    assert report.total_items == 0
    assert report.clusters == ()
    assert report.items_without_published_date == 0


def test_build_news_report_zaehlt_fehlende_daten(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma E", identifiers=[IdentifierSpec(IdentifierType.CIK, "0000000001")]
        )
        session.flush()

        article = GdeltArticle(
            url="https://outlet-a.test/artikel-ohne-datum",
            title="Meldung ohne Datum",
            domain="outlet-a.test",
            language=None,
            source_country=None,
            seen_at=None,
            fetched_at_utc=datetime(2026, 3, 1, tzinfo=UTC),
            source_url="https://api.gdeltproject.org/api/v2/doc/doc?query=Firma+E",
        )
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=(article,))
        session.commit()

        report = build_news_report(session, entity)

    assert report.total_items == 1
    assert report.items_without_published_date == 1
