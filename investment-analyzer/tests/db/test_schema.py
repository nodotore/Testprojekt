from __future__ import annotations

import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from investment_analyzer.audit.models import AuditEventType, AuditLogEntry
from investment_analyzer.connectors.models import Source
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, EntityIdentifier, IdentifierType
from investment_analyzer.normalization.models import DataPoint, ValueKind

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'test.db'}")
    create_all_tables(engine)
    yield create_session_factory(engine)
    engine.dispose()


def test_entity_und_identifier_roundtrip(session_factory) -> None:
    with session_factory() as session:
        entity = Entity(name="Beispiel AG", country="DE", primary_exchange="XETRA")
        entity.identifiers.append(
            EntityIdentifier(id_type=IdentifierType.ISIN, id_value="DE0001234567")
        )
        entity.identifiers.append(
            EntityIdentifier(
                id_type=IdentifierType.TICKER, id_value="BSP", exchange="XETRA"
            )
        )
        session.add(entity)
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        loaded = session.get(Entity, entity_id)
        assert loaded is not None
        assert loaded.name == "Beispiel AG"
        assert len(loaded.identifiers) == 2
        isin_values = {i.id_value for i in loaded.identifiers if i.id_type == IdentifierType.ISIN}
        assert isin_values == {"DE0001234567"}


def test_ticker_allein_ist_keine_eindeutige_entitaet(session_factory) -> None:
    """Zwei verschiedene Entities dürfen denselben Ticker an unterschiedlichen
    Börsen tragen — die Zuordnung MUSS über eine stabilere Kennung (hier ISIN)
    erfolgen, niemals allein über den Ticker (Auftrag §5)."""

    with session_factory() as session:
        e1 = Entity(name="Firma A (US)", country="US")
        e1.identifiers.append(EntityIdentifier(id_type=IdentifierType.TICKER, id_value="ABC"))
        e1.identifiers.append(EntityIdentifier(id_type=IdentifierType.ISIN, id_value="US0000000001"))

        e2 = Entity(name="Firma B (DE, zufällig gleicher Ticker)", country="DE")
        e2.identifiers.append(
            EntityIdentifier(id_type=IdentifierType.TICKER, id_value="ABC", exchange="XETRA")
        )
        e2.identifiers.append(EntityIdentifier(id_type=IdentifierType.ISIN, id_value="DE0000000002"))

        session.add_all([e1, e2])
        session.commit()

        tickers = session.scalars(
            select(EntityIdentifier).where(EntityIdentifier.id_value == "ABC")
        ).all()
        assert len(tickers) == 2
        assert {t.entity_id for t in tickers} == {e1.id, e2.id}


def test_source_roundtrip(session_factory) -> None:
    with session_factory() as session:
        source = Source(
            key="sec_edgar",
            display_name="SEC EDGAR",
            base_url="https://www.sec.gov/cgi-bin/browse-edgar",
            license_note="Public Domain (US-Regierungswerk); User-Agent mit Kontaktadresse Pflicht.",
        )
        session.add(source)
        session.commit()

    with session_factory() as session:
        loaded = session.scalars(select(Source).where(Source.key == "sec_edgar")).one()
        assert loaded.display_name == "SEC EDGAR"
        assert loaded.is_active is True


def _make_entity_and_source(session) -> tuple[Entity, Source]:
    entity = Entity(name="Testfirma AG")
    source = Source(
        key="test_source",
        display_name="Testquelle",
        base_url="https://example.invalid",
        license_note="nur für Tests",
    )
    session.add_all([entity, source])
    session.commit()
    return entity, source


def test_data_point_enthaelt_alle_provenienzfelder(session_factory) -> None:
    with session_factory() as session:
        entity, source = _make_entity_and_source(session)

        dp = DataPoint(
            entity_id=entity.id,
            source_id=source.id,
            metric_name="revenue",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            fiscal_year=2024,
            published_at=date(2025, 2, 15),
            value_raw="1234567890",
            value_normalized=1234567890.0,
            unit="USD",
            currency="USD",
            value_kind=ValueKind.REPORTED,
            quality_score=0.95,
            confidence_score=0.9,
            document_url="https://www.sec.gov/example-10k.htm",
            document_type="10-K",
            content_hash="a" * 64,
            document_id="0000000000-25-000001",
        )
        session.add(dp)
        session.commit()
        dp_id = dp.id

    with session_factory() as session:
        loaded = session.get(DataPoint, dp_id)
        assert loaded is not None
        assert loaded.value_kind == ValueKind.REPORTED
        assert loaded.value_normalized == 1234567890.0
        assert loaded.currency == "USD"
        assert loaded.content_hash == "a" * 64


