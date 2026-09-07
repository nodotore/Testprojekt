"""Erklärbares Scoring (Auftrag §7).

Kombiniert ``FundamentalsReport`` (Milestone 3) und ``ValuationReport``
(Milestone 4) zu einem transparenten, deterministischen Gesamtscore
0–100. **Kein Sprachmodell entscheidet über den Score** — jede
Teilkennzahl wird über eine dokumentierte, feste lineare Skala
abgebildet (``_linear_score``); die KI darf das Ergebnis später nur
zusammenfassen (Auftrag §8a).

Zwei der acht Startgewichtungs-Komponenten aus Auftrag §7
(„Wettbewerbsvorteil", „Nachrichten und Katalysatoren") sind in
Milestone 4 strukturell nicht berechenbar — es gibt weder ein
Geschäftsmodell-/Wettbewerbs- noch ein Nachrichtenmodul (folgt in
späteren Milestones). Sie werden **nicht** mit 0 bewertet (das wäre
eine unfaire Abwertung), sondern explizit als nicht verfügbar markiert
und aus der Gewichtssumme ausgeschlossen — ``coverage`` macht sichtbar,
welcher Anteil der Startgewichtung tatsächlich in den Score eingeflossen
ist (Auftrag §7: „Fehlende Daten dürfen nicht neutral mit null bewertet
werden; sie reduzieren die Konfidenz").

Risiken (aus ``risk/warning_signals.py``) wirken als sichtbare,
nachvollziehbare Abzüge nach der gewichteten Durchschnittsbildung, nie
als verstecktes Malus-Feld.

Verbotene Formulierungen laut Auftrag §7 („sicherer Kauf",
„garantierter Gewinn") werden in keinem hier erzeugten Text verwendet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from investment_analyzer.db.types import utc_now
from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals.report import FundamentalsReport, build_fundamentals_report
from investment_analyzer.risk.warning_signals import WarningSignal
from investment_analyzer.valuation.report import ValuationReport, build_valuation_report

KLASSE_VERTIEFT_PRUEFEN = "Vertieft prüfen"
KLASSE_BEOBACHTEN = "Beobachten"
KLASSE_DERZEIT_UNATTRAKTIV = "Derzeit unattraktiv"
KLASSE_DATENLAGE_UNZUREICHEND = "Datenlage unzureichend"

#: Startgewichtung exakt gemäß Auftrag §7 (Summe = 100).
DEFAULT_WEIGHTS: dict[str, float] = {
    "finanzqualitaet": 25.0,
    "bewertung_sicherheitsmarge": 20.0,
    "wachstum_bestaendigkeit": 15.0,
    "bilanzstaerke": 15.0,
    "wettbewerbsvorteil": 10.0,
    "management_kapitalallokation": 5.0,
    "nachrichten_katalysatoren": 5.0,
    "datenqualitaet_aktualitaet": 5.0,
}

_COMPONENT_LABELS: dict[str, str] = {
    "finanzqualitaet": "Finanzqualität",
    "bewertung_sicherheitsmarge": "Bewertung/Sicherheitsmarge",
    "wachstum_bestaendigkeit": "Wachstum und Beständigkeit",
    "bilanzstaerke": "Bilanzstärke",
    "wettbewerbsvorteil": "Wettbewerbsvorteil",
    "management_kapitalallokation": "Management/Kapitalallokation",
    "nachrichten_katalysatoren": "Nachrichten und Katalysatoren",
    "datenqualitaet_aktualitaet": "Datenqualität/Aktualität",
}

#: In Milestone 4 strukturell nicht berechenbar (kein Wettbewerbs-/Nachrichtenmodul).
NOT_YET_IMPLEMENTABLE_COMPONENTS: tuple[str, ...] = (
    "wettbewerbsvorteil",
    "nachrichten_katalysatoren",
)

RISK_DEDUCTION_POINTS: dict[str, float] = {"hoch": 10.0, "mittel": 5.0, "niedrig": 2.0}

# Konfidenzschwellen (Auftrag §7: unterhalb definierter Schwellen -> Beobachten/Datenlage unzureichend).
MIN_COVERAGE_DATENLAGE_UNZUREICHEND = 0.5
MIN_COVERAGE_VERTIEFT_PRUEFEN = 0.7
MIN_DATA_COMPLETENESS_DATENLAGE_UNZUREICHEND = 0.3
SCORE_THRESHOLD_VERTIEFT_PRUEFEN = 70.0
SCORE_THRESHOLD_BEOBACHTEN = 50.0


def _linear_score(value: float, low: float, high: float) -> float:
    """Bildet ``value`` linear auf [0, 100] ab; ``low`` -> 0, ``high`` -> 100 (Werte außerhalb gekappt).

    ``low`` darf größer als ``high`` sein, um „niedriger ist besser"-
    Kennzahlen (z. B. Verschuldungsgrad) abzubilden.
    """

    if high == low:
        return 50.0
    fraction = (value - low) / (high - low)
    return max(0.0, min(100.0, fraction * 100.0))


@dataclass(frozen=True)
class MetricNote:
    label: str
    formatted_value: str
    score: float
    component: str


@dataclass(frozen=True)
class ComponentScore:
    name: str
    label: str
    weight: float
    score: float | None
    notes: tuple[MetricNote, ...]


@dataclass(frozen=True)
class RiskDeduction:
    code: str
    severity: str
    points: float
    description: str


@dataclass(frozen=True)
class ScoreResult:
    entity_id: str
    entity_name: str
    generated_at_utc: datetime
    as_of: datetime

    components: tuple[ComponentScore, ...]
    coverage: float
    raw_score: float | None
    risk_deductions: tuple[RiskDeduction, ...]
    total_score: float | None
    classification: str

    top_positive_factors: tuple[str, ...]
    top_risks: tuple[str, ...]
    counterarguments: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]

    not_yet_implementable_components: tuple[str, ...]


def _score_finanzqualitaet(fr: FundamentalsReport) -> tuple[float | None, list[MetricNote]]:
    notes: list[MetricNote] = []
    scores: list[float] = []

    if fr.margins.net_margin is not None:
        s = _linear_score(fr.margins.net_margin, 0.0, 0.20)
        scores.append(s)
        notes.append(MetricNote("Nettomarge", f"{fr.margins.net_margin:.1%}", s, "finanzqualitaet"))
    if fr.margins.gross_margin is not None:
        s = _linear_score(fr.margins.gross_margin, 0.20, 0.60)
        scores.append(s)
        notes.append(MetricNote("Bruttomarge", f"{fr.margins.gross_margin:.1%}", s, "finanzqualitaet"))
    if fr.margins.operating_margin is not None:
        s = _linear_score(fr.margins.operating_margin, 0.05, 0.25)
        scores.append(s)
        notes.append(MetricNote("operative Marge", f"{fr.margins.operating_margin:.1%}", s, "finanzqualitaet"))
    if fr.margins.net_margin_stability is not None:
        s = _linear_score(fr.margins.net_margin_stability, 0.10, 0.0)
        scores.append(s)
        notes.append(
            MetricNote(
                "Margenstabilität (Nettomarge)", f"σ={fr.margins.net_margin_stability:.3f}", s, "finanzqualitaet"
            )
        )
    if fr.returns.return_on_equity is not None:
        s = _linear_score(fr.returns.return_on_equity, 0.0, 0.25)
        scores.append(s)
        notes.append(
            MetricNote("Eigenkapitalrendite (ROE)", f"{fr.returns.return_on_equity:.1%}", s, "finanzqualitaet")
        )
    if fr.returns.return_on_invested_capital is not None:
        s = _linear_score(fr.returns.return_on_invested_capital, 0.0, 0.20)
        scores.append(s)
        notes.append(
            MetricNote(
                "Kapitalrendite (ROIC)", f"{fr.returns.return_on_invested_capital:.1%}", s, "finanzqualitaet"
            )
        )
    if fr.cashflow.cash_conversion is not None:
        s = _linear_score(fr.cashflow.cash_conversion, 0.3, 1.1)
        scores.append(s)
        notes.append(MetricNote("Cash Conversion", f"{fr.cashflow.cash_conversion:.2f}", s, "finanzqualitaet"))

    if not scores:
        return None, []
    return sum(scores) / len(scores), notes


def _score_bewertung(vr: ValuationReport) -> tuple[float | None, list[MetricNote]]:
    if vr.safety_margin is None:
        return None, []
    s = _linear_score(vr.safety_margin, -0.20, 0.40)
    note = MetricNote(
        "Sicherheitsmarge (DCF, unteres Band)", f"{vr.safety_margin:+.1%}", s, "bewertung_sicherheitsmarge"
    )
    return s, [note]


def _score_wachstum(fr: FundamentalsReport) -> tuple[float | None, list[MetricNote]]:
    notes: list[MetricNote] = []
    scores: list[float] = []

    revenue_growth = fr.revenue_growth.horizon_3y
    revenue_horizon = "3 Jahre"
    if revenue_growth is None:
        revenue_growth = fr.revenue_growth.horizon_1y
        revenue_horizon = "1 Jahr"
    if revenue_growth is not None:
        s = _linear_score(revenue_growth, -0.05, 0.15)
        scores.append(s)
        notes.append(
            MetricNote(f"Umsatzwachstum ({revenue_horizon})", f"{revenue_growth:+.1%}", s, "wachstum_bestaendigkeit")
        )

    net_income_growth = fr.net_income_growth.horizon_3y
    ni_horizon = "3 Jahre"
    if net_income_growth is None:
        net_income_growth = fr.net_income_growth.horizon_1y
        ni_horizon = "1 Jahr"
    if net_income_growth is not None:
        s = _linear_score(net_income_growth, -0.10, 0.20)
        scores.append(s)
        notes.append(
            MetricNote(f"Gewinnwachstum ({ni_horizon})", f"{net_income_growth:+.1%}", s, "wachstum_bestaendigkeit")
        )

    if fr.revenue_growth.horizon_1y is not None and fr.revenue_growth.horizon_3y is not None:
        konsistent = (fr.revenue_growth.horizon_1y >= 0) == (fr.revenue_growth.horizon_3y >= 0)
        s = 100.0 if konsistent else 30.0
        scores.append(s)
        notes.append(
            MetricNote(
                "Wachstumsbeständigkeit (1J vs. 3J Richtung)",
                "konsistent" if konsistent else "uneinheitlich",
                s,
                "wachstum_bestaendigkeit",
            )
        )

    if not scores:
        return None, []
    return sum(scores) / len(scores), notes


def _score_bilanzstaerke(fr: FundamentalsReport) -> tuple[float | None, list[MetricNote]]:
    notes: list[MetricNote] = []
    scores: list[float] = []

    if fr.leverage.net_debt_to_ebitda is not None:
        s = _linear_score(fr.leverage.net_debt_to_ebitda, 6.0, 0.0)
        scores.append(s)
        notes.append(
            MetricNote("Nettoverschuldung/EBITDA", f"{fr.leverage.net_debt_to_ebitda:.2f}x", s, "bilanzstaerke")
        )
    if fr.leverage.interest_coverage is not None:
        s = _linear_score(fr.leverage.interest_coverage, 1.0, 10.0)
        scores.append(s)
        notes.append(MetricNote("Zinsdeckung", f"{fr.leverage.interest_coverage:.1f}x", s, "bilanzstaerke"))
    if fr.cashflow.working_capital is not None:
        s = 100.0 if fr.cashflow.working_capital > 0 else 30.0
        scores.append(s)
        notes.append(MetricNote("Working Capital", f"{fr.cashflow.working_capital:,.0f}", s, "bilanzstaerke"))

    if not scores:
        return None, []
    return sum(scores) / len(scores), notes


def _score_management(fr: FundamentalsReport) -> tuple[float | None, list[MetricNote]]:
    """Nur anhand von Aktienverwässerung — keine vollständige Management-Bewertung.

    Insidertransaktionen und Vergütungsdaten sind nicht Teil dieses
    Datenmodells (Auftrag §6 nennt sie explizit, aber keine angebundene
    Quelle liefert sie strukturiert) — dieser Teilscore ist bewusst
    schmal und wird in Gegenargumenten entsprechend gekennzeichnet.
    """

    dilution = fr.shareholder.shares_diluted_growth.horizon_3y
    if dilution is None:
        dilution = fr.shareholder.shares_diluted_growth.horizon_1y
    if dilution is None:
        return None, []
    s = _linear_score(dilution, 0.05, -0.02)
    note = MetricNote("Aktienverwässerung", f"{dilution:+.1%} p. a.", s, "management_kapitalallokation")
    return s, [note]


def _score_datenqualitaet(fr: FundamentalsReport) -> tuple[float | None, list[MetricNote]]:
    s = fr.data_completeness * 100.0
    note = MetricNote(
        "Datenvollständigkeit (Fundamentaldaten)", f"{fr.data_completeness:.0%}", s, "datenqualitaet_aktualitaet"
    )
    return s, [note]


def _classify(*, total_score: float | None, coverage: float, data_completeness: float) -> str:
    if total_score is None:
        return KLASSE_DATENLAGE_UNZUREICHEND
    if coverage < MIN_COVERAGE_DATENLAGE_UNZUREICHEND:
        return KLASSE_DATENLAGE_UNZUREICHEND
    if data_completeness < MIN_DATA_COMPLETENESS_DATENLAGE_UNZUREICHEND:
        return KLASSE_DATENLAGE_UNZUREICHEND
    if total_score >= SCORE_THRESHOLD_VERTIEFT_PRUEFEN:
        if coverage < MIN_COVERAGE_VERTIEFT_PRUEFEN:
            return KLASSE_BEOBACHTEN
        return KLASSE_VERTIEFT_PRUEFEN
    if total_score >= SCORE_THRESHOLD_BEOBACHTEN:
        return KLASSE_BEOBACHTEN
    return KLASSE_DERZEIT_UNATTRAKTIV


def _top_positive_factors(notes: list[MetricNote]) -> tuple[str, ...]:
    starke = sorted((n for n in notes if n.score >= 70), key=lambda n: n.score, reverse=True)
    return tuple(f"{n.label}: {n.formatted_value} (Teilscore {n.score:.0f}/100)" for n in starke[:5])


def _top_risks(signals: tuple[WarningSignal, ...], notes: list[MetricNote]) -> tuple[str, ...]:
    ergebnisse = [
        f"{s.description} ({s.evidence})"
        for s in sorted(signals, key=lambda s: RISK_DEDUCTION_POINTS.get(s.severity, 0.0), reverse=True)
    ]
    if len(ergebnisse) < 5:
        schwache = sorted((n for n in notes if n.score <= 30), key=lambda n: n.score)
        for n in schwache:
            ergebnisse.append(f"{n.label}: {n.formatted_value} (Teilscore {n.score:.0f}/100)")
            if len(ergebnisse) >= 5:
                break
    return tuple(ergebnisse[:5])


def _counterarguments(components: tuple[ComponentScore, ...], notes: list[MetricNote]) -> tuple[str, ...]:
    ergebnisse: list[str] = []
    for c in components:
        if c.name in NOT_YET_IMPLEMENTABLE_COMPONENTS:
            ergebnisse.append(
                f"{c.label} wird in dieser Analyseversion nicht bewertet (keine strukturierte Datenquelle "
                "verfügbar) — das Gesamtbild bleibt insofern unvollständig."
            )
        elif c.score is None:
            ergebnisse.append(f"{c.label} konnte mangels Daten nicht bewertet werden.")

    mittelmaessig = sorted((n for n in notes if 30 < n.score < 55), key=lambda n: n.score)
    for n in mittelmaessig[:2]:
        ergebnisse.append(
            f"{n.label} liegt mit {n.formatted_value} nur im mittleren Bereich (Teilscore {n.score:.0f}/100)."
        )
    return tuple(ergebnisse[:5])


def _invalidation_conditions(fr: FundamentalsReport, vr: ValuationReport) -> tuple[str, ...]:
    bedingungen: list[str] = []
    basis = vr.dcf_scenarios.get("Basis") if vr.dcf_scenarios else None
    if basis is not None:
        bedingungen.append(
            "Fällt das tatsächliche Umsatzwachstum dauerhaft unter die DCF-Basisannahme von "
            f"{basis.assumptions.revenue_growth_rate:+.1%} p. a., ist die aktuelle Bewertungsspanne hinfällig."
        )
        bedingungen.append(
            "Sinkt die freie-Cashflow-Marge dauerhaft unter die DCF-Basisannahme von "
            f"{basis.assumptions.fcf_margin:.1%}, verschiebt sich die Bewertungsspanne nach unten."
        )
    if vr.safety_margin is not None and vr.fair_value_lower_band is not None:
        bedingungen.append(
            f"Steigt der Kurs über das untere Bewertungsband ({vr.fair_value_lower_band:.2f}), entfällt die "
            f"aktuelle Sicherheitsmarge von {vr.safety_margin:+.1%}."
        )
    if fr.leverage.net_debt_to_ebitda is not None:
        bedingungen.append(
            "Steigt Nettoverschuldung/EBITDA deutlich über den aktuellen Wert von "
            f"{fr.leverage.net_debt_to_ebitda:.2f}x, verschlechtert sich die Bilanzstärke wesentlich."
        )
    if fr.warning_signals:
        bedingungen.append(
            "Bestätigen oder verstärken sich die oben genannten Warnsignale in künftigen Berichten, ist die "
            "Einschätzung zusätzlich in Frage gestellt."
        )
    return tuple(bedingungen[:5])


def compute_score(
    fundamentals_report: FundamentalsReport,
    valuation_report: ValuationReport,
    *,
    weights: dict[str, float] | None = None,
) -> ScoreResult:
    """Berechnet den erklärbaren Gesamtscore (Auftrag §7) aus zwei bereits gebauten Berichten.

    Reine Funktion (kein Datenbankzugriff) — Aufrufer bauen
    ``fundamentals_report``/``valuation_report`` zuvor über
    ``build_fundamentals_report``/``build_valuation_report``.
    """

    weights_used = dict(weights) if weights is not None else dict(DEFAULT_WEIGHTS)
    if set(weights_used) != set(DEFAULT_WEIGHTS):
        raise ValueError(f"weights muss genau die Schlüssel {sorted(DEFAULT_WEIGHTS)} enthalten.")

    scorers = {
        "finanzqualitaet": lambda: _score_finanzqualitaet(fundamentals_report),
        "bewertung_sicherheitsmarge": lambda: _score_bewertung(valuation_report),
        "wachstum_bestaendigkeit": lambda: _score_wachstum(fundamentals_report),
        "bilanzstaerke": lambda: _score_bilanzstaerke(fundamentals_report),
        "management_kapitalallokation": lambda: _score_management(fundamentals_report),
        "datenqualitaet_aktualitaet": lambda: _score_datenqualitaet(fundamentals_report),
    }

    components: list[ComponentScore] = []
    all_notes: list[MetricNote] = []
    for name, weight in weights_used.items():
        if name in NOT_YET_IMPLEMENTABLE_COMPONENTS:
            components.append(ComponentScore(name, _COMPONENT_LABELS[name], weight, None, ()))
            continue
        score, notes = scorers[name]()
        components.append(ComponentScore(name, _COMPONENT_LABELS[name], weight, score, tuple(notes)))
        all_notes.extend(notes)

    available = [c for c in components if c.score is not None]
    total_weight_used = sum(weights_used.values())
    total_available_weight = sum(c.weight for c in available)
    coverage = total_available_weight / total_weight_used if total_weight_used else 0.0

    raw_score: float | None = None
    if total_available_weight > 0:
        raw_score = sum(c.score * c.weight for c in available if c.score is not None) / total_available_weight

    risk_deductions = tuple(
        RiskDeduction(
            code=signal.code,
            severity=signal.severity,
            points=RISK_DEDUCTION_POINTS.get(signal.severity, 5.0),
            description=signal.description,
        )
        for signal in fundamentals_report.warning_signals
    )
    total_deduction = sum(d.points for d in risk_deductions)

    total_score: float | None = None
    if raw_score is not None:
        total_score = max(0.0, raw_score - total_deduction)

    classification = _classify(
        total_score=total_score, coverage=coverage, data_completeness=fundamentals_report.data_completeness
    )

    return ScoreResult(
        entity_id=fundamentals_report.entity_id,
        entity_name=fundamentals_report.entity_name,
        generated_at_utc=utc_now(),
        as_of=fundamentals_report.as_of,
        components=tuple(components),
        coverage=coverage,
        raw_score=raw_score,
        risk_deductions=risk_deductions,
        total_score=total_score,
        classification=classification,
        top_positive_factors=_top_positive_factors(all_notes),
        top_risks=_top_risks(tuple(fundamentals_report.warning_signals), all_notes),
        counterarguments=_counterarguments(tuple(components), all_notes),
        invalidation_conditions=_invalidation_conditions(fundamentals_report, valuation_report),
        not_yet_implementable_components=NOT_YET_IMPLEMENTABLE_COMPONENTS,
    )


def score_entity(
    session: Session,
    entity: Entity,
    *,
    as_of: datetime | None = None,
    weights: dict[str, float] | None = None,
) -> ScoreResult:
    """Dünner Orchestrierungs-Wrapper: baut beide Berichte und berechnet den Score.

    Für Unit-Tests bevorzugt ``compute_score`` direkt mit bereits
    gebauten Berichten verwenden; diese Funktion ist der bequeme
    Einstiegspunkt für die UI/Rangliste (Milestone 6/8a).
    """

    fundamentals_report = build_fundamentals_report(session, entity, as_of=as_of)
    valuation_report = build_valuation_report(session, entity, as_of=as_of)
    return compute_score(fundamentals_report, valuation_report, weights=weights)
