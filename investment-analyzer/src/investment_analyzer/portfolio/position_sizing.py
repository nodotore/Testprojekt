"""Positionsgrößen-Bandbreite (Auftrag §8: „Positionsgrößen nur als
unverbindliche Bandbreite auf Basis des Nutzerlimits ausgeben").

Liefert NIE einen einzelnen empfohlenen Betrag/eine einzelne Stückzahl —
immer eine Spanne von 0 bis zur Nutzerlimit-Obergrenze, ausdrücklich als
unverbindlich gekennzeichnet (kein Kaufsignal, Auftrag §1/§12).
"""

from __future__ import annotations

from dataclasses import dataclass, field

UNVERBINDLICHKEITS_HINWEIS = (
    "Unverbindliche Bandbreite auf Basis des Nutzerlimits — keine Kaufempfehlung "
    "und keine Anlageberatung (Auftrag §1/§12)."
)


@dataclass(frozen=True)
class PositionSizeBand:
    max_position_value: float
    min_additional_value: float
    max_additional_value: float
    min_additional_shares: float | None
    max_additional_shares: float | None
    note: str = field(default=UNVERBINDLICHKEITS_HINWEIS)


def position_size_band(
    *,
    portfolio_value: float,
    max_position_pct: float,
    current_position_value: float = 0.0,
    latest_price: float | None = None,
) -> PositionSizeBand:
    """Wie viel Wert/Menge einer Position bis zum Nutzerlimit noch Platz hätte.

    Beantwortet ausdrücklich NICHT „wie viel sollte gekauft werden" —
    nur „wie viel wäre bis zur selbst gesetzten Obergrenze noch möglich".
    ``latest_price`` fehlt häufig (siehe Alpha-Vantage-Einschränkungen,
    ``DECISIONS.md``) — in dem Fall bleibt die Stückzahl-Bandbreite
    ``None`` statt eines geschätzten Werts.
    """

    if portfolio_value <= 0:
        raise ValueError("portfolio_value muss größer als 0 sein.")
    if not (0 < max_position_pct <= 100):
        raise ValueError("max_position_pct muss zwischen 0 (exklusiv) und 100 liegen.")

    max_position_value = portfolio_value * (max_position_pct / 100)
    max_additional_value = max(max_position_value - current_position_value, 0.0)

    max_additional_shares: float | None = None
    if latest_price is not None and latest_price > 0:
        max_additional_shares = max_additional_value / latest_price

    return PositionSizeBand(
        max_position_value=max_position_value,
        min_additional_value=0.0,
        max_additional_value=max_additional_value,
        min_additional_shares=0.0 if max_additional_shares is not None else None,
        max_additional_shares=max_additional_shares,
    )
