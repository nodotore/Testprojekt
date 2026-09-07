"""DCF-Modell mit Szenarien und Sensitivitätsmatrix (Auftrag §6 „Bewertung").

Zweistufiges Discounted-Cashflow-Modell (explizite Projektionsjahre +
Gordon-Growth-Terminalwert). **Bewusste Vereinfachung, klar
gekennzeichnet (Auftrag §1):** Der freie Cashflow wird über eine
konstante FCF-Marge auf den projizierten Umsatz fortgeschrieben, statt
Capex, Working-Capital- und Abschreibungsentwicklung einzeln zu
modellieren. Das ist eine gängige Vereinfachung für ein
Einzelinvestoren-Tool, aber eine Vereinfachung — kein Ersatz für ein
vollständiges Drei-Komponenten-Cashflow-Modell.

Ergebnis ist grundsätzlich eine **Bewertungsspanne** (mehrere Szenarien),
nie ein einzelner „exakter" Kurswert (Auftrag §6). Ist eine Annahme
rechnerisch unzulässig (WACC ≤ Terminalwachstum, WACC ≤ 0), liefert
``run_dcf`` ``None`` statt eines irreführenden Ergebnisses.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date


@dataclass(frozen=True)
class DCFAssumptions:
    """Explizit ausgewiesene Modellannahmen für ein DCF-Szenario (Auftrag §1)."""

    revenue_growth_rate: float
    fcf_margin: float
    wacc: float
    terminal_growth_rate: float
    projection_years: int = 5


@dataclass(frozen=True)
class DCFInputs:
    """Ist-Werte, aus denen die Projektion startet — mit Herkunftsdatum (Auftrag §5)."""

    base_revenue: float
    as_of: date
    net_debt: float | None = None
    shares_diluted: float | None = None


@dataclass(frozen=True)
class DCFResult:
    scenario_name: str
    assumptions: DCFAssumptions
    projected_fcf: tuple[float, ...]
    discounted_fcf: tuple[float, ...]
    terminal_value_discounted: float
    enterprise_value: float
    equity_value: float | None
    fair_value_per_share: float | None


def run_dcf(
    assumptions: DCFAssumptions, inputs: DCFInputs, *, scenario_name: str = "Basis"
) -> DCFResult | None:
    """Führt ein DCF-Szenario aus. Liefert ``None`` bei rechnerisch unzulässigen Annahmen."""

    if assumptions.wacc <= 0:
        return None
    if assumptions.wacc <= assumptions.terminal_growth_rate:
        # Terminalwert (Gordon-Growth) ist nur für WACC > Terminalwachstum definiert;
        # sonst würde der Nenner <= 0 einen sinnlosen (negativen/unendlichen) Wert erzeugen.
        return None
    if assumptions.projection_years < 1:
        return None

    revenue = inputs.base_revenue
    projected_fcf: list[float] = []
    discounted_fcf: list[float] = []
    for year in range(1, assumptions.projection_years + 1):
        revenue = revenue * (1.0 + assumptions.revenue_growth_rate)
        fcf = revenue * assumptions.fcf_margin
        discounted = fcf / ((1.0 + assumptions.wacc) ** year)
        projected_fcf.append(fcf)
        discounted_fcf.append(discounted)

    terminal_fcf = projected_fcf[-1] * (1.0 + assumptions.terminal_growth_rate)
    terminal_value = terminal_fcf / (assumptions.wacc - assumptions.terminal_growth_rate)
    terminal_value_discounted = terminal_value / (
        (1.0 + assumptions.wacc) ** assumptions.projection_years
    )

    enterprise_value = sum(discounted_fcf) + terminal_value_discounted

    equity_value: float | None = None
    if inputs.net_debt is not None:
        equity_value = enterprise_value - inputs.net_debt

    fair_value_per_share: float | None = None
    if equity_value is not None and inputs.shares_diluted:
        fair_value_per_share = equity_value / inputs.shares_diluted

    return DCFResult(
        scenario_name=scenario_name,
        assumptions=assumptions,
        projected_fcf=tuple(projected_fcf),
        discounted_fcf=tuple(discounted_fcf),
        terminal_value_discounted=terminal_value_discounted,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        fair_value_per_share=fair_value_per_share,
    )


def safety_margin(fair_value_lower_band: float | None, current_price: float | None) -> float | None:
    """Sicherheitsmarge = (fairer Wert unteres Band − aktueller Kurs) / fairer Wert unteres Band.

    Statt eines einzelnen „Kursziels" (Auftrag §6). Ein positiver Wert
    bedeutet: der aktuelle Kurs liegt unterhalb selbst des pessimistischen
    Bewertungsbands. Liefert ``None``, wenn eine Eingabe fehlt oder das
    untere Band nicht positiv ist (Sicherheitsmarge dann nicht sinnvoll
    interpretierbar).
    """

    if fair_value_lower_band is None or current_price is None:
        return None
    if fair_value_lower_band <= 0:
        return None
    return (fair_value_lower_band - current_price) / fair_value_lower_band


@dataclass(frozen=True)
class SensitivityMatrix:
    """Ergebnis-Gitter einer Zwei-Parameter-Sensitivitätsanalyse (Auftrag §6)."""

    row_parameter: str
    row_values: tuple[float, ...]
    column_parameter: str
    column_values: tuple[float, ...]
    #: fair_value_per_share[row_index][column_index]; ``None`` bei unzulässigen Annahmen.
    fair_value_per_share: tuple[tuple[float | None, ...], ...]


def build_sensitivity_matrix(
    base: DCFAssumptions,
    inputs: DCFInputs,
    *,
    row_parameter: str,
    row_values: Sequence[float],
    column_parameter: str,
    column_values: Sequence[float],
) -> SensitivityMatrix:
    """Baut eine Sensitivitätsmatrix, indem zwei Annahmen unabhängig variiert werden.

    ``row_parameter``/``column_parameter`` müssen Feldnamen von
    ``DCFAssumptions`` sein (z. B. ``"revenue_growth_rate"``, ``"wacc"``,
    ``"fcf_margin"``, ``"terminal_growth_rate"``). Für die vier in
    Auftrag §6 genannten Dimensionen (Wachstum, Marge, Kapitalkosten,
    Terminalwachstum) werden typischerweise zwei Matrizen gebaut:
    Wachstum×WACC und Marge×Terminalwachstum.
    """

    grid: list[tuple[float | None, ...]] = []
    for row_value in row_values:
        row_results: list[float | None] = []
        for column_value in column_values:
            # mypy kann dynamische **kwargs nicht gegen die Dataclass-Felder prüfen,
            # da row_parameter/column_parameter erst zur Laufzeit bekannte Feldnamen sind.
            overrides = {row_parameter: row_value, column_parameter: column_value}
            scenario = replace(base, **overrides)  # type: ignore[arg-type]
            result = run_dcf(scenario, inputs)
            row_results.append(result.fair_value_per_share if result is not None else None)
        grid.append(tuple(row_results))

    return SensitivityMatrix(
        row_parameter=row_parameter,
        row_values=tuple(row_values),
        column_parameter=column_parameter,
        column_values=tuple(column_values),
        fair_value_per_share=tuple(grid),
    )
