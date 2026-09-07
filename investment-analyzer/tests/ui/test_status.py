from __future__ import annotations

from pathlib import Path

from investment_analyzer.audit.models import AuditEventType, AuditLogEntry
from investment_analyzer.connectors.models import Source
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.ui.status import lade_datenstatus


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'status-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_datenstatus_ist_leer_ohne_daten(tmp_path: Path) -> None:
    status = lade_datenstatus(_session_factory(tmp_path))
    assert status.anzahl_unternehmen == 0
    assert status.anzahl_quellen == 0
    assert status.anzahl_datenpunkte == 0
    assert status.letzte_aktivitaet_utc is None


def test_datenstatus_zaehlt_reale_datensaetze(tmp_path: Path) -> None:
    session_factory = _session_factory(tmp_path)
    with session_factory() as session:
        session.add(Entity(name="Testfirma"))
        session.add(
            Source(
                key="sec_edgar",
                display_name="SEC EDGAR",
                base_url="https://www.sec.gov",
                license_note="Public Domain",
            )
        )
        session.add(AuditLogEntry(event_type=AuditEventType.CONFIG_CHANGED, actor="test"))
        session.commit()

    status = lade_datenstatus(session_factory)
    assert status.anzahl_unternehmen == 1
    assert status.anzahl_quellen == 1
    assert status.anzahl_datenpunkte == 0
    assert status.letzte_aktivitaet_utc is not None
