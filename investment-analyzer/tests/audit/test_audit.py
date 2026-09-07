from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from investment_analyzer.audit.logger import AuditLogger
from investment_analyzer.audit.logging_setup import configure_logging
from investment_analyzer.audit.models import AuditEventType, AuditLogEntry
from investment_analyzer.audit.redaction import redact
from investment_analyzer.config.settings import AppSettings
from investment_analyzer.db import create_all_tables, create_db_engine, create_session_factory


def _session_factory(tmp_path: Path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'audit-test.db'}")
    create_all_tables(engine)
    return create_session_factory(engine)


def test_audit_logger_schreibt_eintrag(tmp_path: Path) -> None:
    logger = AuditLogger(_session_factory(tmp_path))
    logger.log_data_fetch(actor="connectors.sec_edgar", source_key="sec_edgar", entity_id=None)

    with logger._session_factory() as session:  # type: ignore[attr-defined]
        eintraege = session.scalars(select(AuditLogEntry)).all()
    assert len(eintraege) == 1
    assert eintraege[0].event_type == AuditEventType.DATA_FETCH
    assert eintraege[0].actor == "connectors.sec_edgar"


def test_audit_logger_secret_accessed_speichert_nie_den_wert(tmp_path: Path) -> None:
    logger = AuditLogger(_session_factory(tmp_path))
    logger.log_secret_accessed(actor="config.secrets", secret_name="alpha_vantage")

    with logger._session_factory() as session:  # type: ignore[attr-defined]
        eintrag = session.scalars(select(AuditLogEntry)).one()
    assert eintrag.detail == "secret_name=alpha_vantage"
    assert "GEHEIM" not in eintrag.detail.upper()


def test_audit_logger_alle_ereignistypen_schreibbar(tmp_path: Path) -> None:
    logger = AuditLogger(_session_factory(tmp_path))
    logger.log_data_fetch_error(actor="a", source_key="s", detail="Timeout")
    logger.log_report_generated(actor="reports.pdf", detail="Bericht X erzeugt")
    logger.log_config_changed(actor="ui", detail="Profil aktualisiert")
    logger.log_belegpruefung_fehlgeschlagen(actor="scoring", detail="Quelle veraltet")

    with logger._session_factory() as session:  # type: ignore[attr-defined]
        typen = {e.event_type for e in session.scalars(select(AuditLogEntry)).all()}
    assert typen == {
        AuditEventType.DATA_FETCH_ERROR,
        AuditEventType.REPORT_GENERATED,
        AuditEventType.CONFIG_CHANGED,
        AuditEventType.BELEGPRUEFUNG_FEHLGESCHLAGEN,
    }


def test_redact_maskiert_api_key() -> None:
    text = "Anfrage mit api_key=SUPERGEHEIM123 fehlgeschlagen"
    assert "SUPERGEHEIM123" not in redact(text)
    assert "REDACTED" in redact(text)


def test_redact_maskiert_bearer_token() -> None:
    text = "Header: Authorization: Bearer abcdef123456.ghijk"
    result = redact(text)
    assert "abcdef123456" not in result
    assert "Bearer" in result


def test_redact_laesst_normalen_text_unveraendert() -> None:
    text = "SEC EDGAR lieferte 42 Datenpunkte für Beispiel AG."
    assert redact(text) == text


def test_configure_logging_schreibt_logdatei_und_redigiert(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path, log_level="INFO")
    logger = configure_logging(settings)
    try:
        logger.info("Verbindung mit token=geheimwert123456 aufgebaut")
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    log_file = settings.log_dir / "app.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "geheimwert123456" not in content
    assert "REDACTED" in content


def test_configure_logging_ist_idempotent(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path, log_level="DEBUG")
    logger1 = configure_logging(settings)
    handler_count_1 = len(logger1.handlers)
    logger2 = configure_logging(settings)
    handler_count_2 = len(logger2.handlers)

    assert handler_count_1 == handler_count_2 == 2
    for handler in list(logger2.handlers):
        handler.close()
        logger2.removeHandler(handler)
