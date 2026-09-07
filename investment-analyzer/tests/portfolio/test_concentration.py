from __future__ import annotations

from investment_analyzer.portfolio.concentration import (
    PositionValue,
    country_concentration,
    currency_exposure,
    sector_concentration,
)


def _pv(*, entity_id, market_value, currency="EUR", sector=None, country=None) -> PositionValue:
    return PositionValue(
        entity_id=entity_id, market_value=market_value, currency=currency, sector=sector, country=country
    )


def test_sector_concentration_berechnet_anteile_exakt() -> None:
    values = [
        _pv(entity_id="1", market_value=600.0, sector="Tech"),
        _pv(entity_id="2", market_value=400.0, sector="Energie"),
    ]
    result = sector_concentration(values)
    assert result.computable is True
    assert result.total_value == 1000.0
    assert result.by_key == {"Tech": 0.6, "Energie": 0.4}
    assert result.unclassified_value == 0.0


def test_sector_concentration_gleicher_sektor_wird_summiert() -> None:
    values = [
        _pv(entity_id="1", market_value=300.0, sector="Tech"),
        _pv(entity_id="2", market_value=300.0, sector="Tech"),
        _pv(entity_id="3", market_value=400.0, sector="Energie"),
    ]
    result = sector_concentration(values)
    assert result.by_key == {"Tech": 0.6, "Energie": 0.4}


def test_sector_concentration_ohne_klassifikation_wird_separat_ausgewiesen() -> None:
    values = [
        _pv(entity_id="1", market_value=800.0, sector="Tech"),
        _pv(entity_id="2", market_value=200.0, sector=None),
    ]
    result = sector_concentration(values)
    assert result.by_key == {"Tech": 0.8}
    assert result.unclassified_value == 200.0
    assert result.note is not None


def test_gemischte_waehrungen_sind_nicht_berechenbar() -> None:
    values = [
        _pv(entity_id="1", market_value=100.0, currency="EUR", sector="Tech"),
        _pv(entity_id="2", market_value=100.0, currency="USD", sector="Tech"),
    ]
    result = sector_concentration(values)
    assert result.computable is False
    assert result.by_key == {}
    assert "Bestandswährungen" in (result.note or "")


def test_leere_liste_ist_berechenbar_aber_leer() -> None:
    result = sector_concentration([])
    assert result.computable is True
    assert result.by_key == {}
    assert result.total_value == 0.0


def test_country_concentration_funktioniert_analog() -> None:
    values = [
        _pv(entity_id="1", market_value=700.0, country="US"),
        _pv(entity_id="2", market_value=300.0, country="DE"),
    ]
    result = country_concentration(values)
    assert result.by_key == {"US": 0.7, "DE": 0.3}


def test_currency_exposure_summiert_rohe_werte_je_waehrung() -> None:
    values = [
        _pv(entity_id="1", market_value=100.0, currency="EUR"),
        _pv(entity_id="2", market_value=50.0, currency="EUR"),
        _pv(entity_id="3", market_value=200.0, currency="USD"),
    ]
    exposure = currency_exposure(values)
    assert exposure.value_by_currency == {"EUR": 150.0, "USD": 200.0}


def test_currency_exposure_liefert_keine_prozentangabe() -> None:
    exposure = currency_exposure([_pv(entity_id="1", market_value=100.0, currency="EUR")])
    assert not hasattr(exposure, "by_key")
