from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from investment_analyzer.connectors.cache import CacheEntry, FileCache, cache_key_for


def test_cache_key_ist_deterministisch_und_ordnungsunabhaengig() -> None:
    k1 = cache_key_for("https://example.invalid/a", {"x": 1, "y": 2})
    k2 = cache_key_for("https://example.invalid/a", {"y": 2, "x": 1})
    k3 = cache_key_for("https://example.invalid/a", {"x": 1, "y": 3})
    assert k1 == k2
    assert k1 != k3


def test_get_ohne_vorhandenen_eintrag_liefert_none(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    assert cache.get("sec_edgar", "irgendein-key") is None


def test_set_und_get_roundtrip(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    now = datetime.now(UTC)
    entry = CacheEntry(data={"foo": "bar"}, fetched_at_utc=now, ttl_seconds=3600, status_code=200)

    cache.set("sec_edgar", "key1", entry)
    geladen = cache.get("sec_edgar", "key1")

    assert geladen is not None
    assert geladen.data == {"foo": "bar"}
    assert geladen.status_code == 200


def test_abgelaufener_eintrag_wird_nie_als_gueltig_zurueckgegeben(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    laengst_abgelaufen = datetime.now(UTC) - timedelta(hours=10)
    entry = CacheEntry(data="alt", fetched_at_utc=laengst_abgelaufen, ttl_seconds=60, status_code=200)

    cache.set("sec_edgar", "key2", entry)

    assert cache.get("sec_edgar", "key2") is None


def test_korrupte_cache_datei_wird_wie_nicht_vorhanden_behandelt(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    path = tmp_path / "sec_edgar" / "kaputt.json"
    path.parent.mkdir(parents=True)
    path.write_text("{ das ist kein gueltiges JSON", encoding="utf-8")

    assert cache.get("sec_edgar", "kaputt") is None


def test_cache_entry_is_fresh_grenzfaelle() -> None:
    now = datetime.now(UTC)
    entry = CacheEntry(data=1, fetched_at_utc=now - timedelta(seconds=59), ttl_seconds=60, status_code=200)
    assert entry.is_fresh(now=now) is True

    abgelaufen = CacheEntry(data=1, fetched_at_utc=now - timedelta(seconds=61), ttl_seconds=60, status_code=200)
    assert abgelaufen.is_fresh(now=now) is False
