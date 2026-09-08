"""Point-in-time-Backtesting ohne Selbsttäuschung (Auftrag §9). Siehe ADR-3
in DECISIONS.md für Modulgrenzen."""

from investment_analyzer.backtesting.engine import BacktestRun, RebalancePeriod, run_backtest
from investment_analyzer.backtesting.metrics import (
    BacktestMetrics,
    annualized_volatility,
    cagr,
    sharpe_ratio,
    sortino_ratio,
    turnover,
)
from investment_analyzer.backtesting.period_return import (
    PeriodReturn,
    compute_period_return,
    estimate_dividends_per_share,
)
from investment_analyzer.backtesting.report import (
    NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES,
    BacktestReport,
    build_backtest_report,
)
from investment_analyzer.backtesting.splits import (
    DateRange,
    TrainValidationSplit,
    split_train_validation_out_of_sample,
)
from investment_analyzer.backtesting.strategy import select_top_n
from investment_analyzer.backtesting.universe import get_point_in_time_universe

__all__ = [
    "NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES",
    "BacktestMetrics",
    "BacktestReport",
    "BacktestRun",
    "DateRange",
    "PeriodReturn",
    "RebalancePeriod",
    "TrainValidationSplit",
    "annualized_volatility",
    "build_backtest_report",
    "cagr",
    "compute_period_return",
    "estimate_dividends_per_share",
    "get_point_in_time_universe",
    "run_backtest",
    "select_top_n",
    "sharpe_ratio",
    "sortino_ratio",
    "split_train_validation_out_of_sample",
    "turnover",
]
