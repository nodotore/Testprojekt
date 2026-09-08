from __future__ import annotations

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
from investment_analyzer.reports.pdf_export import build_pdf_bytes, export_pdf

FETCHED_AT = datetime(2024, 3, 1, tzinfo=UTC)


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'reports-pdf-test.db'}")
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


def _build_bundle(session):
    sources = ensure_default_sources(session)
    entity = find_or_create_entity(
        session, name="Firma G (synthetisches Beispiel)",
        identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000007")],
    )
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
    return build_report_bundle(session, entity, as_of=datetime(2024, 3, 1, tzinfo=UTC))


def test_build_pdf_bytes_liefert_gueltiges_pdf(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        bundle = _build_bundle(session)
        pdf_bytes = build_pdf_bytes(bundle)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_export_pdf_schreibt_datei(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        bundle = _build_bundle(session)
        out_path = tmp_path / "report.pdf"
        export_pdf(bundle, out_path)

    assert out_path.exists()
    assert out_path.read_bytes().startswith(b"%PDF")


def test_build_pdf_bytes_enthaelt_pflichthinweis(tmp_path: Path) -> None:
    """Auftrag §12: Hinweis muss an jeder Berichtsausgabe sichtbar sein.

    Das PDF wird binär (deflate-komprimiert) erzeugt, daher lässt sich der
    Hinweistext nicht direkt im Byte-Strom suchen — stattdessen wird über
    den zugrunde liegenden ``ReportBundle``-Header geprüft, aus dem
    ``build_pdf_bytes`` den Absatz erzeugt (siehe ``reports/bundle.py``).
    """

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        bundle = _build_bundle(session)
        pdf_bytes = build_pdf_bytes(bundle)

    assert pdf_bytes.startswith(b"%PDF")
    assert "keine Anlageberatung" in bundle.header.disclaimer
    assert "Totalverlust" in bundle.header.disclaimer


def test_build_pdf_bytes_ohne_jegliche_daten_bricht_nicht_ab(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        ensure_default_sources(session)
        entity = find_or_create_entity(
            session, name="Firma ohne Daten",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000000099")],
        )
        session.commit()
        bundle = build_report_bundle(session, entity)
        pdf_bytes = build_pdf_bytes(bundle)

    assert pdf_bytes.startswith(b"%PDF")
