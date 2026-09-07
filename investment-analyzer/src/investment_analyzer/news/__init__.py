"""Nachrichtenanalyse (Auftrag §6 „Nachrichten", Milestone 5). Siehe ADR-3 in
DECISIONS.md für Modulgrenzen und ``report.py`` für die dokumentierte
KI-Zusammenfassungs-Lücke dieser Milestone."""

from investment_analyzer.news.classification import classify_event_type, classify_source_category
from investment_analyzer.news.clustering import ClusterableNewsItem, NewsCluster, cluster_news_items
from investment_analyzer.news.ingest import ingest_gdelt_articles, ingest_ir_rss_items
from investment_analyzer.news.models import NewsEventType, NewsItem, NewsSourceCategory
from investment_analyzer.news.report import NewsReport, build_news_report
from investment_analyzer.news.sanitize import sanitize_html_to_text

__all__ = [
    "ClusterableNewsItem",
    "NewsCluster",
    "NewsEventType",
    "NewsItem",
    "NewsReport",
    "NewsSourceCategory",
    "build_news_report",
    "classify_event_type",
    "classify_source_category",
    "cluster_news_items",
    "ingest_gdelt_articles",
    "ingest_ir_rss_items",
    "sanitize_html_to_text",
]
