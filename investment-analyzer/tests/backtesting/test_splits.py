from __future__ import annotations

from datetime import date, timedelta

import pytest

from investment_analyzer.backtesting.splits import split_train_validation_out_of_sample


def test_split_teilt_chronologisch_und_nicht_ueberlappend() -> None:
    result = split_train_validation_out_of_sample(
        date(2020, 1, 1), date(2030, 1, 1), train_fraction=0.6, validation_fraction=0.2
    )
    assert result.train.start == date(2020, 1, 1)
    assert result.train.end == result.validation.start
    assert result.validation.end == result.out_of_sample.start
    assert result.out_of_sample.end == date(2030, 1, 1)


def test_split_reihenfolge_ist_train_vor_validation_vor_oos() -> None:
    result = split_train_validation_out_of_sample(date(2020, 1, 1), date(2024, 1, 1))
    assert result.train.start <= result.train.end <= result.validation.end <= result.out_of_sample.end


def test_split_anteile_ergeben_ungefaehr_die_erwartete_dauer() -> None:
    result = split_train_validation_out_of_sample(
        date(2020, 1, 1), date(2020, 1, 1) + timedelta(days=100), train_fraction=0.5, validation_fraction=0.3
    )
    train_days = (result.train.end - result.train.start).days
    validation_days = (result.validation.end - result.validation.start).days
    oos_days = (result.out_of_sample.end - result.out_of_sample.start).days
    assert train_days == 50
    assert validation_days == 30
    assert oos_days == 20


def test_split_start_muss_vor_end_liegen() -> None:
    with pytest.raises(ValueError, match="start"):
        split_train_validation_out_of_sample(date(2024, 1, 1), date(2020, 1, 1))


def test_split_ungueltige_fractions() -> None:
    with pytest.raises(ValueError, match="train_fraction"):
        split_train_validation_out_of_sample(date(2020, 1, 1), date(2024, 1, 1), train_fraction=0.0)
    with pytest.raises(ValueError, match="validation_fraction"):
        split_train_validation_out_of_sample(
            date(2020, 1, 1), date(2024, 1, 1), validation_fraction=1.0
        )


def test_split_fractions_summe_muss_kleiner_eins_sein() -> None:
    with pytest.raises(ValueError, match="train_fraction \\+ validation_fraction"):
        split_train_validation_out_of_sample(
            date(2020, 1, 1), date(2024, 1, 1), train_fraction=0.7, validation_fraction=0.4
        )
