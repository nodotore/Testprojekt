"""``ReportBundle``: eine einzige Quelle der Wahrheit für alle Exportformate
(Auftrag §10: „Export nach Excel enthält Tabellenblätter Zusammenfassung,
Kennzahlen, Bewertung, Risiken, Nachrichten, Quellen und Annahmen").

Aggregiert die bereits an anderer Stelle deterministisch berechneten
Berichte (``FundamentalsReport``, ``ValuationReport``, ``ScoreResult``,
``NewsReport``) zu einem einzigen, unveränderlichen Objekt. JSON-,
Excel- und PDF-Export (siehe ``json_export.py``, ``excel_export.py``,
``pdf_export.py``) lesen ausschließlich aus diesem Objekt — dadurch
können zwei Exportformate für dieselbe Analyse nie unterschiedliche
Werte zeigen. Eine künftige UI-Detailseite (Milestone 8+) MUSS ebenfalls
von einem ``ReportBundle`` rendern, nicht von eigenen Anfragen, damit
das Auftrag-§10-Abnahmekriterium „Export enthält exakt dieselben Werte
wie die UI-Ansicht" strukturell erfüllt bleibt (siehe ``DECISIONS.md``
ADR-21).

Dieses Modul erzeugt selbst KEINE neuen Zahlen — reine Aggregation
bereits unabhängig getesteter Berichte.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from investment_analyzer.connectors.models import Source
from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.report import FundamentalsReport, build_fundamentals_report
from investment_analyzer.news.report import NewsReport, build_news_report
from investment_analyzer.scoring.score import ScoreResult, compute_score
from investment_analyzer.valuation.report import ValuationReport, build_valuation_report


@dataclass(frozen=True)
class ReportHeader:
    """Auftrag §10: „Jeder Bericht zeigt oben: Datenstand, Analysezeit,
    Marktdatenverzögerung, Datenabdeckung und Konfidenz."

    ``market_data_delay_note`` ist eine feste Formulierung statt einer
    gemessenen Verzögerung — es gibt keinen Streaming-Marktdaten-Feed in
    dieser Version (Alpha-Vantage-Snapshots, siehe DATA_SOURCES.md), die
    tatsächliche Verzögerung ist daher unbekannt und wird nicht
    vorgetäuscht.
    """

    entity_id: str
    entity_name: str
    as_of: datetime
    generated_at_utc: datetime
    data_completeness: float
    score_coverage: float
    score_classification: str
    market_data_delay_note: str


@dataclass(frozen=True)
class SourceInfo:
    key: str
    display_name: str
    license_note: str


@dataclass(frozen=True)
class ReportBundle:
    header: ReportHeader
    fundamentals: FundamentalsReport
    valuation: ValuationReport
    score: ScoreResult
    news: NewsReport
    sources: tuple[SourceInfo, ...]
    assumptions: tuple[str, ...]


_MARKET_DATA_DELAY_NOTE = (
    "Kein Streaming-Marktdaten-Feed angebunden — Kurse sind Einzelabruf-"
    "Snapshots (Alpha Vantage GLOBAL_QUOTE), tatsächliche Verzögerung zum "
    "Live-Markt ist nicht gemessen und wird hier nicht vorgetäuscht."
)


def _collect_assumptions(fundamentals: FundamentalsReport, valuation: ValuationReport) -> tuple[str, ...]:
    """Sammelt jede im Bericht verwendete Annahme als lesbaren Satz (Auftrag §1/§11)."""

    notes: list[str] = [
        f"ROIC-Steuersatz: {fundamentals.returns.roic_tax_rate_assumption:.1%} "
        "(Annahme, kein gemeldeter Steuersatz)."
    ]
    for name, result in sorted(valuation.dcf_scenarios.items()):
        a = result.assumptions
        notes.append(
            f"DCF-Szenario '{name}': Umsatzwachstum {a.revenue_growth_rate:+.1%}, "
            f"FCF-Marge {a.fcf_margin:.1%}, WACC {a.wacc:.1%}, "
            f"Terminalwachstum {a.terminal_growth_rate:.1%} "
            f"(Annahmen, nicht garantiert)."
        )
    notes.extend(valuation.missing_data_notes)
    return tuple(notes)


def build_report_bundle(
    session: Session, entity: Entity, *, as_of: datetime | None = None
) -> ReportBundle:
    """Baut ein vollständiges ``ReportBundle`` für ``entity``.

    Ruft ``FundamentalsReport``/``ValuationReport`` genau EINMAL auf und
    übergibt dieselben Instanzen an ``compute_score`` — vermeidet
    doppelte Berechnung UND garantiert, dass Score und Einzelberichte
    exakt dieselben zugrunde liegenden Werte referenzieren.
    """

    reference = as_of or utc_now()

    fundamentals = build_fundamentals_report(session, entity, as_of=reference)
    valuation = build_valuation_report(session, entity, as_of=reference)
    score = compute_score(fundamentals, valuation)
    news = build_news_report(session, entity)

    sources = tuple(
        SourceInfo(key=row.key, display_name=row.display_name, license_note=row.license_note)
        for row in session.scalars(select(Source).order_by(Source.key)).all()
    )

    header = ReportHeader(
        entity_id=entity.id,
        entity_name=entity.name,
        as_of=reference,
        generated_at_utc=utc_now(),
        data_completeness=fundamentals.data_completeness,
        score_coverage=score.coverage,
        score_classification=score.classification,
        market_data_delay_note=_MARKET_DATA_DELAY_NOTE,
    )

    return ReportBundle(
        header=header,
        fundamentals=fundamentals,
        valuation=valuation,
        score=score,
        news=news,
        sources=sources,
        assumptions=_collect_assumptions(fundamentals, valuation),
    )
