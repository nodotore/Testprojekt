"""Zeitreihen-Repository: ``DataPoint`` → Kennzahlen-Zeitreihen (Auftrag §5, §9).

Point-in-time-fähig: Jede Abfrage akzeptiert einen optionalen ``as_of``-
Zeitpunkt und berücksichtigt nur Datenpunkte, die zu diesem Zeitpunkt
bereits bekannt waren (``retrieved_at_utc <= as_of``). Ohne ``as_of``
wird der aktuelle Zeitpunkt verwendet. Für jede Berichtsperiode
(``period_end``) wird der zu diesem Stichtag zuletzt bekannte Wert
verwendet — spätere Restatements zählen nur, wenn sie vor ``as_of``
eingetroffen sind (kein Look-ahead, Voraussetzung für Milestone 7).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.calculations import TimeSeries
from investment_analyzer.fundamentals.metrics import Metric
from investment_analyzer.normalization.models import DataPoint

#: Zwei aufeinanderfolgende „Jahres"-Datenpunkte müssen mindestens so viele Tage
#: auseinanderliegen, um als unterschiedliche Geschäftsjahre statt Quartale zu gelten.
_MIN_ANNUAL_SPACING_DAYS = 330


def get_series(
    session: Session, entity: Entity, metric: Metric, *, as_of: datetime | None = None
) -> list[tuple[date, float]]:
    """Liefert eine nach Datum aufsteigende (Periodenende, Wert)-Zeitreihe.

    Enthält je ``period_end`` genau einen Wert: den zum Stichtag ``as_of``
    zuletzt bekannten (spätestes ``retrieved_at_utc`` ≤ ``as_of``).
    """

    reference = as_of or utc_now()
    rows = session.execute(
        select(DataPoint.period_end, DataPoint.value_normalized)
        .where(
            DataPoint.entity_id == entity.id,
            DataPoint.metric_name == metric.value,
            DataPoint.retrieved_at_utc <= reference,
            DataPoint.period_end.is_not(None),
            DataPoint.value_normalized.is_not(None),
        )
        .order_by(DataPoint.period_end, DataPoint.retrieved_at_utc)
    ).all()

    # Zeilen sind je period_end aufsteigend nach retrieved_at_utc sortiert,
    # daher gewinnt beim Überschreiben automatisch der zuletzt bekannte Wert.
    latest_by_period: dict[date, float] = {}
    for period_end, value in rows:
        latest_by_period[period_end] = value

    return sorted(latest_by_period.items())


def get_value_at(
    session: Session, entity: Entity, metric: Metric, period_end: date, *, as_of: datetime | None = None
) -> float | None:
    """Punktabfrage: Wert einer Kennzahl zu einem exakten Periodenende, point-in-time gefiltert."""

    reference = as_of or utc_now()
    row = session.execute(
        select(DataPoint.value_normalized)
        .where(
            DataPoint.entity_id == entity.id,
            DataPoint.metric_name == metric.value,
            DataPoint.period_end == period_end,
            DataPoint.retrieved_at_utc <= reference,
        )
        .order_by(DataPoint.retrieved_at_utc.desc())
        .limit(1)
    ).first()
    return row[0] if row is not None else None


def _select_annual_dates(dates: Sequence[date]) -> list[date]:
    """Greedy-Auswahl von Jahres-Stichtagen vom jüngsten rückwärts (siehe ``select_annual_points``)."""

    sorted_dates = sorted(dates)
    if not sorted_dates:
        return []

    selected = [sorted_dates[-1]]
    for d in reversed(sorted_dates[:-1]):
        if (selected[-1] - d).days >= _MIN_ANNUAL_SPACING_DAYS:
            selected.append(d)

    return list(reversed(selected))


def select_annual_points(points: TimeSeries) -> list[tuple[date, float]]:
    """Wählt aus einer gemischten Quartals-/Jahres-Zeitreihe nur Jahrespunkte aus.

    Greedy-Auswahl vom jüngsten Punkt rückwärts: ein Punkt wird
    aufgenommen, wenn er mindestens ``_MIN_ANNUAL_SPACING_DAYS`` vor dem
    zuletzt aufgenommenen Punkt liegt. Funktioniert unabhängig davon, ob
    die Kennzahl eine Fluss- (mit Periodenlänge) oder Bestandsgröße
    (Bilanzstichtag) ist, ohne zusätzliche Metadaten wie „Q1"/„FY" zu
    benötigen (die der Company-Concept-Endpoint zwar liefert, das
    Datenmodell aber bewusst nicht separat speichert — siehe
    `normalization/models.py`).
    """

    by_date = dict(points)
    annual_dates = _select_annual_dates(list(by_date.keys()))
    return [(d, by_date[d]) for d in annual_dates]


def get_annual_series(
    session: Session, entity: Entity, metric: Metric, *, as_of: datetime | None = None
) -> list[tuple[date, float]]:
    """Bequemlichkeitsfunktion: ``get_series`` gefolgt von ``select_annual_points``."""

    return select_annual_points(get_series(session, entity, metric, as_of=as_of))


def get_latest_annual_value(
    session: Session, entity: Entity, metric: Metric, *, as_of: datetime | None = None
) -> tuple[date, float] | None:
    """Neuester Jahresdatenpunkt (Periodenende, Wert), oder ``None`` falls keiner vorhanden."""

    annual = get_annual_series(session, entity, metric, as_of=as_of)
    return annual[-1] if annual else None


def get_latest_annual_datapoint(
    session: Session, entity: Entity, metric: Metric, *, as_of: datetime | None = None
) -> DataPoint | None:
    """Wie ``get_latest_annual_value``, liefert aber die vollständige ``DataPoint``-Zeile.

    Wird für Warnsignale benötigt, die zusätzliche Provenienzfelder wie
    ``published_at`` (Einreichungsdatum) benötigen, nicht nur den Wert
    (siehe ``risk/warning_signals.py``: verspätete Einreichung).
    """

    reference = as_of or utc_now()
    rows = (
        session.execute(
            select(DataPoint)
            .where(
                DataPoint.entity_id == entity.id,
                DataPoint.metric_name == metric.value,
                DataPoint.retrieved_at_utc <= reference,
                DataPoint.period_end.is_not(None),
            )
            .order_by(DataPoint.period_end, DataPoint.retrieved_at_utc)
        )
        .scalars()
        .all()
    )

    latest_by_period: dict[date, DataPoint] = {}
    for row in rows:
        assert row.period_end is not None
        latest_by_period[row.period_end] = row

    annual_dates = _select_annual_dates(list(latest_by_period.keys()))
    if not annual_dates:
        return None
    return latest_by_period[annual_dates[-1]]


def get_latest_value(
    session: Session, entity: Entity, metric: Metric, *, as_of: datetime | None = None
) -> tuple[date, float] | None:
    """Jüngster bekannter Wert, OHNE Jahres-/Quartalsfilterung.

    Für Kennzahlen ohne Jahresrhythmus (insbesondere Marktdaten wie
    ``Metric.PRICE_CLOSE``, die täglich beobachtet werden) ist
    ``get_latest_annual_value`` ungeeignet — hier zählt schlicht der
    zeitlich jüngste, zum Stichtag ``as_of`` bereits bekannte Punkt.
    """

    points = get_series(session, entity, metric, as_of=as_of)
    return points[-1] if points else None
