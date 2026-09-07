from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.fundamentals.series import (
    get_annual_series,
    get_latest_annual_value,
    get_series,
    get_value_at,
    select_annual_points,
)
from investment_analyzer.normalization.models import DataPoint, ValueKind


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'series-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _make_datapoint(
    *, entity: Entity, source: Source, metric: Metric, period_end: date, value: float, retrieved_at_utc: datetime
) -> DataPoint:
    return DataPoint(
        entity_id=entity.id,
        source_id=source.id,
        metric_name=metric.value,
        period_start=None,
        period_end=period_end,
        published_at=period_end,
        retrieved_at_utc=retrieved_at_utc,
        value_raw=str(value),
        value_normalized=value,
        unit="USD",
        currency="USD",
        value_kind=ValueKind.REPORTED,
        document_url="https://example.invalid/doc",
        document_type="10-K",
        content_hash="x" * 64,
        document_id=f"acc-{period_end.isoformat()}-{retrieved_at_utc.isoformat()}",
    )


def test_get_series_liefert_sortierte_zeitreihe(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()

        fetched_at = datetime(2024, 3, 1, tzinfo=UTC)
        session.add_all(
            [
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=300.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2021, 12, 31), value=100.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2022, 12, 31), value=200.0, retrieved_at_utc=fetched_at,
                ),
            ]
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        serie = get_series(session, entity, Metric.REVENUE)

    assert serie == [
        (date(2021, 12, 31), 100.0),
        (date(2022, 12, 31), 200.0),
        (date(2023, 12, 31), 300.0),
    ]


def test_get_series_ist_point_in_time_und_beruecksichtigt_restatements(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()

        session.add_all(
            [
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=300.0,
                    retrieved_at_utc=datetime(2024, 2, 1, tzinfo=UTC),
                ),
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=295.0,  # Restatement, später bekannt
                    retrieved_at_utc=datetime(2024, 6, 1, tzinfo=UTC),
                ),
            ]
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None

        vor_restatement = get_series(session, entity, Metric.REVENUE, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        assert vor_restatement == [(date(2023, 12, 31), 300.0)]

        nach_restatement = get_series(session, entity, Metric.REVENUE, as_of=datetime(2024, 7, 1, tzinfo=UTC))
        assert nach_restatement == [(date(2023, 12, 31), 295.0)]


def test_get_series_isoliert_nach_entity_und_metrik(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity_a = find_or_create_entity(
            session, name="Firma A",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        entity_b = find_or_create_entity(
            session, name="Firma B",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000002")],
        )
        session.flush()
        fetched_at = datetime(2024, 3, 1, tzinfo=UTC)
        session.add_all(
            [
                _make_datapoint(
                    entity=entity_a, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=100.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity_a, source=sources["sec_edgar"], metric=Metric.NET_INCOME,
                    period_end=date(2023, 12, 31), value=10.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity_b, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=999.0, retrieved_at_utc=fetched_at,
                ),
            ]
        )
        session.commit()
        entity_a_id = entity_a.id

    with session_factory() as session:
        entity_a = session.get(Entity, entity_a_id)
        assert entity_a is not None
        revenue_a = get_series(session, entity_a, Metric.REVENUE)
        net_income_a = get_series(session, entity_a, Metric.NET_INCOME)

    assert revenue_a == [(date(2023, 12, 31), 100.0)]
    assert net_income_a == [(date(2023, 12, 31), 10.0)]


def test_get_value_at_exakte_periode(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        session.add(
            _make_datapoint(
                entity=entity, source=sources["sec_edgar"], metric=Metric.TOTAL_EQUITY,
                period_end=date(2023, 12, 31), value=500.0,
                retrieved_at_utc=datetime(2024, 2, 1, tzinfo=UTC),
            )
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert get_value_at(session, entity, Metric.TOTAL_EQUITY, date(2023, 12, 31)) == 500.0
        assert get_value_at(session, entity, Metric.TOTAL_EQUITY, date(2022, 12, 31)) is None


def test_select_annual_points_filtert_quartalswerte_heraus() -> None:
    punkte = [
        (date(2022, 3, 31), 1.0),
        (date(2022, 6, 30), 2.0),
        (date(2022, 9, 30), 3.0),
        (date(2022, 12, 31), 4.0),  # FY 2022
        (date(2023, 3, 31), 5.0),
        (date(2023, 6, 30), 6.0),
        (date(2023, 9, 30), 7.0),
        (date(2023, 12, 31), 8.0),  # FY 2023
    ]
    jahrespunkte = select_annual_points(punkte)
    assert jahrespunkte == [(date(2022, 12, 31), 4.0), (date(2023, 12, 31), 8.0)]


def test_select_annual_points_leere_liste() -> None:
    assert select_annual_points([]) == []


def test_select_annual_points_einzelner_punkt() -> None:
    assert select_annual_points([(date(2023, 12, 31), 1.0)]) == [(date(2023, 12, 31), 1.0)]


def test_get_annual_series_und_latest_annual_value(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Beispiel AG",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000001")],
        )
        session.flush()
        fetched_at = datetime(2024, 3, 1, tzinfo=UTC)
        session.add_all(
            [
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2022, 3, 31), value=25.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2022, 12, 31), value=100.0, retrieved_at_utc=fetched_at,
                ),
                _make_datapoint(
                    entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE,
                    period_end=date(2023, 12, 31), value=110.0, retrieved_at_utc=fetched_at,
                ),
            ]
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        jahresserie = get_annual_series(session, entity, Metric.REVENUE)
        assert jahresserie == [(date(2022, 12, 31), 100.0), (date(2023, 12, 31), 110.0)]

        neuester = get_latest_annual_value(session, entity, Metric.REVENUE)
        assert neuester == (date(2023, 12, 31), 110.0)


def test_get_latest_annual_value_ohne_daten_liefert_none(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000099")],
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        entity = session.get(Entity, entity_id)
        assert entity is not None
        assert get_latest_annual_value(session, entity, Metric.REVENUE) is None
