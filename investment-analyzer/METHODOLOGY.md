# Methodik (Stand nach Milestone 4)

**Status:** Die Abschnitte „Fundamentalkennzahlen" (seit Milestone 3)
und „Bewertung"/„Scoring" (seit Milestone 4) sind im Code umgesetzt
(`fundamentals/calculations.py`, `series.py`, `report.py`;
`valuation/multiples.py`, `dcf.py`, `report.py`; `scoring/score.py`) —
Details und Abweichungen von der ursprünglichen Planung siehe dort. Die
Abschnitte „Zukunfts-/Trendanalyse", „Top-10-Rangliste" und
„Backtesting-Prinzipien" sind weiterhin reine Planung für die jeweils
zuständige künftige Milestone. Diese Datei dient als verbindliche
Referenz für alle Agenten, damit Kennzahlenberechnung, Scoring und
Prognosen konsistent und nachvollziehbar bleiben. Änderungen an der
Methodik erfolgen über einen neuen ADR-Eintrag in `DECISIONS.md`, nicht
stillschweigend im Code.

## Grundprinzip

Alle Zahlen werden deterministisch im Code aus gespeicherten,
provenienzbehafteten Datenpunkten berechnet (siehe `DECISIONS.md` →
ADR-6). Ein Sprachmodell darf Ergebnisse zusammenfassen und erklären,
aber keine Zahl erzeugen, die nicht aus einer Formel oder einem
Quellenobjekt ableitbar ist (Auftrag §11).

## Fundamentalkennzahlen (Milestone 3 — implementiert)

- Wachstumsraten (Umsatz, Gewinn, EPS, freier Cashflow) für 1/3/5/10
  Jahre als CAGR (`fundamentals/calculations.py::growth_rate`), über das
  Kalenderjahr der Berichtsperiode ermittelt; ohne exakt passenden
  Vorjahreswert wird `None` statt einer Näherung geliefert.
- Margen (Brutto/operativ/netto) inkl. Stabilitätsmaß (Stichproben-
  Standardabweichung über die verfügbare Jahres-Historie).
- ROE (Nettogewinn / durchschnittliches Eigenkapital) und ROIC
  (NOPAT / investiertes Kapital, invested capital ≈ Schulden + Eigen-
  kapital − liquide Mittel) implementiert. **Abweichung von der
  ursprünglichen Planung:** eine getrennte bereinigte/unbereinigte
  Sonderposten-Behandlung ist NICHT umgesetzt — es fließt der gemeldete
  operative Gewinn ein, ohne Sonderposten-Bereinigung. Der ROIC-
  Steuersatz ist ein expliziter, sichtbarer Parameter (Default 21 %,
  aktueller US-Körperschaftsteuersatz) statt eines stillen Defaults.
- Cash Conversion = operativer Cashflow / Nettogewinn; Investitionsquote
  = |Capex| / Umsatz; Working Capital = kurzfristige Vermögenswerte −
  kurzfristige Verbindlichkeiten.
- Verschuldungskennzahlen: Nettoverbindlichkeiten/EBITDA, Zinsdeckung
  (operatives Ergebnis als EBIT-Näherung / Zinsaufwand). **Abweichung:**
  ein Fälligkeitsprofil aus den Anhangsangaben ist NICHT umgesetzt — das
  würde eine Volltextauswertung der Filings erfordern (wie bei den
  zurückgestellten Warnsignalen, siehe `risk/warning_signals.py`).
- Verwässerung: CAGR der verwässerten Aktienanzahl, Ausschüttungsquote
  (Dividenden/Nettogewinn). **Abweichung:** Rückkaufvolumen wird erfasst
  (`Metric.SHARE_REPURCHASES`), aber noch nicht zu einer eigenen
  Kennzahl (z. B. Rückkaufrendite) verarbeitet — das benötigt
  Marktkapitalisierungsdaten aus Milestone 4.

## Bewertung (Milestone 4 — implementiert)

- Multiples (KGV, EV/EBITDA, EV/EBIT, KBV, KCFV, FCF-Rendite) als reine
  Funktionen (`valuation/multiples.py`), aktuell im Vergleich zur
  Peer-Gruppe (Branchenzuordnung, Milestone 3). **Abweichung von der
  ursprünglichen Planung:** ein Vergleich zur eigenen 5-/10-Jahres-
  Historie ist NICHT umgesetzt — dafür fehlt eine mehrjährig
  akkumulierte Kurshistorie (Alpha Vantage GLOBAL_QUOTE liefert nur den
  aktuellen Kurs je Abruf); vorgemerkt als offener Punkt.
