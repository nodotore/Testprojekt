from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from investment_analyzer.connectors.alpha_vantage import AlphaVantageQuote
from investment_analyzer.connectors.sec_edgar import (
    SecCompanyConcept,
    SecConceptFact,
    SecSubmissions,
)
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import IdentifierType
from investment_analyzer.entity_resolution.service import IdentifierSpec, find_or_create_entity
from investment_analyzer.normalization.ingest import (
    ingest_alpha_vantage_quote,
    ingest_sec_company_concept,
    update_entity_classification,
)
from investment_analyzer.normalization.models import DataPoint, ValueKind


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'ingest-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def _concept(*, fetched_at: datetime) -> SecCompanyConcept:
    return SecCompanyConcept(
        cik="0000320193",
        taxonomy="us-gaap",
        tag="Revenues",
        label="Revenues",
        description="Umsatzerlöse.",
        facts=(
            SecConceptFact(
                end_date=date(2023, 12, 30),
                start_date=date(2023, 10, 1),
                value=119575000000.0,
                unit="USD",
                fiscal_year=2024,
                fiscal_period="Q1",
                form="10-Q",
                filed_date=date(2024, 2, 1),
                accession_number="0000320193-24-000010",
            ),
            SecConceptFact(
                end_date=date(2022, 12, 31),
                start_date=date(2022, 10, 1),
                value=117154000000.0,
                unit="USD",
                fiscal_year=2023,
                fiscal_period="Q1",
                form="10-Q",
                filed_date=date(2023, 2, 2),
                accession_number="0000320193-23-000012",
            ),
        ),
        fetched_at_utc=fetched_at,
        source_url="https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Revenues.json",
    )


