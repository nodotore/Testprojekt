from __future__ import annotations

import pytest

from investment_analyzer.connectors.errors import SSRFBlockedError
from investment_analyzer.connectors.ssrf import assert_safe_url


def _resolver_returning(ip: str):
    def _resolve(host: str, port: int | None):
        return [(2, 1, 6, "", (ip, port or 443))]

    return _resolve


def test_erlaubt_https_host_mit_oeffentlicher_ip() -> None:
    assert_safe_url(
        "https://www.sec.gov/foo",
        frozenset({"www.sec.gov"}),
        resolver=_resolver_returning("23.216.9.1"),
    )


def test_lehnt_nicht_https_ab() -> None:
    with pytest.raises(SSRFBlockedError, match="HTTPS"):
        assert_safe_url(
            "http://www.sec.gov/foo",
            frozenset({"www.sec.gov"}),
            resolver=_resolver_returning("23.216.9.1"),
        )


def test_lehnt_host_ausserhalb_der_allowlist_ab() -> None:
    with pytest.raises(SSRFBlockedError, match="Allowlist"):
        assert_safe_url(
            "https://evil.example.com/foo",
            frozenset({"www.sec.gov"}),
            resolver=_resolver_returning("23.216.9.1"),
        )


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",  # loopback
        "10.0.0.5",  # privates Netz
        "192.168.1.1",  # privates Netz
        "169.254.1.1",  # link-local
        "0.0.0.0",  # unspecified
    ],
)
def test_lehnt_dns_rebinding_auf_nicht_oeffentliche_adressen_ab(ip: str) -> None:
    with pytest.raises(SSRFBlockedError, match="nicht-öffentliche Adresse"):
        assert_safe_url(
            "https://www.sec.gov/foo",
            frozenset({"www.sec.gov"}),
            resolver=_resolver_returning(ip),
        )


def test_lehnt_bei_dns_fehler_ab() -> None:
    def _failing_resolver(host: str, port: int | None):
        raise OSError("DNS nicht erreichbar")

    with pytest.raises(SSRFBlockedError, match="DNS-Auflösung"):
        assert_safe_url(
            "https://www.sec.gov/foo", frozenset({"www.sec.gov"}), resolver=_failing_resolver
        )


def test_hostvergleich_ist_case_insensitive() -> None:
    assert_safe_url(
        "https://WWW.SEC.GOV/foo",
        frozenset({"www.sec.gov"}),
        resolver=_resolver_returning("23.216.9.1"),
    )