def test_point_in_time_query_verhindert_look_ahead(session_factory) -> None:
    """Kernvoraussetzung für Bias-freie Backtests (Auftrag §9, ADR-6):
    Eine Abfrage zu einem historischen Stichtag darf nur Datenpunkte sehen,
    deren retrieved_at_utc zu diesem Zeitpunkt bereits bekannt war."""

    with session_factory() as session:
        entity, source = _make_entity_and_source(session)

        alt = DataPoint(
            entity_id=entity.id,
            source_id=source.id,
            metric_name="eps_diluted",
            published_at=date(2024, 1, 15),
            retrieved_at_utc=datetime(2024, 1, 16, tzinfo=UTC),
            value_raw="1.50",
            value_normalized=1.50,
            unit="USD",
            currency="USD",
            value_kind=ValueKind.REPORTED,
            document_url="https://example.invalid/report-v1",
            document_type="press_release",
            content_hash="v1",
        )
        # Restatement/Korrektur: neue Zeile, spätere retrieved_at_utc
        korrektur = DataPoint(
            entity_id=entity.id,
            source_id=source.id,
            metric_name="eps_diluted",
            published_at=date(2024, 1, 15),
            retrieved_at_utc=datetime(2024, 6, 1, tzinfo=UTC),
            value_raw="1.45",
            value_normalized=1.45,
            unit="USD",
            currency="USD",
            value_kind=ValueKind.REPORTED,
            document_url="https://example.invalid/report-v2-restated",
            document_type="10-K/A",
            content_hash="v2",
        )
        session.add_all([alt, korrektur])
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        stichtag_backtest = datetime(2024, 3, 1, tzinfo=UTC)
        sichtbar = session.scalars(
            select(DataPoint)
            .where(
                DataPoint.entity_id == entity_id,
                DataPoint.metric_name == "eps_diluted",
                DataPoint.retrieved_at_utc <= stichtag_backtest,
            )
            .order_by(DataPoint.retrieved_at_utc.desc())
        ).first()
        assert sichtbar is not None
        assert sichtbar.value_normalized == 1.50  # Korrektur vom Juni war am 1. März noch nicht bekannt

        stichtag_heute = datetime(2024, 12, 31, tzinfo=UTC)
        aktuell = session.scalars(
            select(DataPoint)
            .where(
                DataPoint.entity_id == entity_id,
                DataPoint.metric_name == "eps_diluted",
                DataPoint.retrieved_at_utc <= stichtag_heute,
            )
            .order_by(DataPoint.retrieved_at_utc.desc())
        ).first()
        assert aktuell is not None
        assert aktuell.value_normalized == 1.45


def test_audit_log_roundtrip(session_factory) -> None:
    with session_factory() as session:
        entry = AuditLogEntry(
            event_type=AuditEventType.DATA_FETCH,
            actor="connectors.sec_edgar",
            source_key="sec_edgar",
            detail="10-K für CIK 0000000000 abgerufen",
        )
        session.add(entry)
        session.commit()

    with session_factory() as session:
        loaded = session.scalars(
            select(AuditLogEntry).where(AuditLogEntry.event_type == AuditEventType.DATA_FETCH)
        ).one()
        assert loaded.actor == "connectors.sec_edgar"
        assert "geheim" not in (loaded.detail or "").lower()


@pytest.mark.slow
def test_alembic_migration_gegen_sqlite(tmp_path: Path) -> None:
    """End-to-End-Test der echten Alembic-Migration (nicht nur create_all)."""

    env = {
        **__import__("os").environ,
        "IA_DATA_DIR": str(tmp_path),
    }
    ini_path = PROJECT_ROOT / "alembic.ini"

    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert upgrade.returncode == 0, upgrade.stderr

    db_path = tmp_path / "investment_analyzer.db"
    assert db_path.exists()

    import sqlite3

    con = sqlite3.connect(db_path)
    tables = {row[0] for row in con.execute("select name from sqlite_master where type='table'")}
    con.close()
    assert {
        "entities",
        "entity_identifiers",
        "sources",
        "data_points",
        "audit_log_entries",
        "alembic_version",
    } <= tables

    downgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), "downgrade", "base"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert downgrade.returncode == 0, downgrade.stderr
