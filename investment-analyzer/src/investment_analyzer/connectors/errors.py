"""Fehlerhierarchie für Connectoren (Auftrag §4: „Fehlerprotokoll").

Grundregel (Auftrag §4, SECURITY.md): Fällt eine Quelle aus, muss ein
klarer Fehler entstehen — niemals ein stiller Fallback auf einen alten
Wert, der als aktuell erscheint. Aufrufer fangen diese Fehler ab und
protokollieren sie über ``AuditLogger.log_data_fetch_error`` (siehe
``audit/logger.py``), statt sie zu verschlucken.
"""

from __future__ import annotations


class ConnectorError(RuntimeError):
    """Basisklasse aller Connector-Fehler."""


class SSRFBlockedError(ConnectorError):
    """Eine Anfrage wurde durch den SSRF-Schutz/die URL-Allowlist blockiert (Auftrag §12)."""


class ConnectorTimeoutError(ConnectorError):
    """Die Anfrage hat das konfigurierte Timeout überschritten."""


class ConnectorRateLimitedError(ConnectorError):
    """Die Gegenstelle hat mit HTTP 429 (Rate Limit) geantwortet."""


class ConnectorHTTPError(ConnectorError):
    """Die Gegenstelle hat mit einem nicht erfolgreichen HTTP-Status geantwortet."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class ConnectorValidationError(ConnectorError):
    """Die Antwort der Gegenstelle entspricht nicht dem erwarteten Schema."""


class NoFreshDataAvailableError(ConnectorError):
    """Live-Abruf fehlgeschlagen UND kein noch gültiger (nicht abgelaufener) Cache-Eintrag
    vorhanden. Wird bewusst NICHT durch einen stillschweigend zurückgegebenen,
    abgelaufenen Cache-Wert ersetzt (Auftrag §4)."""
