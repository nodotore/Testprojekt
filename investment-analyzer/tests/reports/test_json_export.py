from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity, IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint, ValueKind
from investment_analyzer.reports.bundle import build_report_bundle
from investment_analyzer.reports.json_export import report_bundle_to_dict, report_bundle_to_json

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'reports-json-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _dp(
    *, entity: Entity, source: Source, metric: Metric, period_end: date, value: float,
    retrieved_at_utc: datetime = FETCHED_AT,
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
        document_id=f"acc-{metric.value}-{period_end.isoformat()}",
    )


def _build_bundle_with_peer(session, tmp_path: Path):
    sources = ensure_default_sources(session)
    entity = find_or_create_entity(
        session, name="Firma G (synthetisches Beispiel)",
        identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
    )
    entity.sic_code = "3571"
    peer = find_or_create_entity(
        session, name="Firma H (Branchenkollege)",
        identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000010")],
    )
    peer.sic_code = "3571"
    session.flush()

    for d, u in zip(
        [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)],
        [1000.0, 1100.0, 1210.0, 1331.0],
        strict=True,
    ):
        session.add(_dp(entity=entity, source=sources["sec_edgar"], metric=Metric.REVENUE, period_end=d, value=u))
        session.add(
            _dp(entity=entity, source=sources["sec_edgar"], metric=Metric.OPERATING_CASH_FLOW, period_end=d, value=u * 0.15)
        )
        session.add(_dp(entity=entity, source=sources["sec_edgar"], metric=Metric.CAPEX, period_end=d, value=-u * 0.05))

    session.add(
        _dp(
            entity=entity, source=sources["sec_edgar"], metric=Metric.PRICE_CLOSE, period_end=date(2024, 1, 15),
            value=20.0, retrieved_at_utc=datetime(2024, 1, 15, tzinfo=UTC),
        )
    )
    session.commit()
    return entity


def test_report_bundle_to_dict_ist_json_serialisierbar(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)

    # json.dumps darf nicht scheitern -- das ist der eigentliche Test.
    json.dumps(as_dict)


def test_report_bundle_to_dict_serialisiert_daten_als_iso_strings(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)

    assert as_dict["header"]["as_of"] == "2024-03-01T00:00:00+00:00"
    assert isinstance(as_dict["header"]["generated_at_utc"], str)


def test_report_bundle_to_dict_flacht_peer_entities_ab(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)

    peers = as_dict["fundamentals"]["peers"]
    assert len(peers) == 1
    assert peers[0]["name"] == "Firma H (Branchenkollege)"
    assert set(peers[0]) == {"id", "name", "country", "primary_exchange", "sic_code", "sic_description"}


def test_report_bundle_to_dict_enthaelt_alle_top_level_bereiche(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)

    assert set(as_dict) == {
        "header", "fundamentals", "valuation", "score", "news", "sources", "assumptions"
    }


def test_report_bundle_to_json_liefert_dieselben_werte_wie_to_dict(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)
        as_json = report_bundle_to_json(bundle)

    assert json.loads(as_json) == as_dict


def test_report_bundle_to_dict_dcf_szenarien_enthalten_assumptions(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = _build_bundle_with_peer(session, tmp_path)
        bundle = build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))
        as_dict = report_bundle_to_dict(bundle)

    scenarios = as_dict["valuation"]["dcf_scenarios"]
    assert "Basis" in scenarios
    assert "wacc" in scenarios["Basis"]["assumptions"]
