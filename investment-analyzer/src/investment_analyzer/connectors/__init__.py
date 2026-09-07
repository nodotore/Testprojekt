"""Datenquellen-Connectoren (Auftrag §4; siehe DATA_SOURCES.md für die Quellenmatrix).

Jeder Connector erhält über ``base.Connector`` einheitlich: Timeout,
Retry mit Backoff, Rate Limiting, Cache, SSRF-Schutz/URL-Allowlist und
ein Fehlerprotokoll (siehe ``base.py``, ``errors.py``, ``ssrf.py``,
``rate_limiter.py``, ``cache.py``).
"""

from investment_analyzer.connectors.alpha_vantage import AlphaVantageConnector, AlphaVantageQuote
from investment_analyzer.connectors.base import Connector, ConnectorConfig, FetchResult
from investment_analyzer.connectors.cache import CacheEntry, FileCache, cache_key_for
from investment_analyzer.connectors.errors import (
    ConnectorError,
    ConnectorHTTPError,
    ConnectorRateLimitedError,
    ConnectorTimeoutError,
    ConnectorValidationError,
    SSRFBlockedError,
)
from investment_analyzer.connectors.models import Source
from investment_analyzer.connectors.rate_limiter import RateLimiter
from investment_analyzer.connectors.sec_edgar import (
    SecCompanyConcept,
    SecEdgarConnector,
    SecSubmissions,
)
from investment_analyzer.connectors.seed import ensure_default_sources
from investment_analyzer.connectors.ssrf import assert_safe_url

__all__ = [
    "AlphaVantageConnector",
    "AlphaVantageQuote",
    "CacheEntry",
    "Connector",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectorHTTPError",
    "ConnectorRateLimitedError",
    "ConnectorTimeoutError",
    "ConnectorValidationError",
    "FetchResult",
    "FileCache",
    "RateLimiter",
    "SSRFBlockedError",
    "SecCompanyConcept",
    "SecEdgarConnector",
    "SecSubmissions",
    "Source",
    "assert_safe_url",
    "cache_key_for",
    "ensure_default_sources",
]
