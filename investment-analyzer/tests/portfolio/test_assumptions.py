from __future__ import annotations

from investment_analyzer.portfolio.assumptions import PortfolioAssumptions


def test_net_proceeds_zieht_transaktionskosten_ab() -> None:
    assumptions = PortfolioAssumptions(transaction_cost_pct=0.01)
    assert assumptions.net_proceeds(1000.0) == 990.0


def test_tax_on_gain_besteuert_nur_gewinn() -> None:
    assumptions = PortfolioAssumptions(tax_rate_pct=0.25)
    assert assumptions.tax_on_gain(100.0) == 25.0


def test_tax_on_gain_bei_verlust_ist_null() -> None:
    assumptions = PortfolioAssumptions(tax_rate_pct=0.25)
    assert assumptions.tax_on_gain(-50.0) == 0.0


def test_default_werte_sind_dokumentierte_naeherungen() -> None:
    assumptions = PortfolioAssumptions()
    assert assumptions.transaction_cost_pct == 0.001
    assert round(assumptions.tax_rate_pct, 5) == 0.26375
    assert assumptions.min_daily_liquidity_shares == 100_000.0


def test_assumptions_sind_konfigurierbar() -> None:
    custom = PortfolioAssumptions(transaction_cost_pct=0.005, tax_rate_pct=0.3)
    assert custom.net_proceeds(200.0) == 199.0
    assert custom.tax_on_gain(10.0) == 3.0
