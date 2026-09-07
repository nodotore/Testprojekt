"""Deterministische, regelbasierte Nachrichtenklassifikation (Auftrag §6 „Nachrichten").

Sowohl Quellqualität als auch Ereignistyp werden über einfache,
nachvollziehbare Schlüsselwort-Regeln vergeben — nie durch ein
Sprachmodell (Auftrag §8a-Analogie, konsistent mit ``scoring/score.py``).
Beide Klassifikationen sind dokumentierte Heuristiken, keine
redaktionelle Prüfung: sie dienen der groben Einordnung/Filterung, nicht
als belastbare Tatsachenbehauptung über eine einzelne Meldung (Auftrag
§11: „Wurde eine Annahme als Tatsache formuliert?").
"""

from __future__ import annotations

from investment_analyzer.news.models import NewsEventType, NewsSourceCategory

#: Kleine, bewusst konservative Liste bekannter Meinungs-/Kommentar-Portale.
#: Unvollständig per Konstruktion — alles andere aus einer Nicht-IR-Quelle
#: gilt als „unabhängiger Bericht", was NICHT dieselbe Aussage ist wie
#: „redaktionell geprüft". Diese Liste kann/soll bei Bedarf erweitert
#: werden, ohne dass das ein Schema-Bruch wäre.
KNOWN_COMMENTARY_DOMAINS = frozenset(
    {
        "seekingalpha.com",
        "fool.com",
        "zacks.com",
        "benzinga.com",
        "simplywall.st",
    }
)


def classify_source_category(*, source_key: str, domain: str | None) -> str:
    """Ordnet einen Treffer einer der drei Auftrag-§6-Quellkategorien zu.

    IR-RSS-Treffer (``source_key == "ir_rss"``) sind per Definition
    Unternehmensmeldungen — die Quelle ist der eigene IR-/PR-Feed des
    Unternehmens (``connectors/ir_rss.py``). Alles andere (aktuell:
    GDELT) gilt als unabhängiger Bericht, außer die Domain steht auf der
    kleinen, dokumentierten Kommentar-Liste oben.
    """

    if source_key == "ir_rss":
        return NewsSourceCategory.UNTERNEHMENSMELDUNG
    if domain and domain.lower() in KNOWN_COMMENTARY_DOMAINS:
        return NewsSourceCategory.KOMMENTAR
    return NewsSourceCategory.UNABHAENGIGER_BERICHT


#: Reihenfolge ist Priorität: Die erste zutreffende Kategorie gewinnt. Rein
#: lexikalisch (Kleinschreibung, Teilstring-Suche) — bewusst keine
#: Named-Entity-Erkennung, kein Sprachmodell.
_EVENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        NewsEventType.MERGER_ACQUISITION,
        (
            "acquisition",
            "acquires",
            "merger",
            "merges",
            "takeover",
            "übernahme",
            "fusion",
            "akquisition",
            "zusammenschluss",
        ),
    ),
    (
        NewsEventType.EARNINGS,
        (
            "earnings",
            "quarterly results",
            "q1 results",
            "q2 results",
            "q3 results",
            "q4 results",
            "guidance",
            "quartalszahlen",
            "geschäftsbericht",
            "jahresergebnis",
        ),
    ),
    (
        NewsEventType.MANAGEMENT,
        (
            "chief executive",
            "resigns",
            "steps down",
            "appointed as ceo",
            "appoints new ceo",
            "vorstand",
            "geschäftsführung",
            "rücktritt",
            "nachfolger",
        ),
    ),
    (
        NewsEventType.LEGAL_REGULATORY,
        (
            "lawsuit",
            "sues",
            "litigation",
            "investigation",
            "regulator",
            "sanction",
            "klage",
            "ermittlung",
            "untersuchung",
            "sanktion",
            "kartellamt",
            "aufsichtsbehörde",
        ),
    ),
    (
        NewsEventType.CYBER_SUPPLY_CHAIN,
        (
            "cyberattack",
            "data breach",
            "ransomware",
            "supply chain",
            "cyberangriff",
            "datenleck",
            "lieferkette",
        ),
    ),
    (
        NewsEventType.CAPITAL_MARKETS,
        (
            "dividend",
            "buyback",
            "share repurchase",
            "rights issue",
            "bond issue",
            "dividende",
            "aktienrückkauf",
            "kapitalerhöhung",
            "anleihe",
        ),
    ),
    (
        NewsEventType.PRODUCT_OPERATIONS,
        (
            "product launch",
            "recall",
            "partnership",
            "plant closure",
            "produkteinführung",
            "rückruf",
            "partnerschaft",
            "werksschließung",
        ),
    ),
)


def classify_event_type(title: str, summary: str | None = None) -> str:
    """Ordnet Titel/Kurzfassung einem groben Ereignistyp zu (erste Übereinstimmung gewinnt).

    Rein lexikalisch — kein Sprachmodell, keine Named-Entity-Erkennung.
    Liefert ``NewsEventType.SONSTIGES``, wenn kein Schlüsselwort passt;
    das ist der Normalfall für viele Meldungen, kein Fehlerzustand.
    """

    haystack = f"{title} {summary or ''}".lower()
    for event_type, keywords in _EVENT_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return event_type
    return NewsEventType.SONSTIGES
