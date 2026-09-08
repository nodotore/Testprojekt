from __future__ import annotations

from unittest.mock import patch

from investment_analyzer.news.sanitize import _TextExtractor, sanitize_html_to_text


def test_none_und_leerer_input_liefert_none() -> None:
    assert sanitize_html_to_text(None) is None
    assert sanitize_html_to_text("") is None
    assert sanitize_html_to_text("   \n\t  ") is None


def test_einfaches_html_wird_zu_klartext() -> None:
    result = sanitize_html_to_text("<p>Firma E hat heute <b>Rekordzahlen</b> vorgelegt.</p>")
    assert result == "Firma E hat heute Rekordzahlen vorgelegt."


def test_script_und_style_inhalte_werden_verworfen() -> None:
    raw = "<div>Text<script>alert('x')</script> danach<style>.x{color:red}</style> Ende</div>"
    result = sanitize_html_to_text(raw)
    assert "alert" not in (result or "")
    assert "color:red" not in (result or "")
    assert "Text" in (result or "")
    assert "Ende" in (result or "")


def test_html_entities_werden_aufgeloest() -> None:
    result = sanitize_html_to_text("Umsatz &amp; Gewinn &gt; Erwartung")
    assert result == "Umsatz & Gewinn > Erwartung"


def test_ueberschuessiger_leerraum_wird_kollabiert() -> None:
    result = sanitize_html_to_text("Zeile eins\n\n   Zeile   zwei")
    assert result == "Zeile eins Zeile zwei"


def test_lange_texte_werden_gekuerzt_mit_ellipse() -> None:
    long_text = "Wort " * 1000
    result = sanitize_html_to_text(long_text, max_length=50)
    assert result is not None
    assert len(result) <= 51
    assert result.endswith("…")


def test_kaputtes_html_bricht_nicht_ab() -> None:
    result = sanitize_html_to_text("<div><p>Nicht geschlossen")
    assert result is not None
    assert "Nicht geschlossen" in result


def test_verschachtelte_escaped_markup_wird_nicht_erneut_ausgefuehrt() -> None:
    # Doppelt kodiertes Markup (z. B. aus einem CMS-Export) bleibt als
    # Literaltext erhalten statt als Tag interpretiert zu werden — kein
    # zweiter Parse-Durchlauf (Sicherheitsrelevanz: kein Bypass-Risiko).
    result = sanitize_html_to_text("&lt;script&gt;alert(1)&lt;/script&gt;")
    assert result == "<script>alert(1)</script>"


def test_ausnahme_im_parser_laesst_kein_rohes_markup_durch() -> None:
    """Regressionstest (Milestone-8-Security-Review, unabhängige Prüfung,
    siehe DECISIONS.md ADR-25): löst ``HTMLParser`` selbst eine Ausnahme
    aus (im Normalbetrieb praktisch nie der Fall), darf NICHT der
    unveränderte Rohtext zurückgegeben werden -- das widerspräche der
    Modul-Zusicherung „kein Markup bleibt erhalten". Der Regex-Fallback
    muss zumindest Tags entfernen."""

    with patch.object(_TextExtractor, "feed", side_effect=RuntimeError("simulierter Parser-Absturz")):
        result = sanitize_html_to_text("<div>Text<script>alert('x')</script> Ende</div>")

    assert result is not None
    assert "<script>" not in result
    assert "<div>" not in result
    assert "Text" in result
    assert "Ende" in result
