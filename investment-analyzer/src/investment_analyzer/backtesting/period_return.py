"""Perioden-Rendite inkl. Dividenden und Transaktionskosten (Auftrag §9:
„Rebalancing, Gebühren, Spreads, Dividenden und Währungen
berücksichtigen").

Reine Funktionen ohne Datenbankzugriff.

**Bewusste, dokumentierte Vereinfachungen:**
- Spreads werden NICHT separat modelliert — nur ein pauschaler
  Transaktionskosten-Prozentsatz (``portfolio.assumptions.
  PortfolioAssumptions``, Milestone 6) je Rebalancing-Trade. Ein
  Geld-/Brief-Spread würde eine Orderbuch-/Tick-Datenquelle voraussetzen,
  die im Kostenlos-Paket nicht existiert (siehe ``DATA_SOURCES.md``).
- Dividenden je Aktie werden nicht direkt gemeldet (SEC/Alpha Vantage
  liefern nur den gesamten gezahlten Betrag ``Metric.DIVIDENDS_PAID``) —
  die Dividende je Aktie wird als ``DIVIDENDS_PAID / SHARES_DILUTED`` der
  jeweiligen Periode GESCHÄTZT (Näherung, keine Tatsachenbehauptung,
  Auftrag §11). Fehlt eine der beiden Größen, wird KEINE Dividende
  angenommen (``None``), nicht geraten.
- Währungsumrechnung ist NICHT implementiert (dieselbe Lücke wie
  ADR-16/ADR-20) — eine Periodenrendite wird immer in der Währung der
  zugrunde liegenden Kursreihe berechnet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodReturn:
    price_start: float
    price_end: float
    dividends_per_share: float
    transaction_cost_pct: float
    gross_return: float
    net_return: float


def estimate_dividends_per_share(
    dividends_paid: float | None, shares_diluted: float | None
) -> float | None:
    """Grobe Näherung: Gesamt-Dividende / verwässerte Aktienanzahl der Periode."""

    if dividends_paid is None or shares_diluted is None or shares_diluted <= 0:
        return None
    return dividends_paid / shares_diluted


def compute_period_return(
    *,
    price_start: float,
    price_end: float,
    dividends_per_share: float = 0.0,
    transaction_cost_pct: float = 0.0,
) -> PeriodReturn:
    """Gesamtrendite (Kursänderung + Dividende) einer Periode, abzüglich
    Transaktionskosten. ``transaction_cost_pct`` wird EINMALIG angewendet
    (Annahme: ein Trade je Rebalancing, kein Roundtrip-Doppelabzug).
    """

    if price_start <= 0:
        raise ValueError("price_start muss größer als 0 sein.")
    if price_end < 0:
        raise ValueError("price_end darf nicht negativ sein.")
    if dividends_per_share < 0:
        raise ValueError("dividends_per_share darf nicht negativ sein.")
    if not (0 <= transaction_cost_pct < 1):
        raise ValueError("transaction_cost_pct muss zwischen 0 und 1 (exklusiv) liegen.")

    gross_return = (price_end - price_start + dividends_per_share) / price_start
    net_return = (1 + gross_return) * (1 - transaction_cost_pct) - 1

    return PeriodReturn(
        price_start=price_start,
        price_end=price_end,
        dividends_per_share=dividends_per_share,
        transaction_cost_pct=transaction_cost_pct,
        gross_return=gross_return,
        net_return=net_return,
    )
