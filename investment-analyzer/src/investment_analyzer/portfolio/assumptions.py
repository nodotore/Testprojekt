"""Konfigurierbare Portfolio-Annahmen (Auftrag §8: „Transaktionskosten, Steuern
und Liquidität als konfigurierbare Annahmen berücksichtigen").

Bewusst ein expliziter, sichtbarer Parametersatz statt stiller
Konstanten im Code — jede Berechnung, die diese Annahmen verwendet, gibt
den tatsächlich genutzten Satz mit aus (Auftrag §11: „Wurde eine Annahme
als Tatsache formuliert?" — hier: nein, sie ist als Annahme benannt und
änderbar).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioAssumptions:
    """Standardwerte sind grobe, dokumentierte Näherungen — kein individuell
    ermittelter Steuersatz/Broker-Tarif. Über die Einstellungsseite änderbar
    (Auftrag §10, Seite 10)."""

    #: Grober Standardwert für Online-Broker (Auftrag nennt keinen Startwert).
    transaction_cost_pct: float = 0.001

    #: Deutsche Kapitalertragsteuer inkl. Solidaritätszuschlag (25 % + 5,5 %
    #: Soli darauf) als Default-Näherung — keine individuelle Steuerberatung
    #: (Auftrag §12), keine Kirchensteuer, kein Sparerpauschbetrag.
    tax_rate_pct: float = 0.26375

    #: Mindest-Handelsvolumen/Tag (Stückzahl) als grobe Liquiditätsschwelle —
    #: entspricht keiner offiziellen Börsen-Definition von „illiquide".
    min_daily_liquidity_shares: float = 100_000.0

    def net_proceeds(self, gross_value: float) -> float:
        """Erlös nach Transaktionskosten — NICHT nach Steuern (siehe ``tax_on_gain``)."""

        return gross_value * (1 - self.transaction_cost_pct)

    def tax_on_gain(self, gain: float) -> float:
        """Steuer auf einen realisierten Gewinn.

        Liefert 0 bei Verlust (``gain <= 0``) — eine Verlustverrechnung mit
        anderen Positionen/Perioden wird NICHT modelliert (vereinfachte
        Annahme, keine individuelle Steuerberatung, Auftrag §12).
        """

        return max(gain, 0.0) * self.tax_rate_pct
