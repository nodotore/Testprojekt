"""Warnsignale aus Zahlen — Teilmenge ohne Nachrichtenabhängigkeit (Auftrag §6).

Implementiert werden ausschließlich Signale, die sich direkt und
deterministisch aus bereits erfassten Fundamentaldaten ableiten lassen.
Aus dem Auftrag-§6-Katalog **nicht** implementiert, weil sie Volltext-
oder Nachrichtenauswertung erfordern (folgt frühestens in Milestone 5
„Nachrichtenanalyse" bzw. einer künftigen Filing-Volltext-Auswertung):

- Going-Concern-Hinweise
- Bilanzierungsänderungen / Non-GAAP-Anpassungen im Detail
- Rechtsstreitigkeiten, Regulierung, Sanktionen
- Cybervorfälle, Lieferkettenrisiken
- Short-Interest und technische Signale

Diese Lücken werden hier bewusst NICHT als (immer unauffällige)
Signale vorgetäuscht — ein Aufrufer, der ein vollständiges Bild
erwartet, muss diese Liste kennen (siehe auch
``fundamentals/report.py``, das sie in jeden Bericht aufnimmt).

Jedes implementierte Signal liefert entweder ``None`` (Kriterium nicht
erfüllt ODER Datenlage unzureichend — beides führt zu keinem Alarm,
niemals zu einem geratenen) oder ein ``WarningSignal`` mit knapper,
zahlenbasierter Begründung (``evidence``), damit die Aussage
nachvollziehbar bleibt (Auftrag §11).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from investment_analyzer.entity_resolution.models import Entity
from investment_analyzer.fundamentals import series
from investment_analyzer.fundamentals.calculations import growth_rate, safe_divide
from investment_analyzer.fundamentals.metrics import Metric

#: Aus dem Auftrag-§6-Katalog textbasierte, hier NICHT implementierte Signale.
NOT_YET_IMPLEMENTABLE_SIGNALS: tuple[str, ...] = (
    "going_concern_hinweise",
    "bilanzierungsaenderungen",
    "non_gaap_anpassungen_detail",
    "rechtsstreitigkeiten",
    "regulierung_sanktionen",
    "cybervorfaelle",
    "lieferkettenrisiken",
    "short_interest",
)

DEFAULT_DILUTION_THRESHOLD = 0.03
DEFAULT_SBC_REVENUE_THRESHOLD = 0.05
DEFAULT_UNUSUAL_GROWTH_GAP = 0.15
DEFAULT_LATE_FILING_DAYS = 120


@dataclass(frozen=True)
class WarningSignal:
    code: str
    severity: str  # "hoch" | "mittel" | "niedrig"
    description: str
    evidence: str


def check_cashflow_divergence(
    session: Session, entity: Entity, *, horizon_years: int = 1
) -> WarningSignal | None:
    """Sinkender operativer Cashflow trotz steigendem Nettogewinn (Auftrag §6)."""

    net_income_growth = growth_rate(
        series.get_annual_series(session, entity, Metric.NET_INCOME), horizon_years=horizon_years
    )
    ocf_growth = growth_rate(
        series.get_annual_series(session, entity, Metric.OPERATING_CASH_FLOW),
        horizon_years=horizon_years,
    )
    if net_income_growth is None or ocf_growth is None:
        return None
    if not (net_income_growth > 0 and ocf_growth < 0):
        return None

    return WarningSignal(
        code="cashflow_divergence",
        severity="hoch",
        description="Sinkender operativer Cashflow trotz steigendem Nettogewinn.",
        evidence=(
            f"Nettogewinn-Wachstum {net_income_growth:+.1%}, operativer Cashflow "
            f"{ocf_growth:+.1%} über {horizon_years} Jahr(e)."
        ),
    )


def check_strong_dilution(
    session: Session,
    entity: Entity,
    *,
    horizon_years: int = 3,
    threshold: float = DEFAULT_DILUTION_THRESHOLD,
) -> WarningSignal | None:
    """Starke Aktienverwässerung (Auftrag §6)."""

    dilution = growth_rate(
        series.get_annual_series(session, entity, Metric.SHARES_DILUTED), horizon_years=horizon_years
    )
    if dilution is None or dilution <= threshold:
        return None

    return WarningSignal(
        code="strong_dilution",
        severity="mittel",
        description="Starke Aktienverwässerung.",
        evidence=(
            f"Verwässerte Aktienanzahl wuchs um {dilution:+.1%} p. a. über "
            f"{horizon_years} Jahre (Schwelle: {threshold:.1%})."
        ),
    )


def check_high_stock_based_compensation(
    session: Session, entity: Entity, *, threshold: float = DEFAULT_SBC_REVENUE_THRESHOLD
) -> WarningSignal | None:
    """Hohe aktienbasierte Vergütung im Verhältnis zum Umsatz (Auftrag §6)."""

    sbc_point = series.get_latest_annual_value(session, entity, Metric.STOCK_BASED_COMPENSATION)
    revenue_point = series.get_latest_annual_value(session, entity, Metric.REVENUE)
    if sbc_point is None or revenue_point is None:
        return None

    sbc_date, sbc = sbc_point
    _, revenue = revenue_point
    ratio = safe_divide(sbc, revenue)
    if ratio is None or ratio <= threshold:
        return None

    return WarningSignal(
        code="high_stock_based_compensation",
        severity="niedrig",
        description="Hohe aktienbasierte Vergütung im Verhältnis zum Umsatz.",
        evidence=(
            f"Aktienbasierte Vergütung {ratio:.1%} des Umsatzes im Geschäftsjahr "
            f"bis {sbc_date.isoformat()} (Schwelle: {threshold:.1%})."
        ),
    )


def _unusual_stock_growth_vs_revenue(
    session: Session,
    entity: Entity,
    metric: Metric,
    *,
    code: str,
    label: str,
    horizon_years: int,
    gap_threshold: float,
) -> WarningSignal | None:
    metric_growth = growth_rate(
        series.get_annual_series(session, entity, metric), horizon_years=horizon_years
    )
    revenue_growth = growth_rate(
        series.get_annual_series(session, entity, Metric.REVENUE), horizon_years=horizon_years
    )
    if metric_growth is None or revenue_growth is None:
        return None
    gap = metric_growth - revenue_growth
    if gap <= gap_threshold:
        return None

    return WarningSignal(
        code=code,
        severity="mittel",
        description=f"{label} wachsen deutlich schneller als der Umsatz.",
        evidence=(
            f"Wachstum {label.lower()} {metric_growth:+.1%} vs. Umsatzwachstum "
            f"{revenue_growth:+.1%} über {horizon_years} Jahr(e) "
            f"(Differenz {gap:+.1%} > Schwelle {gap_threshold:.1%})."
        ),
    )


def check_unusual_receivables_growth(
    session: Session,
    entity: Entity,
    *,
    horizon_years: int = 1,
    gap_threshold: float = DEFAULT_UNUSUAL_GROWTH_GAP,
) -> WarningSignal | None:
    """Ungewöhnliches Forderungswachstum relativ zum Umsatz (Auftrag §6)."""

    return _unusual_stock_growth_vs_revenue(
        session,
        entity,
        Metric.ACCOUNTS_RECEIVABLE,
        code="unusual_receivables_growth",
        label="Forderungen",
        horizon_years=horizon_years,
        gap_threshold=gap_threshold,
    )


def check_unusual_inventory_growth(
    session: Session,
    entity: Entity,
    *,
    horizon_years: int = 1,
    gap_threshold: float = DEFAULT_UNUSUAL_GROWTH_GAP,
) -> WarningSignal | None:
    """Ungewöhnliches Vorratswachstum relativ zum Umsatz (Auftrag §6)."""

    return _unusual_stock_growth_vs_revenue(
        session,
        entity,
        Metric.INVENTORY,
        code="unusual_inventory_growth",
        label="Vorräte",
        horizon_years=horizon_years,
        gap_threshold=gap_threshold,
    )


def check_late_filing(
    session: Session, entity: Entity, *, threshold_days: int = DEFAULT_LATE_FILING_DAYS
) -> WarningSignal | None:
    """Möglicherweise verspätete jüngste Jahreseinreichung (Auftrag §6).

    Grober Indikator: Zeit zwischen Periodenende und Einreichungsdatum
    der jüngsten Jahreskennzahl (hier: Umsatz) über der Schwelle. Ersetzt
    keine echte Prüfung auf explizite „NT"-Verspätungsmeldungen (Non-Timely
    Filings) — die dafür nötige Filing-Typ-Auswertung ist nicht Teil
    dieses numerischen Checks.
    """

    datapoint = series.get_latest_annual_datapoint(session, entity, Metric.REVENUE)
    if datapoint is None or datapoint.period_end is None:
        return None

    lag_days = (datapoint.published_at - datapoint.period_end).days
    if lag_days <= threshold_days:
        return None

    return WarningSignal(
        code="late_filing",
        severity="mittel",
        description="Jüngste Jahreseinreichung ungewöhnlich spät nach Periodenende.",
        evidence=(
            f"{lag_days} Tage zwischen Periodenende ({datapoint.period_end.isoformat()}) und "
            f"Einreichung ({datapoint.published_at.isoformat()}), Schwelle: {threshold_days} Tage."
        ),
    )


#: Alle implementierten Checks, für eine vollständige Prüfung in einer Schleife nutzbar
#: (siehe ``fundamentals/report.py``).
ALL_CHECKS = (
    check_cashflow_divergence,
    check_strong_dilution,
    check_high_stock_based_compensation,
    check_unusual_receivables_growth,
    check_unusual_inventory_growth,
    check_late_filing,
)


def run_all_checks(session: Session, entity: Entity) -> list[WarningSignal]:
    """Führt alle implementierten Warnsignal-Checks aus und liefert die ausgelösten."""

    results = []
    for check in ALL_CHECKS:
        signal = check(session, entity)
        if signal is not None:
            results.append(signal)
    return results
