"""SSRF-Schutz und URL-Allowlist je Connector (Auftrag §12, SECURITY.md).

Zwei Prüfstufen für jede ausgehende Anfrage:

1. **Allowlist:** Nur HTTPS und nur explizit erlaubte Hostnamen (exakter
   Domainabgleich, keine Wildcards) sind zulässig.
2. **DNS-Rebinding-Schutz:** Der Hostname wird aufgelöst; zeigt er auf
   eine private, loopback-, link-local- oder anderweitig reservierte
   IP-Adresse, wird die Anfrage abgelehnt — auch wenn der Hostname selbst
   auf der Allowlist steht (verhindert, dass ein erlaubter Hostname zur
   Laufzeit auf ein internes Netzwerk umgebogen wird).

Der Resolver ist injizierbar, damit Tests ohne echte DNS-Auflösung
laufen (schneller, deterministisch, funktioniert auch ohne
Netzwerkzugriff in der Entwicklungsumgebung).
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit

from investment_analyzer.connectors.errors import SSRFBlockedError

#: Signatur von ``socket.getaddrinfo`` — genügt für unsere Zwecke (nur die IP-Adressen).
Resolver = Callable[[str, int | None], list[tuple]]


def _default_resolver(host: str, port: int | None) -> list[tuple]:
    return socket.getaddrinfo(host, port)


def assert_safe_url(
    url: str,
    allowed_hosts: frozenset[str],
    *,
    resolver: Resolver = _default_resolver,
) -> None:
    """Wirft ``SSRFBlockedError``, falls ``url`` nicht sicher aufrufbar ist."""

    parts = urlsplit(url)

    if parts.scheme != "https":
        raise SSRFBlockedError(f"Nur HTTPS ist erlaubt, erhalten: {parts.scheme!r} ({url}).")

    host = (parts.hostname or "").lower()
    if host not in allowed_hosts:
        raise SSRFBlockedError(
            f"Host {host!r} ist nicht in der Allowlist dieses Connectors ({sorted(allowed_hosts)})."
        )

    try:
        addrinfo = resolver(host, parts.port)
    except OSError as exc:
        raise SSRFBlockedError(f"DNS-Auflösung für {host!r} fehlgeschlagen: {exc}") from exc

    if not addrinfo:
        raise SSRFBlockedError(f"DNS-Auflösung für {host!r} lieferte keine Adresse.")

    for family_info in addrinfo:
        sockaddr = family_info[4]
        ip_text = sockaddr[0]
        ip = ipaddress.ip_address(ip_text)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise SSRFBlockedError(
                f"Host {host!r} löst auf eine nicht-öffentliche Adresse auf ({ip_text}) — "
                "wird als möglicher SSRF-/DNS-Rebinding-Versuch blockiert."
            )
