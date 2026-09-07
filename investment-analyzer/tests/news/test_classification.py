from __future__ import annotations

from investment_analyzer.news.classification import classify_event_type, classify_source_category
from investment_analyzer.news.models import NewsEventType, NewsSourceCategory


def test_ir_rss_ist_immer_unternehmensmeldung() -> None:
    category = classify_source_category(source_key="ir_rss", domain="ir.firma-e.test")
    assert category == NewsSourceCategory.UNTERNEHMENSMELDUNG


def test_gdelt_ohne_bekannte_kommentar_domain_ist_unabhaengiger_bericht() -> None:
    category = classify_source_category(source_key="gdelt", domain="reuters.test")
    assert category == NewsSourceCategory.UNABHAENGIGER_BERICHT


def test_gdelt_mit_bekannter_kommentar_domain_ist_kommentar() -> None:
    category = classify_source_category(source_key="gdelt", domain="seekingalpha.com")
    assert category == NewsSourceCategory.KOMMENTAR


def test_domain_gross_kleinschreibung_wird_ignoriert() -> None:
    category = classify_source_category(source_key="gdelt", domain="SeekingAlpha.com")
    assert category == NewsSourceCategory.KOMMENTAR


def test_fehlende_domain_ist_unabhaengiger_bericht() -> None:
    category = classify_source_category(source_key="gdelt", domain=None)
    assert category == NewsSourceCategory.UNABHAENGIGER_BERICHT


def test_earnings_keyword_wird_erkannt() -> None:
    assert classify_event_type("Firma E: Quartalszahlen übertreffen Erwartungen") == (
        NewsEventType.EARNINGS
    )


def test_merger_keyword_wird_erkannt() -> None:
    assert classify_event_type("Firma E announces acquisition of Rival Corp") == (
        NewsEventType.MERGER_ACQUISITION
    )


def test_management_keyword_wird_erkannt() -> None:
    assert classify_event_type("Vorstandsvorsitzender kündigt Rücktritt an") == (
        NewsEventType.MANAGEMENT
    )


def test_legal_keyword_wird_erkannt() -> None:
    assert classify_event_type("Regulator opens investigation into Firma E") == (
        NewsEventType.LEGAL_REGULATORY
    )


def test_cyber_keyword_wird_erkannt() -> None:
    assert classify_event_type("Firma E confirms data breach affecting customers") == (
        NewsEventType.CYBER_SUPPLY_CHAIN
    )


def test_capital_markets_keyword_wird_erkannt() -> None:
    assert classify_event_type("Firma E kündigt Aktienrückkauf an") == (
        NewsEventType.CAPITAL_MARKETS
    )


def test_product_keyword_wird_erkannt() -> None:
    assert classify_event_type("Firma E announces new product launch") == (
        NewsEventType.PRODUCT_OPERATIONS
    )


def test_ohne_treffer_ist_sonstiges() -> None:
    assert classify_event_type("Firma E eröffnet neues Bürogebäude") == NewsEventType.SONSTIGES


def test_summary_wird_mit_durchsucht() -> None:
    result = classify_event_type("Kurzmeldung", summary="Details zur geplanten Fusion mit Wettbewerber.")
    assert result == NewsEventType.MERGER_ACQUISITION


def test_erste_passende_kategorie_in_prioritaetsreihenfolge_gewinnt() -> None:
    # Enthält sowohl ein Earnings- als auch ein Merger-Schlüsselwort —
    # Merger steht in der Prioritätsliste zuerst.
    result = classify_event_type("Fusion und Quartalszahlen in einer Meldung")
    assert result == NewsEventType.MERGER_ACQUISITION
