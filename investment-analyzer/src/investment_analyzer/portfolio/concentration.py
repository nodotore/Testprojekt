"""Konzentrationsanalyse für Watchlist/Portfolio (Auftrag §8: „Branchen-,
Länder-, Währungs- und Faktor-Konzentration anzeigen").

Gewichtung nach Marktwert (Menge × jüngster bekannter Kurs, siehe
``fundamentals/series.py::get_latest_value``, aufgerufen in
``portfolio/report.py``). Reine Funktionen ohne Datenbankzugriff —
dieselbe Trennung wie in ``valuation/``/``scoring/``.

**Bewusste Einschränkung:** Es existiert kein Fremdwährungs-
Umrechnungsmodell (dieselbe Lücke wie die unbekannte Alpha-Vantage-
Kurswährung, siehe ``DECISIONS.md`` ADR-16/ADR-20). Branchen- und
Länder-Konzentration als Prozentsatz sind nur sinnvoll, wenn alle
einbezogenen Positionen in derselben Bestandswährung geführt werden —
bei gemischten Währungen würde eine Summierung ohne FX-Umrechnung
Äpfel mit Birnen addieren (Auftrag §11: keine erfundene/implizite
Umrechnung). In diesem Fall liefert die Funktion ``computable=False``
statt eines irreführenden Prozentsatzes. Währungs-Exposure wird deshalb
separat und OHNE Prozentangabe über Währungsgrenzen hinweg ausgewiesen
(``currency_exposure``).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

#: Aus Auftrag §8 nicht umgesetzt: „Faktor-Konzentration" (Value-/Growth-/
#: Quality-Exposure je Position) — dafür existiert noch kein Faktormodell
#: bzw. keine strukturierte Stil-Klassifikation je Entity.
NOT_YET_IMPLEMENTABLE_CONCENTRATIONS: tuple[str, ...] = ("faktor_konzentration",)


@dataclass(frozen=True)
class PositionValue:
    """Marktwert einer Position zum Zeitpunkt der Berechnung, plus die für die
    Konzentrationsanalyse benötigten Klassifikationsmerkmale."""

    entity_id: str
    market_value: float
    currency: str
    sector: str | None
    country: str | None


@dataclass(frozen=True)
class ConcentrationBreakdown:
    """Prozentuale Konzentration je Gruppierungsschlüssel (Anteile summieren
    sich auf 1.0, sofern ``unclassified_value`` 0 ist)."""

    computable: bool
    note: str | None
    by_key: dict[str, float]
    total_value: float
    unclassified_value: float


@dataclass(frozen=True)
class CurrencyExposure:
    """Rohe Marktwerte je Bestandswährung — bewusst KEINE Prozentangabe über
    Währungsgrenzen hinweg (siehe Modul-Docstring)."""

    value_by_currency: dict[str, float]


def _single_currency_breakdown(
    values: Sequence[PositionValue], key_fn: Callable[[PositionValue], str | None]
) -> ConcentrationBreakdown:
    if not values:
        return ConcentrationBreakdown(
            computable=True, note="Keine Positionen vorhanden.", by_key={}, total_value=0.0,
            unclassified_value=0.0,
        )

    currencies = {v.currency for v in values}
    if len(currencies) > 1:
        return ConcentrationBreakdown(
            computable=False,
            note=(
                f"Gemischte Bestandswährungen ({', '.join(sorted(currencies))}) ohne "
                "FX-Umrechnung nicht als ein Prozentsatz darstellbar (siehe DECISIONS.md ADR-20)."
            ),
            by_key={},
            total_value=0.0,
            unclassified_value=0.0,
        )

    total = sum(v.market_value for v in values)
    if total <= 0:
        return ConcentrationBreakdown(
            computable=True, note="Gesamtmarktwert ist 0 oder negativ.", by_key={}, total_value=0.0,
            unclassified_value=0.0,
        )

    grouped: dict[str, float] = {}
    unclassified = 0.0
    for value in values:
        key = key_fn(value)
        if key is None:
            unclassified += value.market_value
            continue
        grouped[key] = grouped.get(key, 0.0) + value.market_value

    by_key = {key: amount / total for key, amount in grouped.items()}
    note = (
        "Einzelne Positionen ohne bekannte Klassifikation fließen als "
        "'unclassified_value' nicht in by_key ein."
        if unclassified > 0
        else None
    )
    return ConcentrationBreakdown(
        computable=True, note=note, by_key=by_key, total_value=total, unclassified_value=unclassified
    )


def sector_concentration(values: Sequence[PositionValue]) -> ConcentrationBreakdown:
    return _single_currency_breakdown(values, lambda v: v.sector)


def country_concentration(values: Sequence[PositionValue]) -> ConcentrationBreakdown:
    return _single_currency_breakdown(values, lambda v: v.country)


def currency_exposure(values: Sequence[PositionValue]) -> CurrencyExposure:
    exposure: dict[str, float] = {}
    for value in values:
        exposure[value.currency] = exposure.get(value.currency, 0.0) + value.market_value
    return CurrencyExposure(value_by_currency=exposure)
