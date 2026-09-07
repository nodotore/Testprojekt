"""Risiken und Warnsignale (Auftrag §6). Milestone 3: Teilmenge ohne Nachrichtenabhängigkeit.

Siehe ``warning_signals.py`` für die implementierten Checks und
``NOT_YET_IMPLEMENTABLE_SIGNALS`` für die aus dem Auftrag-§6-Katalog
bewusst noch nicht abgedeckten, textbasierten Signale.
"""

from investment_analyzer.risk.warning_signals import (
    ALL_CHECKS,
    NOT_YET_IMPLEMENTABLE_SIGNALS,
    WarningSignal,
    check_cashflow_divergence,
    check_high_stock_based_compensation,
    check_late_filing,
    check_strong_dilution,
    check_unusual_inventory_growth,
    check_unusual_receivables_growth,
    run_all_checks,
)

__all__ = [
    "ALL_CHECKS",
    "NOT_YET_IMPLEMENTABLE_SIGNALS",
    "WarningSignal",
    "check_cashflow_divergence",
    "check_high_stock_based_compensation",
    "check_late_filing",
    "check_strong_dilution",
    "check_unusual_inventory_growth",
    "check_unusual_receivables_growth",
    "run_all_checks",
]
