from __future__ import annotations

from datetime import UTC, date, datetime

from dateutil.relativedelta import relativedelta

from investment_analyzer.ui.backtest import _rebalance_dates


def test_rebalance_dates_monatlich() -> None:
    termine = _rebalance_dates(date(2024, 1, 1), date(2024, 3, 1), relativedelta(months=1))

    assert termine == [
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 2, 1, tzinfo=UTC),
        datetime(2024, 3, 1, tzinfo=UTC),
    ]


def test_rebalance_dates_quartalsweise_ueberspringt_zwischenmonate() -> None:
    termine = _rebalance_dates(date(2024, 1, 1), date(2024, 7, 1), relativedelta(months=3))

    assert termine == [
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 4, 1, tzinfo=UTC),
        datetime(2024, 7, 1, tzinfo=UTC),
    ]


def test_rebalance_dates_zu_kurzer_zeitraum_liefert_nur_startdatum() -> None:
    # Ein Zeitraum, der kürzer als ein Schritt ist, liefert nur einen einzigen
    # Termin -- die aufrufende Seite muss das als "zu wenig für einen
    # Backtest" (mindestens zwei Stichtage nötig) erkennen und ablehnen.
    termine = _rebalance_dates(date(2024, 1, 1), date(2024, 1, 15), relativedelta(months=1))

    assert termine == [datetime(2024, 1, 1, tzinfo=UTC)]


def test_rebalance_dates_end_gleich_start_liefert_einen_termin() -> None:
    termine = _rebalance_dates(date(2024, 1, 1), date(2024, 1, 1), relativedelta(months=1))
    assert termine == [datetime(2024, 1, 1, tzinfo=UTC)]
