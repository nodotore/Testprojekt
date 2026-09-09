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
from investment_analyzer.ui.news import _cluster_tabelle


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'ui-news-test.db'}")
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


def test_cluster_tabelle_enthaelt_alle_meldungen_mit_quelle(tmp_path: Path) -> None:
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
        )
        ingest_gdelt_articles(session, entity=entity, source=sources["gdelt"], articles=articles)
        session.commit()

        report = build_news_report(session, entity)

    assert len(report.clusters) == 1
    cluster = report.clusters[0]
    assert cluster.is_multi_source

    df = _cluster_tabelle(cluster)
    assert len(df) == 2
    assert set(df["Domain"]) == {"outlet-a.test", "outlet-b.test"}
    assert "https://outlet-a.test/artikel-1" in list(df["Quelle"])
