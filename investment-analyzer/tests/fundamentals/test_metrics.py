from __future__ import annotations

from investment_analyzer.fundamentals.metrics import (
    FLOW_METRICS,
    STOCK_METRICS,
    Metric,
    resolve_metric,
)


def test_resolve_metric_bekannter_tag() -> None:
    assert resolve_metric("Revenues") == Metric.REVENUE
    assert resolve_metric("NetIncomeLoss") == Metric.NET_INCOME
    assert resolve_metric("EarningsPerShareDiluted") == Metric.EPS_DILUTED
    assert resolve_metric("Assets") == Metric.TOTAL_ASSETS


def test_resolve_metric_unbekannter_tag_liefert_none() -> None:
    assert resolve_metric("EinNichtGemapptesTag") is None


def test_alle_metrics_sind_entweder_flow_oder_stock_oder_bewusst_ausgenommen() -> None:
    # Aktien-/kapitalmarktbezogene Größen (z. B. Dividenden, Rückkäufe) sind
    # Flow-Größen; Bilanzgrößen sind Stock-Größen. Jede Metric taucht in
    # höchstens einer der beiden Mengen auf.
    overlap = FLOW_METRICS & STOCK_METRICS
    assert overlap == set()


def test_jeder_mapping_wert_ist_eine_gueltige_metric() -> None:
    from investment_analyzer.fundamentals.metrics import SEC_US_GAAP_TAG_TO_METRIC

    for tag, metric in SEC_US_GAAP_TAG_TO_METRIC.items():
        assert isinstance(metric, Metric), f"{tag} mappt auf keinen Metric-Wert"
