"""Idempotentes Anlegen/Aktualisieren der bekannten ``Source``-Zeilen.

Jede in ``DATA_SOURCES.md`` dokumentierte, tatsächlich angebundene
Quelle bekommt hierüber eine feste Zeile in der Datenbank (Basis-URL,
Lizenzhinweis) — referenziert von jedem ``DataPoint`` (Auftrag §5).
Wird bei jedem Programmstart/Connector-Einsatz aufgerufen; ändert sich
z. B. der Lizenzhinweistext im Code, wird die bestehende Zeile
aktualisiert statt dupliziert.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.connectors.alpha_vantage import ALPHA_VANTAGE_LICENSE_NOTE
from investment_analyzer.connectors.alpha_vantage import BASE_URL as ALPHA_VANTAGE_BASE_URL
from investment_analyzer.connectors.gdelt import BASE_URL as GDELT_BASE_URL
from investment_analyzer.connectors.gdelt import GDELT_LICENSE_NOTE
from investment_analyzer.connectors.ir_rss import IR_RSS_LICENSE_NOTE
from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.sec_edgar import SEC_EDGAR_LICENSE_NOTE

#: data.sec.gov ist die Basis-URL für Submissions-/XBRL-Endpunkte (siehe sec_edgar.py).
SEC_EDGAR_BASE_URL = "https://data.sec.gov"

#: IR-RSS hat keine einzelne Basis-URL (je Emittent ein eigener Host,
#: siehe connectors/ir_rss.py) — die Source-Zeile dokumentiert das Verfahren,
#: nicht einen konkreten Host; die tatsächliche Feed-URL steht je Treffer in
#: ``NewsItem.url``.
IR_RSS_BASE_URL = ""

_KNOWN_SOURCES: tuple[dict[str, str], ...] = (
    {
        "key": "sec_edgar",
        "display_name": "SEC EDGAR",
        "base_url": SEC_EDGAR_BASE_URL,
        "license_note": SEC_EDGAR_LICENSE_NOTE,
    },
    {
        "key": "alpha_vantage",
        "display_name": "Alpha Vantage",
        "base_url": ALPHA_VANTAGE_BASE_URL,
        "license_note": ALPHA_VANTAGE_LICENSE_NOTE,
    },
    {
        "key": "gdelt",
        "display_name": "GDELT Project",
        "base_url": GDELT_BASE_URL,
        "license_note": GDELT_LICENSE_NOTE,
    },
    {
        "key": "ir_rss",
        "display_name": "Investor-Relations-RSS (diverse Hosts)",
        "base_url": IR_RSS_BASE_URL,
        "license_note": IR_RSS_LICENSE_NOTE,
    },
)


def ensure_default_sources(session: Session) -> dict[str, Source]:
    """Legt die bekannten Source-Zeilen an bzw. aktualisiert sie; liefert sie nach Key indiziert."""

    sources: dict[str, Source] = {}
    for spec in _KNOWN_SOURCES:
        existing = session.scalars(select(Source).where(Source.key == spec["key"])).first()
        if existing is None:
            existing = Source(
                key=spec["key"],
                display_name=spec["display_name"],
                base_url=spec["base_url"],
                license_note=spec["license_note"],
            )
            session.add(existing)
            session.flush()
        else:
            existing.display_name = spec["display_name"]
            existing.base_url = spec["base_url"]
            existing.license_note = spec["license_note"]
        sources[spec["key"]] = existing
    return sources
