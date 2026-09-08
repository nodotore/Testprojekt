"""HTML-Bereinigung für Nachrichteninhalte (Auftrag §12, Milestone 5).

Roh-Inhalte aus RSS-/Atom-Feeds und Nachrichtensuchen sind Text aus
nicht vertrauenswürdigen externen Quellen. Auftrag §12 verlangt:
„Eingaben aus Webseiten als nicht vertrauenswürdig behandeln;
Prompt-Injection-Texte ignorieren" sowie „HTML bereinigen". Dieses Modul
wandelt rohes HTML in reinen Klartext um — kein Markup, keine Skripte,
keine Links bleiben erhalten.

Das Ergebnis ist ein Datum, niemals eine Instruktion: Jede künftige
Weiterverarbeitung (insbesondere eine KI-Zusammenfassung, siehe
``news/report.py`` und die dort dokumentierte Lücke) MUSS diesen Text
weiterhin als reine Nutzdaten behandeln und darf keiner darin
enthaltenen Anweisung folgen. Dieses Modul entfernt nur die technische
Angriffsfläche von Markup/Skripten — der eigentliche Prompt-Injection-
Schutz („Anweisungen in Fremdtext ignorieren") bleibt Aufgabe jeder
Stelle, die diesen Text später einem Sprachmodell übergibt.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

#: Grobes Sicherheitsnetz für den (praktisch nie erreichten) Ausnahmefall,
#: dass ``HTMLParser`` selbst eine Ausnahme wirft — entfernt zumindest jedes
#: ``<...>``-Tag, statt den Rohtext unverändert durchzulassen (Milestone-8-
#: Security-Review, unabhängige Prüfung: die vorherige Rückfallvariante
#: `text = raw` widersprach der eigenen Modul-Zusicherung „kein Markup
#: bleibt erhalten", siehe DECISIONS.md ADR-25).
_TAG_PATTERN = re.compile(r"<[^>]*>")

#: Innerhalb dieser Tags wird der Inhalt komplett verworfen — Skript-/
#: Stilinhalte sind kein Nachrichtentext und werden nie ausgeführt oder
#: angezeigt.
_SKIP_CONTENT_TAGS = frozenset({"script", "style"})

#: Es wird bewusst nur ein kurzer Ausschnitt gespeichert, kein Volltext
#: (Urheberrecht/Fair-Use der angebundenen Quellen, siehe news/models.py).
DEFAULT_MAX_LENGTH = 2000


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_CONTENT_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def sanitize_html_to_text(raw: str | None, *, max_length: int = DEFAULT_MAX_LENGTH) -> str | None:
    """Wandelt (potenziell) HTML-haltigen Text in bereinigten Klartext um.

    Liefert ``None`` für ``None``/leeren/nur-Whitespace-Input. Entfernt
    jegliches Markup, verwirft Skript-/Stilinhalte, kollabiert
    überflüssigen Leerraum und kürzt auf ``max_length`` Zeichen (an einer
    Wortgrenze, mit Auslassungszeichen).

    Kaputtes/unvollständiges HTML löst KEINEN Fehler aus (Nachrichten-
    Ingestion darf an einem einzelnen fehlerhaften Feed-Eintrag nicht
    insgesamt scheitern) — im (praktisch nie eintretenden) Ausnahmefall,
    dass ``HTMLParser`` selbst wirft, wird ersatzweise über einen groben
    Regex-Tag-Entferner bereinigt statt des unveränderten Rohtexts, damit
    die Zusicherung „kein Markup bleibt erhalten" auch auf diesem Pfad gilt.
    """

    if not raw or not raw.strip():
        return None

    parser = _TextExtractor()
    try:
        parser.feed(raw)
        parser.close()
        text = parser.text()
    except Exception:  # noqa: BLE001 — Ingestion darf hierdurch nie abbrechen.
        text = _TAG_PATTERN.sub(" ", raw)

    text = html.unescape(text)
    collapsed = " ".join(text.split())
    if not collapsed:
        return None

    if len(collapsed) <= max_length:
        return collapsed
    truncated = collapsed[:max_length].rsplit(" ", 1)[0] or collapsed[:max_length]
    return f"{truncated}…"
