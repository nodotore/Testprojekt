# Methodik (Planungsstand Milestone 0)

**Status: geplant, noch nicht implementiert.** Diese Datei beschreibt die
Methodik, wie sie ab Milestone 3/4/7 im Code umgesetzt werden soll. Sie
dient als verbindliche Referenz für alle Agenten, damit
Kennzahlenberechnung, Scoring und Prognosen konsistent und
nachvollziehbar bleiben. Änderungen an der Methodik erfolgen über einen
neuen ADR-Eintrag in `DECISIONS.md`, nicht stillschweigend im Code.

## Grundprinzip

Alle Zahlen werden deterministisch im Code aus gespeicherten,
provenienzbehafteten Datenpunkten berechnet (siehe `DECISIONS.md` →
ADR-6). Ein Sprachmodell darf Ergebnisse zusammenfassen und erklären,
aber keine Zahl erzeugen, die nicht aus einer Formel oder einem
Quellenobjekt ableitbar ist (Auftrag §11).

## Fundamentalkennzahlen (Milestone 3)

- Wachstumsraten (Umsatz, Gewinn, EPS, FCF) für 1/3/5/10 Jahre als
  CAGR, jeweils mit Angabe der zugrundeliegenden Berichtsperioden.
- Margen (Brutto/operativ/netto) inkl. Stabilitätsmaß (z. B.
  Standardabweichung über die verfügbare Historie).
- ROIC/ROE mit expliziter Behandlung von Sonderposten (bereinigt und
  unbereinigt getrennt ausgewiesen, nie nur ein „bereinigter" Wert ohne
  Kennzeichnung).
- Cash Conversion = operativer Cashflow / Nettogewinn; Working Capital-
  und Investitionsquoten aus der Kapitalflussrechnung.
- Verschuldungskennzahlen: Nettoverbindlichkeiten/EBITDA, Zinsdeckung
  (EBIT/Zinsaufwand), Fälligkeitsprofil aus den Anhangsangaben.
- Verwässerung: Entwicklung der ausstehenden Aktien (voll verwässert vs.
  Basis), Rückkaufvolumen, Dividendenquote und -deckung.

## Bewertung (Milestone 4)

- Multiples (KGV, EV/EBITDA, EV/EBIT, KBV, KCFV, FCF-Rendite) jeweils im
  Vergleich zur eigenen 5-/10-Jahres-Historie und zu einer Peer-Gruppe
  (Branchenzuordnung + Größenähnlichkeit).
- DCF: drei Szenarien (Basis/optimistisch/pessimistisch) mit explizit
  ausgewiesenen Annahmen (Umsatzwachstum, Margenpfad, Kapitalkosten
  WACC, Terminalwachstum). Ergebnis ist eine **Bewertungsspanne**, kein
  Einzelkurswert.
- Sensitivitätsmatrix: Variation von Wachstum, Marge, WACC,
  Terminalwachstum je ±1–2 Stufen, tabellarisch dargestellt.
- Ausgabe „Sicherheitsmarge" = (fairer Wert unteres Band − aktueller
  Kurs) / fairer Wert unteres Band, nie ein einzelnes „Kursziel".

## Scoring (Milestone 4, Auftrag §7)

Gesamtscore 0–100, Startgewichtung (konfigurierbar, siehe
`AUFTRAG.md` §7):

| Komponente | Gewicht |
|---|---:|
| Finanzqualität | 25 |
| Bewertung/Sicherheitsmarge | 20 |
| Wachstum und Beständigkeit | 15 |
| Bilanzstärke | 15 |
| Wettbewerbsvorteil | 10 |
| Management/Kapitalallokation | 5 |
| Nachrichten und Katalysatoren | 5 |
| Datenqualität/Aktualität | 5 |

Risiken wirken als sichtbare, ausgewiesene Abzüge (kein verstecktes
„Malus"-Feld). Fehlende Daten reduzieren die Konfidenz statt neutral mit
0 bewertet zu werden; unterhalb definierter Konfidenzschwellen wird ein
Kandidat auf „Beobachten" oder „Datenlage unzureichend" gesetzt statt
einen vollen Score zu erhalten.

Ausgabeklassen: **Vertieft prüfen**, **Beobachten**, **Derzeit
unattraktiv**, **Datenlage unzureichend**. Zu jedem Ergebnis: fünf
wichtigste positive Faktoren, fünf Risiken, Gegenargumente, Bedingungen
für Ungültigkeit der These. Verbotene Formulierungen: „sicherer Kauf",
„garantierter Gewinn".

Die exakten Schwellenwerte (Mindestkonfidenz, Mindestliquidität,
Mindesthistorie für Top-10-Aufnahme) werden in Milestone 4 als
konfigurierbare Parameter mit begründeten Startwerten festgelegt und
hier ergänzt.

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
