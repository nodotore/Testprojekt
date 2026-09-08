"""Train-/Validierungs-/Out-of-Sample-Zeitraumtrennung (Auftrag §9:
„Train-, Validierungs- und Out-of-sample-Zeiträume trennen").

Eine reine, deterministische Funktion: teilt einen Gesamtzeitraum in
drei nicht überlappende, chronologisch aufeinanderfolgende Abschnitte.
Muss VOR jeder Parameteroptimierung angewendet werden — die Optimierung
eines Backtest-Parameters (z. B. ein Score-Schwellenwert) darf
ausschließlich auf dem Train-Zeitraum erfolgen, ihre Güte nur auf dem
Validierungs-Zeitraum geprüft werden, und der Out-of-Sample-Zeitraum
darf erst am Ende einmal zur finalen Bestätigung herangezogen werden
(Auftrag §9: „Keine Optimierung akzeptieren, die nur auf einem Zeitraum
oder wenigen Aktien funktioniert").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("start darf nicht nach end liegen.")


@dataclass(frozen=True)
class TrainValidationSplit:
    train: DateRange
    validation: DateRange
    out_of_sample: DateRange


def split_train_validation_out_of_sample(
    start: date,
    end: date,
    *,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> TrainValidationSplit:
    """Teilt ``[start, end]`` chronologisch in drei nicht überlappende Abschnitte.

    ``train_fraction`` + ``validation_fraction`` müssen zusammen kleiner
    als 1 sein (der Rest ist Out-of-Sample). Die Reihenfolge ist immer
    chronologisch (Train zuerst) — ein Backtest, der für die früheste
    Optimierungsphase spätere Daten verwendet, wäre selbst ein
    Look-ahead-Verstoß.
    """

    if start >= end:
        raise ValueError("start muss vor end liegen.")
    if not (0 < train_fraction < 1):
        raise ValueError("train_fraction muss zwischen 0 und 1 liegen.")
    if not (0 < validation_fraction < 1):
        raise ValueError("validation_fraction muss zwischen 0 und 1 liegen.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train_fraction + validation_fraction muss kleiner als 1 sein.")

    total_days = (end - start).days
    train_end = start + timedelta(days=round(total_days * train_fraction))
    validation_end = train_end + timedelta(days=round(total_days * validation_fraction))

    return TrainValidationSplit(
        train=DateRange(start, train_end),
        validation=DateRange(train_end, validation_end),
        out_of_sample=DateRange(validation_end, end),
    )
