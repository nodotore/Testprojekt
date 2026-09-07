"""Watchlist und Portfolio (Auftrag §8 „Portfolio- und Vergleichsfunktionen").

Siehe ``DECISIONS.md`` ADR-20 zur Begründung, warum dieses Modul über die
ursprüngliche Auftrag-§4-Modulliste hinaus ergänzt wurde.
"""

from investment_analyzer.portfolio.assumptions import PortfolioAssumptions
from investment_analyzer.portfolio.concentration import (
    NOT_YET_IMPLEMENTABLE_CONCENTRATIONS,
    ConcentrationBreakdown,
    CurrencyExposure,
    PositionValue,
    country_concentration,
    currency_exposure,
    sector_concentration,
)
from investment_analyzer.portfolio.csv_import import (
    CsvImportError,
    CsvImportResult,
    import_portfolio_csv,
    import_watchlist_csv,
)
from investment_analyzer.portfolio.models import PortfolioPosition, WatchlistEntry
from investment_analyzer.portfolio.position_sizing import PositionSizeBand, position_size_band
from investment_analyzer.portfolio.report import (
    PortfolioPositionSnapshot,
    PortfolioReport,
    build_portfolio_report,
)
from investment_analyzer.portfolio.risk_metrics import (
    CorrelationResult,
    DrawdownResult,
    correlation_matrix,
    max_drawdown,
    pairwise_correlation,
)

__all__ = [
    "NOT_YET_IMPLEMENTABLE_CONCENTRATIONS",
    "ConcentrationBreakdown",
    "CorrelationResult",
    "CsvImportError",
    "CsvImportResult",
    "CurrencyExposure",
    "DrawdownResult",
    "PortfolioAssumptions",
    "PortfolioPosition",
    "PortfolioPositionSnapshot",
    "PortfolioReport",
    "PositionSizeBand",
    "PositionValue",
    "WatchlistEntry",
    "build_portfolio_report",
    "correlation_matrix",
    "country_concentration",
    "currency_exposure",
    "import_portfolio_csv",
    "import_watchlist_csv",
    "max_drawdown",
    "pairwise_correlation",
    "position_size_band",
    "sector_concentration",
]
