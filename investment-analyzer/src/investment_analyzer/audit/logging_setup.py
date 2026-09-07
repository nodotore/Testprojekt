"""Zentrales Logging-Setup (Auftrag §4, §12).

Konfiguriert Konsole + rotierende Logdatei unter ``AppSettings.log_dir``.
Beide Handler erhalten den ``RedactingFilter`` (siehe ``redaction.py``).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from investment_analyzer.audit.redaction import RedactingFilter
from investment_analyzer.config.settings import AppSettings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(settings: AppSettings) -> logging.Logger:
    """Richtet das Root-Logging für die Anwendung ein und gibt den App-Logger zurück.

    Idempotent bezüglich mehrfachen Aufrufs innerhalb desselben Prozesses:
    vorhandene Handler des App-Loggers werden vor dem Neuaufbau entfernt.
    """

    settings.ensure_data_dirs()

    logger = logging.getLogger("investment_analyzer")
    logger.setLevel(settings.log_level.upper())
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter(_LOG_FORMAT)
    redacting_filter = RedactingFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redacting_filter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        settings.log_dir / "app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redacting_filter)
    logger.addHandler(file_handler)

    return logger
