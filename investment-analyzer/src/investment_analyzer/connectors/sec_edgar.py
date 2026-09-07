"""SEC-EDGAR-Connector (Primärquelle Unternehmensmeldungen, Auftrag §3 Stufe 1).

Öffentliche, kostenlose API der US-Börsenaufsicht (Public Domain). Deckt
zunächst nur US-Emittenten ab — die fehlende gleichwertige Meldungsquelle
für DE/EU ist eine bekannte, dokumentierte Lücke der Kostenlos-Variante
(siehe ``DATA_SOURCES.md``, ``DECISIONS.md`` ADR-9).

Drei Operationen:

- ``resolve_cik_by_ticker``: Ticker → CIK (SEC-interne Kennung), Basis
  für eine stabile ``EntityIdentifier``-Zuordnung (niemals Ticker allein,
  Auftrag §5).
- ``get_submissions``: Firmenname, bekannte Ticker/Börsen, jüngste
  Einreichungen (Formtyp, Datum, Accession Number, Primärdokument-URL).
- ``get_company_concept``: eine einzelne XBRL-Kennzahl (z. B.
  ``Revenues``) über alle gemeldeten Perioden — inkl. Berichtsperiode,
  Einreichungsdatum und Accession Number, also bereits mit vollständiger
  Provenienz im Sinne von Auftrag §5.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

from investment_analyzer.connectors.base import Connector, ConnectorConfig
from investment_analyzer.connectors.cache import FileCache
from investment_analyzer.connectors.errors import ConnectorValidationError
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.ssrf import Resolver

SEC_EDGAR_LICENSE_NOTE = (
    "Public Domain (US-Regierungswerk, SEC EDGAR). Pflicht: aussagekräftiger "
    "User-Agent-Header mit Kontaktadresse. Fair-Access-Policy, empfohlen höchstens "
    "10 Anfragen/Sekunde."
)

#: SEC EDGAR verteilt Daten über zwei Hosts: www.sec.gov (u. a. Ticker-Liste)
#: und data.sec.gov (Submissions-/XBRL-APIs).
ALLOWED_HOSTS = frozenset({"www.sec.gov", "data.sec.gov"})

TICKER_LIST_URL = "https://www.sec.gov/files/company_tickers.json"

#: Die Ticker-Liste ändert sich selten — ein Tag TTL ist unkritisch und schont das Rate-Limit.
TICKER_LIST_CACHE_TTL_SECONDS = 24 * 60 * 60


def build_config(*, contact: str, cache_ttl_seconds: int = 3600) -> ConnectorConfig:
    """Baut die Connector-Konfiguration inkl. Pflicht-User-Agent (Auftrag §4/§12).

    ``contact`` muss eine für die SEC nachvollziehbare Kontaktangabe sein
    (z. B. ``"kontakt@example.com"``) — ohne aussagekräftigen User-Agent
    drosselt/blockiert SEC EDGAR Anfragen.
    """

    if not contact.strip():
        raise ValueError("contact darf nicht leer sein (SEC-EDGAR-Pflichtangabe, DATA_SOURCES.md).")

    return ConnectorConfig(
        key="sec_edgar",
        display_name="SEC EDGAR",
        base_url="https://data.sec.gov",
        allowed_hosts=ALLOWED_HOSTS,
        license_note=SEC_EDGAR_LICENSE_NOTE,
        default_headers={
            "User-Agent": f"InvestmentAnalyzer/0.1 ({contact})",
            "Accept-Encoding": "gzip, deflate",
        },
        cache_ttl_seconds=cache_ttl_seconds,
    )


@dataclass(frozen=True)
class TickerMapping:
    cik: str  # zehnstellig, führende Nullen
    ticker: str
    title: str


@dataclass(frozen=True)
class SecFiling:
    accession_number: str
    form: str
    filing_date: date
    report_date: date | None
    primary_document: str


@dataclass(frozen=True)
class SecSubmissions:
    cik: str
    name: str
    tickers: tuple[str, ...]
    exchanges: tuple[str, ...]
    filings: tuple[SecFiling, ...]
    fetched_at_utc: datetime
    source_url: str
    sic: str | None = None
    sic_description: str | None = None


@dataclass(frozen=True)
class SecConceptFact:
    end_date: date
    value: float
    unit: str
    form: str
    filed_date: date
    accession_number: str
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    start_date: date | None = None


@dataclass(frozen=True)
class SecCompanyConcept:
    cik: str
    taxonomy: str
    tag: str
    label: str | None
    description: str | None
    facts: tuple[SecConceptFact, ...]
    fetched_at_utc: datetime
    source_url: str


class SecEdgarConnector(Connector):
    """Connector für SEC EDGAR (Ticker→CIK, Submissions, XBRL Company Concepts)."""

    def __init__(
        self,
        *,
        contact: str,
        http_client: httpx.Client | None = None,
        cache: FileCache | None = None,
        rate_limiter: RateLimiter | None = None,
        ssrf_resolver: Resolver | None = None,
    ) -> None:
        config = build_config(contact=contact)
        super().__init__(
            config,
            http_client=http_client,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter(10, 1.0),
            ssrf_resolver=ssrf_resolver,
        )

    def resolve_cik_by_ticker(self, ticker: str) -> TickerMapping:
        """Löst einen Ticker über die offizielle SEC-Ticker-Liste zu einer CIK auf."""

        result = self.get_json(TICKER_LIST_URL, cache_ttl_seconds=TICKER_LIST_CACHE_TTL_SECONDS)
        if not isinstance(result.data, dict):
            raise ConnectorValidationError("Unerwartetes Format der SEC-Ticker-Liste (kein Objekt).")

        ticker_upper = ticker.upper()
        for entry in result.data.values():
            if str(entry.get("ticker", "")).upper() == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)
                return TickerMapping(cik=cik, ticker=entry["ticker"], title=entry.get("title", ""))

        raise ConnectorValidationError(
            f"Ticker {ticker!r} wurde in der SEC-Ticker-Liste nicht gefunden."
        )

    def get_submissions(self, cik: str) -> SecSubmissions:
        """Firmenname, Ticker/Börsen und jüngste Einreichungen für eine CIK."""

        cik_padded = cik.zfill(10)
        result = self.get_json(f"/submissions/CIK{cik_padded}.json")
        data = result.data

        try:
            recent = data["filings"]["recent"]
            accession_numbers = recent["accessionNumber"]
            report_dates = recent.get("reportDate", [""] * len(accession_numbers))
            filings = tuple(
                SecFiling(
                    accession_number=accession_number,
                    form=form,
                    filing_date=date.fromisoformat(filing_date),
                    report_date=date.fromisoformat(report_date) if report_date else None,
                    primary_document=primary_document,
                )
                for accession_number, form, filing_date, report_date, primary_document in zip(
                    accession_numbers,
                    recent["form"],
                    recent["filingDate"],
                    report_dates,
                    recent["primaryDocument"],
                    strict=True,
                )
            )
            return SecSubmissions(
                cik=cik_padded,
                name=data["name"],
                tickers=tuple(data.get("tickers", [])),
                exchanges=tuple(data.get("exchanges", [])),
                filings=filings,
                fetched_at_utc=result.fetched_at_utc,
                source_url=result.url,
                sic=data.get("sic") or None,
                sic_description=data.get("sicDescription") or None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorValidationError(
                f"Unerwartetes Submissions-Format für CIK {cik_padded}: {exc}"
            ) from exc

    def get_company_concept(
        self, cik: str, tag: str, *, taxonomy: str = "us-gaap"
    ) -> SecCompanyConcept:
        """Eine einzelne XBRL-Kennzahl (z. B. ``Revenues``) über alle gemeldeten Perioden."""

        cik_padded = cik.zfill(10)
        result = self.get_json(f"/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json")
        data = result.data

        try:
            facts: list[SecConceptFact] = []
            units: dict[str, list[dict[str, Any]]] = data["units"]
            for unit_name, entries in units.items():
                for entry in entries:
                    facts.append(
                        SecConceptFact(
                            end_date=date.fromisoformat(entry["end"]),
                            start_date=date.fromisoformat(entry["start"]) if entry.get("start") else None,
                            value=float(entry["val"]),
                            unit=unit_name,
                            fiscal_year=entry.get("fy"),
                            fiscal_period=entry.get("fp"),
                            form=entry["form"],
                            filed_date=date.fromisoformat(entry["filed"]),
                            accession_number=entry["accn"],
                        )
                    )
            return SecCompanyConcept(
                cik=cik_padded,
                taxonomy=taxonomy,
                tag=tag,
                label=data.get("label"),
                description=data.get("description"),
                facts=tuple(facts),
                fetched_at_utc=result.fetched_at_utc,
                source_url=result.url,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorValidationError(
                f"Unerwartetes CompanyConcept-Format für CIK {cik_padded}/{tag}: {exc}"
            ) from exc
