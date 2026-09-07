"""Kanonisches Kennzahlen-Vokabular und XBRL-Tag-Mapping (Auftrag §6).

``DataPoint.metric_name`` ist laut ``normalization/models.py`` „ab
Milestone 3 im fundamentals-Modul verbindlich" definiert — dieses Modul
löst dieses Versprechen ein. Jede Kennzahl, die im Rest des
``fundamentals``-Moduls (und später ``valuation``/``scoring``) verwendet
wird, referenziert ausschließlich diese kanonischen Namen, nie
quellenspezifische Rohbezeichner (z. B. XBRL-Tags) direkt — so bleiben
Berechnungen unabhängig davon, über welchen Connector eine Kennzahl
letztlich eintrifft.

Das Mapping ist bewusst nicht erschöpfend: Nur Tags, die tatsächlich in
``connectors/sec_edgar.py`` abgefragt werden bzw. gängige, stabile
US-GAAP-Taxonomie-Tags sind, werden aufgenommen. Ein unbekannter Tag
führt bei der Ingestion zu einem expliziten Fehler statt eines stillen
Verlusts der Kennzahl (siehe ``normalization/ingest.py``).
"""

from __future__ import annotations

from enum import StrEnum


class Metric(StrEnum):
    """Kanonische, quellenunabhängige Kennzahlennamen."""

    REVENUE = "revenue"
    GROSS_PROFIT = "gross_profit"
    OPERATING_INCOME = "operating_income"
    PRETAX_INCOME = "pretax_income"
    INCOME_TAX_EXPENSE = "income_tax_expense"
    NET_INCOME = "net_income"
    EPS_DILUTED = "eps_diluted"

    OPERATING_CASH_FLOW = "operating_cash_flow"
    CAPEX = "capex"

    TOTAL_ASSETS = "total_assets"
    TOTAL_LIABILITIES = "total_liabilities"
    TOTAL_EQUITY = "total_equity"
    CURRENT_ASSETS = "current_assets"
    CURRENT_LIABILITIES = "current_liabilities"
    CASH_AND_EQUIVALENTS = "cash_and_equivalents"
    LONG_TERM_DEBT = "long_term_debt"
    SHORT_TERM_DEBT = "short_term_debt"
    INTEREST_EXPENSE = "interest_expense"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"

    SHARES_DILUTED = "shares_diluted"
    DIVIDENDS_PAID = "dividends_paid"
    SHARE_REPURCHASES = "share_repurchases"
    STOCK_BASED_COMPENSATION = "stock_based_compensation"
    DEPRECIATION_AND_AMORTIZATION = "depreciation_and_amortization"


#: Als Geldbetrag interpretierbare Kennzahlen (für Marge/Wachstumsberechnungen relevant).
FLOW_METRICS = frozenset(
    {
        Metric.REVENUE,
        Metric.GROSS_PROFIT,
        Metric.OPERATING_INCOME,
        Metric.PRETAX_INCOME,
        Metric.INCOME_TAX_EXPENSE,
        Metric.NET_INCOME,
        Metric.OPERATING_CASH_FLOW,
        Metric.CAPEX,
        Metric.INTEREST_EXPENSE,
        Metric.DIVIDENDS_PAID,
        Metric.SHARE_REPURCHASES,
        Metric.STOCK_BASED_COMPENSATION,
        Metric.DEPRECIATION_AND_AMORTIZATION,
    }
)

#: Bestandsgrößen (Bilanz-Stichtagswerte, keine Perioden-Flüsse).
STOCK_METRICS = frozenset(
    {
        Metric.TOTAL_ASSETS,
        Metric.TOTAL_LIABILITIES,
        Metric.TOTAL_EQUITY,
        Metric.CASH_AND_EQUIVALENTS,
        Metric.LONG_TERM_DEBT,
        Metric.SHORT_TERM_DEBT,
        Metric.SHARES_DILUTED,
        Metric.ACCOUNTS_RECEIVABLE,
        Metric.INVENTORY,
        Metric.CURRENT_ASSETS,
        Metric.CURRENT_LIABILITIES,
    }
)

#: SEC-EDGAR/US-GAAP-XBRL-Tag → kanonische Kennzahl. Nur stabile, gängige Tags.
SEC_US_GAAP_TAG_TO_METRIC: dict[str, Metric] = {
    "Revenues": Metric.REVENUE,
    "RevenueFromContractWithCustomerExcludingAssessedTax": Metric.REVENUE,
    "RevenueFromContractWithCustomerIncludingAssessedTax": Metric.REVENUE,
    "GrossProfit": Metric.GROSS_PROFIT,
    "OperatingIncomeLoss": Metric.OPERATING_INCOME,
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": (
        Metric.PRETAX_INCOME
    ),
    "IncomeTaxExpenseBenefit": Metric.INCOME_TAX_EXPENSE,
    "NetIncomeLoss": Metric.NET_INCOME,
    "EarningsPerShareDiluted": Metric.EPS_DILUTED,
    "NetCashProvidedByUsedInOperatingActivities": Metric.OPERATING_CASH_FLOW,
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": Metric.OPERATING_CASH_FLOW,
    "PaymentsToAcquirePropertyPlantAndEquipment": Metric.CAPEX,
    "PaymentsToAcquireProductiveAssets": Metric.CAPEX,
    "Assets": Metric.TOTAL_ASSETS,
    "Liabilities": Metric.TOTAL_LIABILITIES,
    "StockholdersEquity": Metric.TOTAL_EQUITY,
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": Metric.TOTAL_EQUITY,
    "CashAndCashEquivalentsAtCarryingValue": Metric.CASH_AND_EQUIVALENTS,
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": Metric.CASH_AND_EQUIVALENTS,
    "LongTermDebtNoncurrent": Metric.LONG_TERM_DEBT,
    "LongTermDebt": Metric.LONG_TERM_DEBT,
    "ShortTermBorrowings": Metric.SHORT_TERM_DEBT,
    "LongTermDebtCurrent": Metric.SHORT_TERM_DEBT,
    "InterestExpense": Metric.INTEREST_EXPENSE,
    "InterestExpenseDebt": Metric.INTEREST_EXPENSE,
    "WeightedAverageNumberOfDilutedSharesOutstanding": Metric.SHARES_DILUTED,
    "PaymentsOfDividends": Metric.DIVIDENDS_PAID,
    "PaymentsOfDividendsCommonStock": Metric.DIVIDENDS_PAID,
    "PaymentsForRepurchaseOfCommonStock": Metric.SHARE_REPURCHASES,
    "ShareBasedCompensation": Metric.STOCK_BASED_COMPENSATION,
    "DepreciationDepletionAndAmortization": Metric.DEPRECIATION_AND_AMORTIZATION,
    "DepreciationAmortizationAndAccretionNet": Metric.DEPRECIATION_AND_AMORTIZATION,
    "DepreciationAndAmortization": Metric.DEPRECIATION_AND_AMORTIZATION,
    "AccountsReceivableNetCurrent": Metric.ACCOUNTS_RECEIVABLE,
    "ReceivablesNetCurrent": Metric.ACCOUNTS_RECEIVABLE,
    "InventoryNet": Metric.INVENTORY,
    "AssetsCurrent": Metric.CURRENT_ASSETS,
    "LiabilitiesCurrent": Metric.CURRENT_LIABILITIES,
}


def resolve_metric(xbrl_tag: str) -> Metric | None:
    """Löst einen SEC-US-GAAP-XBRL-Tag zu einer kanonischen Kennzahl auf, falls bekannt."""

    return SEC_US_GAAP_TAG_TO_METRIC.get(xbrl_tag)
