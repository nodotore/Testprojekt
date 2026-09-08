from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.ir_rss import IrRssConnector, build_config, parse_feed

RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Firma E Investor Relations</title>
    <item>
      <title>Firma E meldet Quartalszahlen</title>
      <link>https://ir.firma-e.test/news/quartalszahlen</link>
      <pubDate>Mon, 02 Mar 2026 15:04:05 GMT</pubDate>
      <description>&lt;p&gt;Firma E hat heute die Zahlen fuer Q1 vorgelegt.&lt;/p&gt;</description>
    </item>
    <item>
      <title>Ohne Link wird uebersprungen</title>
      <pubDate>Mon, 02 Mar 2026 15:04:05 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Firma E Pressemitteilungen</title>
  <entry>
    <title>Firma E kuendigt Partnerschaft an</title>
    <link href="https://ir.firma-e.test/news/partnerschaft" />
    <published>2026-03-01T09:00:00Z</published>
    <summary>Kurze Zusammenfassung der Partnerschaft.</summary>
  </entry>
</feed>
"""


def _public_ip_resolver(host: str, port: int | None):
    return [(2, 1, 6, "", ("104.18.10.1", port or 443))]


def _connector(feed_url: str, handler, *, cache_dir: Path | None = None) -> IrRssConnector:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    cache = FileCache(cache_dir) if cache_dir is not None else None
    return IrRssConnector(feed_url, http_client=client, cache=cache, ssrf_resolver=_public_ip_resolver)


def test_build_config_leitet_allowlist_aus_feed_url_ab() -> None:
    config = build_config("https://ir.firma-e.test/rss.xml")
    assert config.allowed_hosts == frozenset({"ir.firma-e.test"})
    assert config.key == "ir_rss:ir.firma-e.test"


def test_feed_url_ohne_host_wird_abgelehnt() -> None:
    with pytest.raises(ValueError, match="Hostnamen"):
        build_config("not-a-url")


def test_parse_feed_rss20() -> None:
    items = parse_feed(RSS_FEED)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Firma E meldet Quartalszahlen"
    assert item.url == "https://ir.firma-e.test/news/quartalszahlen"
    assert item.published_at is not None
    assert item.published_at.isoformat() == "2026-03-02T15:04:05+00:00"
    assert "Q1" in (item.summary_html or "")


def test_parse_feed_atom() -> None:
    items = parse_feed(ATOM_FEED)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Firma E kuendigt Partnerschaft an"
    assert item.url == "https://ir.firma-e.test/news/partnerschaft"
    assert item.published_at is not None
    assert item.published_at.isoformat() == "2026-03-01T09:00:00+00:00"


def test_parse_feed_kaputtes_xml_wirft_validierungsfehler() -> None:
    with pytest.raises(ConnectorValidationError, match="XML"):
        parse_feed("<rss><channel>")


def test_parse_feed_unbekanntes_root_element_wirft_validierungsfehler() -> None:
    with pytest.raises(ConnectorValidationError, match="Root-Element"):
        parse_feed("<html><body>Keine Feed-Datei</body></html>")


def test_parse_feed_lehnt_billion_laughs_angriff_ab() -> None:
    """Milestone-8-Ausfalltest (manipulierte Webinhalte): ein böswilliger IR-
    Feed-Betreiber könnte eine winzige XML-Payload mit rekursiver Entity-
    Expansion senden ("Billion Laughs"), die beim Parsen mehrere Gigabyte
    Speicher belegt. Die HTTP-Größenobergrenze (ConnectorConfig.
    max_response_bytes) schützt davor NICHT, da die Payload selbst winzig
    ist -- der Angriff entsteht erst beim XML-Parsen. ``defusedxml`` lehnt
    Entity-Definitionen grundsätzlich ab, statt sie zu expandieren."""

    billion_laughs = (
        '<?xml version="1.0"?>'
        "<!DOCTYPE rss ["
        '<!ENTITY lol "lol">'
        '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
        '<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">'
        "]>"
        "<rss><channel><item><title>&lol3;</title>"
        "<link>https://evil.test/x</link></item></channel></rss>"
    )
    with pytest.raises(ConnectorValidationError, match="nicht erlaubte XML-Konstrukte"):
        parse_feed(billion_laughs)


def test_fetch_feed_ruft_ueber_https_ab_und_parst() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "ir.firma-e.test"
        return httpx.Response(200, text=RSS_FEED, headers={"content-type": "application/rss+xml"})

    connector = _connector("https://ir.firma-e.test/rss.xml", handler)
    feed = connector.fetch_feed()

    assert len(feed.items) == 1
    assert feed.items[0].url == "https://ir.firma-e.test/news/quartalszahlen"
    assert feed.source_url == "https://ir.firma-e.test/rss.xml"


def test_fetch_feed_cached_landet_nicht_doppelt_im_netzwerk(tmp_path: Path) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, text=RSS_FEED)

    connector = _connector("https://ir.firma-e.test/rss.xml", handler, cache_dir=tmp_path)
    connector.fetch_feed()
    connector.fetch_feed()

    assert calls["count"] == 1
