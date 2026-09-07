"""Best-effort-Redaction bekannter Secret-Muster in Logausgaben (Auftrag §12, SECURITY.md).

Dies ist eine zusätzliche Verteidigungslinie, KEIN Ersatz für die
Grundregel „Secrets werden nie geloggt" — Aufrufer dürfen
``SecretStore``-Rückgabewerte niemals an Log-Aufrufe übergeben. Dieser
Filter fängt Fälle ab, in denen ein Secret versehentlich (z. B. über
eine rohe HTTP-Header- oder Request-Log-Zeile) in eine Lognachricht
gelangt.
"""

from __future__ import annotations

import logging
import re

_REDACTED = "***REDACTED***"

_PATTERNS: tuple[re.Pattern[str], ...] = (
    # key=..., token: "...", password='...', api_key=...
    re.compile(
        r"(?i)\b(api[_-]?key|token|secret|password|passwort)\b(\s*[:=]\s*)(['\"]?)"
        r"([A-Za-z0-9_\-\.]{6,})\3"
    ),
    # Authorization: Bearer <token>
    re.compile(r"(?i)(Authorization:\s*Bearer\s+)([A-Za-z0-9_\-\.]{6,})"),
)


def redact(text: str) -> str:
    """Ersetzt erkannte Secret-artige Teilstrings in ``text``."""

    result = text
    for pattern in _PATTERNS:
        if pattern.groups == 4:
            result = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{_REDACTED}{m.group(3)}", result)
        else:
            result = pattern.sub(lambda m: f"{m.group(1)}{_REDACTED}", result)
    return result


class RedactingFilter(logging.Filter):
    """Logging-Filter, der ``record.msg`` (sofern String) durch ``redact()`` schickt."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        return True
