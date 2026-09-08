"""Deterministische Top-N-Auswahl-Strategie (Auftrag §9: „Keine Optimierung
akzeptieren, die nur auf einem Zeitraum oder wenigen Aktien funktioniert").

Die Auswahl nutzt ausschließlich das bereits bestehende, feste
Scoring-System aus Milestone 4 (Startgewichtung gemäß Auftrag §7) — kein
zusätzlicher, auf dem Backtest-Zeitraum gefitteter Parameter. Das ist
eine strukturelle Absicherung gegen Overfitting: Es gibt in dieser
Strategie keinen freien Parameter, der auf historische Daten „trainiert"
werden könnte.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from investment_analyzer.backtesting.universe import get_point_in_time_universe
from investment_analyzer.scoring.score import KLASSE_DATENLAGE_UNZUREICHEND, score_entity


def select_top_n(
    session: Session, *, as_of: datetime, n: int, weights: dict[str, float] | None = None
) -> list[str]:
    """Wählt bis zu ``n`` Entity-IDs mit dem höchsten Score zum Stichtag ``as_of``.

    Nutzt ausschließlich Daten, die zu ``as_of`` bereits bekannt waren
    (``get_point_in_time_universe`` + ``score_entity(..., as_of=as_of)``).
    Entities ohne berechenbaren Score (``total_score is None``) ODER mit
    der Klassifikation „Datenlage unzureichend" werden ausgeschlossen —
    ``total_score`` allein reicht nicht: die Datenqualitäts-Komponente
    liefert immer einen Zahlenwert (auch 0 bei völlig fehlenden
    Fundamentaldaten), sodass ``total_score`` selbst dann nicht ``None``
    wäre. Erst die von ``compute_score`` bereits vorgenommene
    Konfidenz-Einstufung (Auftrag §7: „Beobachten"/„Datenlage
    unzureichend" statt Nullbewertung) macht diese Fälle zuverlässig
    erkennbar. Bei Score-Gleichstand entscheidet die ``entity_id`` für
    ein deterministisches, reproduzierbares Ergebnis.
    """

    if n <= 0:
        raise ValueError("n muss größer als 0 sein.")

    universe = get_point_in_time_universe(session, as_of)
    scored: list[tuple[str, float]] = []
    for entity in universe:
        result = score_entity(session, entity, as_of=as_of, weights=weights)
        if result.total_score is not None and result.classification != KLASSE_DATENLAGE_UNZUREICHEND:
            scored.append((entity.id, result.total_score))

    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return [entity_id for entity_id, _ in scored[:n]]