def test_ingest_sec_company_concept_erzeugt_datapoints_mit_provenienz(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            country="US",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()

        fetched_at = datetime(2024, 2, 2, 12, 0, tzinfo=UTC)
        created = ingest_sec_company_concept(
            session, entity=entity, source=sources["sec_edgar"], concept=_concept(fetched_at=fetched_at)
        )
        session.commit()

    assert len(created) == 2
    erster = created[0]
    assert erster.metric_name == "revenue"
    assert erster.value_normalized == 119575000000.0
    assert erster.currency == "USD"
    assert erster.value_kind == ValueKind.REPORTED
    assert erster.document_id == "0000320193-24-000010"
    assert "sec.gov/Archives/edgar/data/320193/" in erster.document_url
    assert "0000320193-24-000010-index.htm" in erster.document_url
    assert erster.retrieved_at_utc == fetched_at
    assert len(erster.content_hash) == 64  # sha256 hex

    with session_factory() as session:
        alle = session.scalars(
            select(DataPoint).where(DataPoint.metric_name == "revenue")
        ).all()
    assert len(alle) == 2


def test_ingest_sec_company_concept_ist_idempotent(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()

        fetched_at = datetime(2024, 2, 2, 12, 0, tzinfo=UTC)
        concept = _concept(fetched_at=fetched_at)
        ingest_sec_company_concept(session, entity=entity, source=sources["sec_edgar"], concept=concept)
        session.commit()

    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()
        # Erneuter Abruf derselben Einreichungen (z. B. Cache-Miss am nächsten Tag):
        zweiter_lauf = ingest_sec_company_concept(
            session, entity=entity, source=sources["sec_edgar"], concept=_concept(fetched_at=fetched_at)
        )
        session.commit()

    assert zweiter_lauf == []  # nichts Neues eingefügt

    with session_factory() as session:
        alle = session.scalars(select(DataPoint).where(DataPoint.metric_name == "revenue")).all()
    assert len(alle) == 2  # weiterhin nur die ursprünglichen zwei Zeilen


def test_ingest_sec_company_concept_neue_einreichung_derselben_periode_wird_ergaenzt(
    tmp_path: Path,
) -> None:
    """Ein Restatement (neue Accession Number, gleiche Berichtsperiode) erzeugt eine
    zusätzliche Zeile statt die alte zu überschreiben (append-only, ADR-6)."""

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()

        erster_lauf = _concept(fetched_at=datetime(2024, 2, 2, tzinfo=UTC))
        ingest_sec_company_concept(session, entity=entity, source=sources["sec_edgar"], concept=erster_lauf)
        session.commit()

    restated_fact = SecConceptFact(
        end_date=date(2023, 12, 30),
        start_date=date(2023, 10, 1),
        value=119000000000.0,  # korrigierter Wert
        unit="USD",
        fiscal_year=2024,
        fiscal_period="Q1",
        form="10-Q/A",
        filed_date=date(2024, 3, 1),
        accession_number="0000320193-24-000099",  # NEUE Accession Number
    )
    restated_concept = SecCompanyConcept(
        cik="0000320193",
        taxonomy="us-gaap",
        tag="Revenues",
        label="Revenues",
        description=None,
        facts=(restated_fact,),
        fetched_at_utc=datetime(2024, 3, 2, tzinfo=UTC),
        source_url="https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Revenues.json",
    )

    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()
        neu = ingest_sec_company_concept(session, entity=entity, source=sources["sec_edgar"], concept=restated_concept)
        session.commit()

    assert len(neu) == 1
    assert neu[0].value_normalized == 119000000000.0

    with session_factory() as session:
        alle = session.scalars(select(DataPoint).where(DataPoint.metric_name == "revenue")).all()
    # Die ursprünglichen zwei Zeilen bleiben unverändert erhalten, plus die neue Restatement-Zeile:
    assert len(alle) == 3
    werte_fuer_periode = sorted(
        dp.value_normalized for dp in alle if dp.period_end == date(2023, 12, 30)
    )
    assert werte_fuer_periode == [119000000000.0, 119575000000.0]


def test_ingest_alpha_vantage_quote_erzeugt_datapoint_mit_reduzierter_konfidenz(
    tmp_path: Path,
) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="International Business Machines",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000051143")],
        )
        session.flush()

        quote = AlphaVantageQuote(
            symbol="IBM",
            price=Decimal("232.42"),
            previous_close=Decimal("230.09"),
            change=Decimal("2.33"),
            change_percent="1.0127%",
            volume=3465234,
            latest_trading_day=date(2024, 9, 6),
            fetched_at_utc=datetime(2024, 9, 6, 21, 0, tzinfo=UTC),
            source_url="https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM",
        )

        data_point = ingest_alpha_vantage_quote(
            session, entity=entity, source=sources["alpha_vantage"], quote=quote
        )
        session.commit()

    assert data_point.metric_name == "price_close"
    assert data_point.value_normalized == 232.42
    assert data_point.currency is None  # bewusst nicht geraten (Auftrag §11)
    assert data_point.quality_score == 0.6
    assert data_point.confidence_score == 0.6
    assert data_point.document_type == "market_data_snapshot"
    assert data_point.period_end == date(2024, 9, 6)

    with session_factory() as session:
        alle = session.scalars(select(DataPoint).where(DataPoint.metric_name == "price_close")).all()
    assert len(alle) == 1


def test_ingest_sec_company_concept_unbekannter_tag_ohne_override_wirft(tmp_path: Path) -> None:
    import pytest

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()

        unbekanntes_concept = SecCompanyConcept(
            cik="0000320193",
            taxonomy="us-gaap",
            tag="EinVoelligUnbekannterTag",
            label=None,
            description=None,
            facts=(
                SecConceptFact(
                    end_date=date(2023, 12, 30),
                    value=1.0,
                    unit="USD",
                    form="10-Q",
                    filed_date=date(2024, 2, 1),
                    accession_number="0000320193-24-000010",
                ),
            ),
            fetched_at_utc=datetime(2024, 2, 2, tzinfo=UTC),
            source_url="https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Unbekannt.json",
        )

        with pytest.raises(ValueError, match="nicht im Kennzahlen-Mapping"):
            ingest_sec_company_concept(
                session, entity=entity, source=sources["sec_edgar"], concept=unbekanntes_concept
            )


def test_ingest_sec_company_concept_mit_explizitem_metric_override(tmp_path: Path) -> None:
    from investment_analyzer.fundamentals.metrics import Metric

    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        sources = ensure_default_sources(session)
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        session.flush()

        unbekanntes_concept = SecCompanyConcept(
            cik="0000320193",
            taxonomy="us-gaap",
            tag="EinNochNichtGemapptesTag",
            label=None,
            description=None,
            facts=(
                SecConceptFact(
                    end_date=date(2023, 12, 30),
                    value=42.0,
                    unit="USD",
                    form="10-Q",
                    filed_date=date(2024, 2, 1),
                    accession_number="0000320193-24-000010",
                ),
            ),
            fetched_at_utc=datetime(2024, 2, 2, tzinfo=UTC),
            source_url="https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Unbekannt.json",
        )

        created = ingest_sec_company_concept(
            session,
            entity=entity,
            source=sources["sec_edgar"],
            concept=unbekanntes_concept,
            metric=Metric.CAPEX,
        )

    assert len(created) == 1
    assert created[0].metric_name == "capex"


def _submissions(*, sic: str | None, sic_description: str | None) -> SecSubmissions:
    return SecSubmissions(
        cik="0000320193",
        name="Apple Inc.",
        tickers=("AAPL",),
        exchanges=("Nasdaq",),
        filings=(),
        fetched_at_utc=datetime(2024, 2, 2, tzinfo=UTC),
        source_url="https://data.sec.gov/submissions/CIK0000320193.json",
        sic=sic,
        sic_description=sic_description,
    )


def test_update_entity_classification_setzt_sic_felder(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        update_entity_classification(
            entity, _submissions(sic="3571", sic_description="Electronic Computers")
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        from investment_analyzer.entity_resolution.models import Entity

        geladen = session.get(Entity, entity_id)
        assert geladen is not None
        assert geladen.sic_code == "3571"
        assert geladen.sic_description == "Electronic Computers"


def test_update_entity_classification_ueberschreibt_nicht_mit_leerwerten(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        entity = find_or_create_entity(
            session,
            name="Apple Inc.",
            identifiers=[IdentifierSpec(id_type=IdentifierType.CIK, id_value="0000320193")],
        )
        update_entity_classification(
            entity, _submissions(sic="3571", sic_description="Electronic Computers")
        )
        session.commit()
        entity_id = entity.id

    with session_factory() as session:
        from investment_analyzer.entity_resolution.models import Entity

        entity = session.get(Entity, entity_id)
        assert entity is not None
        update_entity_classification(entity, _submissions(sic=None, sic_description=None))
        session.commit()

    with session_factory() as session:
        from investment_analyzer.entity_resolution.models import Entity

        geladen = session.get(Entity, entity_id)
        assert geladen is not None
        assert geladen.sic_code == "3571"  # bleibt erhalten, wird nicht auf None zurückgesetzt
        assert geladen.sic_description == "Electronic Computers"