- DCF (`valuation/dcf.py`): Zwei-Phasen-Modell (explizite
  Projektionsjahre + Gordon-Growth-Terminalwert) mit drei Szenarien
  (Basis/optimistisch/pessimistisch, aus der Umsatz-/Margenhistorie des
  Unternehmens abgeleitet) und explizit ausgewiesenen Annahmen
  (Umsatzwachstum, FCF-Marge, WACC-Default 9 %, Terminalwachstum-
  Default 2 %). Ergebnis ist eine **Bewertungsspanne**, kein
  Einzelkurswert. **Abweichung:** die FCF-Marge wird als über die
  Projektionsjahre konstant angenommen statt Capex/NWC/D&A getrennt
  fortzuschreiben — vereinfachte, aber transparent dokumentierte
  Annahme (`DCFAssumptions`). WACC ist ein grober marktüblicher
  Standardwert, keine unternehmensspezifische CAPM-Herleitung (mit
  Beta) — als späterer Verbesserungspunkt vorgemerkt.
- Sensitivitätsmatrix (`build_sensitivity_matrix`): Variation zweier
  wählbarer Parameter (z. B. Wachstum × WACC) über einen konfigurier-
  baren Wertebereich, tabellarisch als fairer Wert je Kombination.
- Sicherheitsmarge (`safety_margin`) = (fairer Wert − aktueller Kurs) /
  fairer Wert, je Szenario einzeln ausgewiesen, nie ein einzelnes
  „Kursziel".

## Scoring (Milestone 4, Auftrag §7 — implementiert)

Gesamtscore 0–100 (`scoring/score.py::compute_score`/`score_entity`),
Startgewichtung (konfigurierbar, siehe `AUFTRAG.md` §7):

| Komponente | Gewicht | Status Milestone 4 |
|---|---:|---|
| Finanzqualität | 25 | berechnet |
| Bewertung/Sicherheitsmarge | 20 | berechnet (nur DCF, siehe oben) |
| Wachstum und Beständigkeit | 15 | berechnet |
| Bilanzstärke | 15 | berechnet |
| Wettbewerbsvorteil | 10 | **nicht berechenbar** (ADR-17) |
| Management/Kapitalallokation | 5 | berechnet, bewusst schmal (nur Aktienverwässerung) |
| Nachrichten und Katalysatoren | 5 | **nicht berechenbar** (ADR-17, wartet auf Milestone 5) |
| Datenqualität/Aktualität | 5 | berechnet |

**Abweichung von der ursprünglichen Planung (siehe ADR-17):** die
beiden strukturell nicht berechenbaren Komponenten
(„Wettbewerbsvorteil", „Nachrichten und Katalysatoren") fließen NICHT
mit 0 in den gewichteten Durchschnitt ein — sie werden aus der
Gewichtssumme entfernt, die übrigen sechs Gewichte werden auf 100 %
renormiert. Der Anteil der tatsächlich genutzten Original-Gewichtung
wird als `coverage` sichtbar gemacht (in dieser Milestone max. 85 %,
da 15 der 100 Gewichtspunkte auf die beiden fehlenden Komponenten
entfallen).

Risiken (aus den Milestone-3-Warnsignalen) wirken als sichtbare,
ausgewiesene Punktabzüge nach dem gewichteten Durchschnitt (kein
verstecktes „Malus"-Feld). `coverage` und `data_completeness` wirken
als Konfidenzschwellen: unterhalb definierter Werte wird ein Kandidat
auf „Beobachten" oder „Datenlage unzureichend" herabgestuft, auch wenn
der reine gewichtete Score hoch wäre.

Ausgabeklassen: **Vertieft prüfen**, **Beobachten**, **Derzeit
unattraktiv**, **Datenlage unzureichend**. Zu jedem Ergebnis: bis zu
fünf wichtigste positive Faktoren, fünf Risiken, Gegenargumente,
Bedingungen für Ungültigkeit der These — alle deterministisch aus den
berechneten Werten generiert, nie durch ein Sprachmodell. Verbotene
Formulierungen „sicherer Kauf"/„garantierter Gewinn" kommen im
generierten Text nachweislich nicht vor (dediziert getestet).

## Zukunfts-/Trendanalyse (Milestone 4/5, Auftrag §7a)

Vier Prognosehorizonte, jeweils getrennt: sehr kurzfristig (1–4 Wochen),
kurzfristig (1–3 Monate), mittelfristig (3–12 Monate), strategisch
(1–3 Jahre). Je Horizont: Aufwärts-/Seitwärts-/Abwärtsszenario mit
Bandbreite, Eintrittswahrscheinlichkeit (grobe Spanne, keine
Scheingenauigkeit), Konfidenz, konkrete Auslöser.

**Mehrere unabhängige Modelle, nicht vermischt:**

1. Fundamentale Szenarien (Fortschreibung der DCF-Annahmen)
2. Analystenrevisionen (nur nachrangiges Signal, Auftrag §7a)
3. Ereignis-/Nachrichtenanalyse (Cluster aus dem `news`-Modul)
4. Branchen-/Makrofaktoren (aus EZB-/Weltbank-/Destatis-Daten)
5. Einfaches robustes Zeitreihenmodell (z. B. saisonale Fortschreibung
   mit Konfidenzintervall — kein Black-Box-ML in Version 1)

Je Modell werden Signal, Stärke, Datenstand und historischer Nutzen
(Out-of-Sample-Trefferquote) separat angezeigt. Technische Kursmuster
ergänzen, ersetzen aber nie die Fundamentalanalyse.

Prognosen werden unveränderlich gespeichert (append-only) und monatlich
gegen den tatsächlichen Verlauf geprüft: Trefferquote, Kalibrierung,
durchschnittlicher Fehler, Vergleich zum Referenzindex. Modelle mit
dauerhaft schlechter Out-of-Sample-Leistung werden automatisch
abgewertet und zur Überprüfung markiert.

Besondere Kennzeichnung bei: Prognosen um Quartalszahlen/politische
Entscheidungen (hohe Sprungunsicherheit), geringer Liquidität/hoher
Volatilität, außergewöhnlichen Marktphasen ohne Vergleichshistorie,
Prognosen mit Abhängigkeit von einem einzelnen Ereignis/einer einzelnen
Quelle.

## Top-10-Rangliste (Milestone 4/6, Auftrag §8a)

Rangliste entsteht ausschließlich aus den gespeicherten, deterministisch
berechneten Teilwerten — nie aus einem einzelnen KI-Texturteil. Die KI
fasst nur zusammen. Mindestanforderungen für Top-10-Aufnahme:
Mindestliquidität, ausreichende Historie, definierte Mindestkonfidenz
(Schwellenwerte werden in Milestone 4 festgelegt). Werden diese nicht
von zehn Kandidaten erfüllt, werden bewusst weniger als zehn ausgegeben.

Drei alternative Ranglisten: (1) beste Kombination Qualität/Bewertung,
(2) geringstes Gesamtrisiko, (3) größtes Chancenpotenzial bei
entsprechend höherem Risiko. Vergleich zum Vorlauf (Auf-/Absteiger, neue/
entfernte Kandidaten) wird bei jeder Neuberechnung dokumentiert;
vergangene Prognosen werden unveränderlich archiviert.

## Backtesting-Prinzipien (Milestone 7, Auftrag §9)

- Point-in-time-Universum inkl. delisteter Unternehmen, soweit Daten
  verfügbar.
- Explizite Vermeidung von Look-ahead-, Survivorship- und
  Selection-Bias (technisch: jede Query im Backtest ist zeitlich
  parametrisiert und darf nur Daten mit Abrufzeitpunkt ≤ Stichtag sehen).
- Rebalancing, Gebühren, Spreads, Dividenden, Währungseffekte werden
  modelliert, nicht ignoriert.
- Trennung Train-/Validierungs-/Out-of-Sample-Zeitraum verbindlich vor
  jeder Parameteroptimierung.
- Kennzahlen: CAGR, Volatilität, Sharpe/Sortino, maximaler Drawdown,
  Turnover — immer im Vergleich zu einem einfachen Referenzindex.
- Keine Optimierung wird akzeptiert, die nur auf einem Zeitraum oder
  wenigen Aktien funktioniert (Overfitting-Check verbindlich vor
  Abnahme).

## Belegprüfung vor jeder Ausgabe (Auftrag §11)

Vor jeder Berichtsausgabe prüft das System automatisiert:

1. Ist jede Zahl einer Quelle oder nachvollziehbaren Formel zugeordnet?
2. Ist die Quelle aktuell genug (Alterskriterium je Kennzahlentyp)?
3. Widersprechen sich Quellen?
4. Wurde eine Annahme als Tatsache formuliert?
5. Fehlen wesentliche Gegenargumente?

Scheitert die Prüfung, wird keine Empfehlung ausgegeben, sondern die
Lücke explizit angezeigt.
