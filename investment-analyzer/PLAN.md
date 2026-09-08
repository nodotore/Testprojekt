# Implementierungsplan (verbindlich, Stand Milestone 0)

Dieser Plan konkretisiert die Milestones aus `AUFTRAG.md` §14 für dieses
Projekt. Er ist verbindlich im Sinne von Auftrag §16, wird aber nach
Nutzerentscheidungen (siehe `MILESTONE_0.md`) an konkreten Stellen
präzisiert (z. B. welche Connectoren in Milestone 2 zuerst kommen).

**Grundregel:** Milestone 1 beginnt erst nach ausdrücklicher Freigabe des
Nutzers zu den in `MILESTONE_0.md` gestellten Fragen. Die vier
blockierenden Fragen (Projektstruktur, Kostenvariante, Prioritätsmärkte,
Deployment-Ziel) sind am 2026-09-07 beantwortet (siehe `MILESTONE_0.md`
und ADR-7–ADR-10 in `DECISIONS.md`); der ausdrückliche Startbefehl für
Milestone 1 steht noch aus.

## Milestone 0 — Klärung und Datenlizenzen (dieser Stand)

**Ziel:** Fragenliste, Quellen-/Lizenzmatrix, Kostenvarianten,
Architekturentscheidung, verbindlicher Plan stehen; Nutzer hat
entschieden.

**Ergebnisse dieser Runde:**
- `AUFTRAG.md` (Referenzkopie), `CLAUDE.md`, `MILESTONE_0.md`
  (Fragenliste), `DATA_SOURCES.md` (Quellen-/Lizenzmatrix +
  Kostenvarianten), `DECISIONS.md` (ADR-1 bis ADR-6), `PLAN.md` (dieses
  Dokument), `METHODOLOGY.md` (Scoring-/DCF-/Prognose-Methodik als
  Planungsstand), `SECURITY.md` (Sicherheitsrichtlinie als
  Planungsstand), `PROGRESS.md`, `TODO.md`, `CHANGELOG.md`,
  `NEXT_STEPS.md`.

**Abnahmekriterium Milestone 0:** Nutzer hat die Fragen in
`MILESTONE_0.md` beantwortet (oder ausdrücklich auf die vorgeschlagenen
Standardwerte verwiesen) und Milestone 1 freigegeben. Fragen
beantwortet ✅ (2026-09-07); Freigabe zum Start von Milestone 1 steht
noch aus.

## Milestone 1 — Grundgerüst (abgeschlossen 2026-09-07)

**Ziel:** Lauffähiges, leeres Programmgerüst unter Windows startbar,
mit Tests.

**Geplante Schritte:**
1. `pyproject.toml`, venv-Setup, `ruff`/`mypy`/`pytest`-Konfiguration
   (backend-agent)
2. Paketstruktur gemäß ADR-3 anlegen (leere Module mit `__init__.py` +
   README je Modul) (backend-agent)
3. Konfigurationssystem (pydantic-settings): Profil aus Auftrag §2
   (Regionen, Branchen, Horizont, Risikoklasse, Stil, Währung,
   Marktkapitalisierungsgrenzen, Positionsgröße, Kandidatenzahl,
   Speicherort/Exportformate) als typisiertes, persistiertes Modell
   (backend-agent)
4. `SecretStore`-Interface + Keyring-/Verschlüsselte-Datei-Implementierung
   gemäß ADR-5 (security-reviewer + backend-agent)
5. Datenbankschema (SQLAlchemy-Modelle) für Provenienz-Grundmodell gemäß
   ADR-6, Alembic-Migrationen, getestet gegen SQLite und PostgreSQL
   (backend-agent)
6. Logging + Audit-Log-Grundgerüst (audit-Modul) (backend-agent)
7. Streamlit-Startseite (Seite 1 „Start/Datenstatus" aus Auftrag §10) mit
   Ersteinrichtungsdialog gemäß Auftrag §2 (frontend-agent)
8. Windows-Startskripte (`start.ps1`/`start.bat`): venv anlegen,
   Abhängigkeiten installieren, Migrationen ausführen, Streamlit/FastAPI
   starten (backend-agent)
9. Grundgerüst-Tests: Konfiguration laden/speichern, Secret-Store
   Roundtrip, DB-Migration läuft, Streamlit startet (test-agent)

**Abnahmekriterium:** `start.ps1` startet unter Windows ohne manuelle
Zusatzschritte außer Python-Installation; Ersteinrichtungsdialog
speichert ein Profil; mind. 5 Tests grün. **Erfüllt:** `start.ps1`
erkennt Python 3.12+, legt `.venv` an, installiert Abhängigkeiten, führt
`alembic upgrade head` aus und startet Streamlit; 50 Tests grün
(`ruff`/`mypy` fehlerfrei). Offen: manuelle Verifikation unter echtem
Windows sowie Browsertest der Oberfläche stehen noch aus (Sandbox bot
nur Linux + Headless-/HTTP-Verifikation, siehe `PROGRESS.md`).

## Milestone 2 — Datenbeschaffung (abgeschlossen 2026-09-07, mit offenem Punkt)

**Ziel:** Zwei robuste Connectoren (Primärquelle Unternehmensmeldungen +
Marktdatenquelle), vollständig mit Provenienz, Cache, Rate Limits,
Datenalter getestet.

**Geplante Schritte (Connector-Auswahl bestätigt, siehe `MILESTONE_0.md`
→ ADR-8/ADR-9: Kostenlos-Variante, breite Marktauswahl):**
1. Connector-Basisklasse: Timeout, Retry+Backoff, Rate Limiting, Cache,
   Validierung, Fehlerprotokoll, Lizenzhinweis-Metadatum (data-source-agent)
2. Connector A — SEC EDGAR (Primärquelle Meldungen, zunächst USA;
   EU/DE-Meldungsquelle bekannte Lücke, siehe ADR-9) (data-source-agent)
3. Connector B — Alpha Vantage Free (Marktdaten; enge Rate Limits von
   5 req/min im Caching/Scheduling berücksichtigen) (data-source-agent)
4. Normalisierung: Einheiten, Währungsumrechnung, Geschäftsjahresabgleich,
   Split-/Dividenden-Anpassung (normalization-Modul) (financial-analysis-agent)
5. Entity Resolution: Ticker/ISIN/LEI → interne Entity-ID
   (entity_resolution-Modul) (backend-agent)
6. SSRF-Schutz + URL-Allowlist je Connector (security-reviewer)
7. Tests: Cache-Verhalten, Rate-Limit-Einhaltung, simulierter
   Quellenausfall → sichtbarer Fehler statt stiller Altdaten (test-agent)

**Abnahmekriterium:** Beide Connectoren liefern für mind. 10 reale
Testunternehmen Daten mit vollständiger Provenienz; simulierter Ausfall
erzeugt sichtbaren Fehler, keinen stillen Fallback auf veraltete Werte.

**Erfüllt:** Connector-Grundgerüst (Timeout, exponentieller Backoff,
Rate-Limiting, dateibasierter Cache mit TTL, SSRF-Schutz mit
DNS-Rebinding-Prüfung, einheitliches Fehlerprotokoll) sowie SEC-EDGAR-
und Alpha-Vantage-Connector vollständig implementiert und mit
gemockten, realistisch strukturierten Antworten getestet (66 neue
Tests, insgesamt 116, `ruff`/`mypy` fehlerfrei). Simulierter
Quellenausfall (Timeout, 5xx, 429, ungültiges JSON, Alpha-Vantage-
Rate-Limit-Hinweis im 200er-Body) erzeugt in jedem Fall einen
sichtbaren Fehler statt eines stillen Fallbacks auf veraltete
Cache-Daten (dediziert getestet). Source-Seeding, Entity-Resolution
(niemals Ticker allein, ADR/Auftrag §5) und Ingestion in
provenienzbehaftete `DataPoint`-Zeilen (inkl. Point-in-time-/
Restatement-Verhalten) sind implementiert und getestet.

**Offen — Live-Verifikation mit 10 realen Unternehmen:** In dieser
Sandbox-Entwicklungsumgebung ist ausgehender Netzwerkzugriff auf
`www.sec.gov`/`data.sec.gov` und `www.alphavantage.co` durch die
Egress-Policy des Umgebungs-Proxys blockiert (verifiziert per
`curl` → `403 CONNECT tunnel failed`, siehe `PROGRESS.md`). Der
formale Abnahmenachweis mit zehn realen Unternehmen konnte hier daher
nicht erbracht werden und steht aus — nachzuholen in einer Umgebung mit
echtem Internetzugang (z. B. beim Nutzer über `start.ps1`); für Alpha
Vantage zusätzlich erst, sobald ein echter API-Schlüssel vorliegt (der
öffentliche „demo"-Schlüssel funktioniert nur für das Symbol IBM).

## Milestone 3 — Fundamentalanalyse (abgeschlossen 2026-09-07, mit offenem Punkt)

Normalisierung, Kennzahlen (Auftrag §6 „Fundamentaldaten"), Zeitreihen
(1/3/5/10 Jahre), Peer-Gruppen-Zuordnung, Warnsignale (Auftrag §6
„Risiken und Warnsignale", Teilmenge ohne News-Abhängigkeit).
Abnahme: manuell nachgerechnete Testfälle (mind. 3 reale Unternehmen,
Handrechnung vs. Code) stimmen überein (financial-analysis-agent +
test-agent).

**Erfüllt:** Kanonisches Kennzahlen-Vokabular (`fundamentals/metrics.py`,
22 Kennzahlen, XBRL-Tag-Mapping) verbindlich in der Ingestion verankert
(Auftrag §16-Grundsatz „keine unbelegten Zahlen" — unbekannte Tags
werden abgelehnt statt uneinheitlich gespeichert). Reiner, DB-freier
Berechnungskern (`calculations.py`: CAGR/Wachstum, Margen + Stabilität,
ROE/ROIC, Cash Conversion/Investitionsquote/Working Capital, EBITDA,
Nettoverschuldung/EBITDA, Zinsdeckung, Ausschüttungsquote,
Aktienverwässerung). Point-in-time-fähiges Zeitreihen-Repository
(`series.py`) mit robuster Jahres-/Quartals-Trennung ohne zusätzliche
Metadaten. SIC-Klassifikation (neue Alembic-Migration, gegen SQLite
verifiziert) und einfache Peer-Gruppen-Zuordnung über den SIC-Code.
Sechs zahlenbasierte Warnsignal-Checks (`risk/warning_signals.py`) mit
expliziter Auflistung der acht textbasierten, noch nicht
implementierbaren Signale aus Auftrag §6 (keine Fake-Coverage).
Orchestrierung zu einem `FundamentalsReport` (`report.py`) inkl.
`data_completeness`/`missing_fields` — fehlende Daten reduzieren
sichtbar die Aussagekraft statt neutral mit Null bewertet zu werden
(Auftrag §7-Grundsatz, vollständige Umsetzung folgt in Milestone 4).
66 neue Tests (insgesamt 182), `ruff`/`mypy` fehlerfrei.

**Offen — Verifikation an drei realen Unternehmen:** Die Handrechnungs-
Tests verwenden bewusst einfache, synthetische Beispieldaten (klar so
gekennzeichnet), da diese Sandbox mangels Internetzugangs keine echten
SEC-Filings laden konnte (dieselbe Einschränkung wie bei den
Connector-Live-Tests in Milestone 2, siehe `PROGRESS.md`). Die Formeln
sind damit nachweislich korrekt implementiert; der Abgleich mit
tatsächlich veröffentlichten Geschäftszahlen dreier realer Unternehmen
steht noch aus und ist nachzuholen, sobald Internetzugang und
(für Alpha Vantage) ein echter API-Schlüssel verfügbar sind.

## Milestone 4 — Bewertung und Score (abgeschlossen 2026-09-07)

Multiples, DCF mit drei Szenarien + Sensitivitätsmatrix (Auftrag §6
„Bewertung"), erklärbares Scoring mit Startgewichtung aus Auftrag §7,
Konfidenzlogik (fehlende Daten → Konfidenzabschlag statt Nullwertung),
Gegenargumente/Ausgabeklassen. Abnahme: DCF-Handrechnung stimmt;
Scoring-Gewichte konfigurierbar und nachvollziehbar geloggt
(financial-analysis-agent + test-agent).

**Erfüllt:** Multiples-Berechnungskern (`valuation/multiples.py`: KGV,
EV/EBITDA, EV/EBIT, KBV, Kurs/FCF, FCF-Rendite). Zweistufiges DCF-Modell
(`valuation/dcf.py`) mit explizit dokumentierter Vereinfachung (konstante
FCF-Marge statt einzeln modelliertem Capex/NWC/Abschreibungspfad),
Sensitivitätsmatrizen für alle vier in Auftrag §6 genannten Dimensionen
(Wachstum×WACC, Marge×Terminalwachstum), Sicherheitsmarge statt
Einzelkursziel. `valuation/report.py` leitet die drei Szenarien
(Basis/Optimistisch/Pessimistisch) deterministisch aus der eigenen
3-/1-Jahres-Historie ab — liefert `None` (keine erfundene Annahme)
statt einer Bewertung, wenn die Historie nicht reicht.
`scoring/score.py` setzt die Auftrag-§7-Startgewichtung 1:1 um
(25/20/15/15/10/5/5/5 = 100), rechnet Risiken als sichtbare, benannte
Abzüge nach der gewichteten Durchschnittsbildung, und weist über
`coverage`/`data_completeness` aus, wie vertrauenswürdig der Score ist
— unterhalb definierter Schwellen wird auf „Beobachten" oder
„Datenlage unzureichend" herabgestuft statt einen unbegründet hohen
Score auszugeben. Zu jedem Ergebnis werden bis zu fünf positive
Faktoren, fünf Risiken (inkl. der Warnsignal-Evidenz aus Milestone 3),
Gegenargumente und Ungültigkeitsbedingungen erzeugt — alle Texte
deterministisch aus den berechneten Zahlen generiert, nie vom
Sprachmodell erfunden; die verbotenen Formulierungen „sicherer Kauf"/
„garantierter Gewinn" werden nirgends verwendet (dediziert getestet).

**Bewusste, dokumentierte Lücke:** Zwei der acht Auftrag-§7-Komponenten
(„Wettbewerbsvorteil" 10 %, „Nachrichten und Katalysatoren" 5 %) sind
strukturell nicht berechenbar, da es noch kein Wettbewerbs-/
Geschäftsmodell- oder Nachrichtenmodul gibt (Milestone 5+). Sie werden
NICHT mit 0 bewertet, sondern als „nicht verfügbar" markiert und aus
der Gewichtssumme ausgeschlossen (`coverage` sinkt entsprechend auf
maximal 85 %) — konsistent mit dem bereits in Milestone 3 etablierten
Muster (`NOT_YET_IMPLEMENTABLE_SIGNALS`).

59 neue Tests (insgesamt 241), davon zahlreiche exakte
Handrechnungs-Tests (u. a. ein DCF-Fall mit Wachstum = WACC, wodurch
sich jedes Jahr exakt auf `base_revenue × fcf_margin` abdiskontiert —
siehe `tests/valuation/test_dcf.py`). `ruff`/`mypy` fehlerfrei. Wie in
Milestone 2/3 war eine Verifikation mit echten Marktdaten/DCF-Annahmen
für reale Unternehmen in dieser Sandbox mangels Internetzugang nicht
möglich (siehe `PROGRESS.md`).

## Milestone 5 — Nachrichtenanalyse (abgeschlossen 2026-09-07)

**Erfüllt:** Connector-Grundgerüst um `get_text()` erweitert (Rohtext
statt JSON, für RSS/Atom, ohne `get_json()`-Verhalten zu ändern);
GDELT-DOC-2.0-Connector (`connectors/gdelt.py`, Volltextsuche nach
Firmenname, kein API-Schlüssel nötig) und generischer IR-RSS-Connector
(`connectors/ir_rss.py`, RSS-2.0/Atom-Parsing über stdlib
`xml.etree`, Host-Allowlist wird pro Feed-URL zur Laufzeit gesetzt,
SSRF-/DNS-Rebinding-Schutz bleibt davon unabhängig aktiv). Neues
provenienzbehaftetes `NewsItem`-Modell (`news/models.py`, ADR-18) mit
Migration und Erweiterung des Source-Seedings um `gdelt`/`ir_rss`.
HTML-Bereinigung zu reinem Klartext (`news/sanitize.py`, Skript-/
Stilinhalte werden verworfen, Auftrag §12) sowie deterministische,
regelbasierte Klassifikation von Quellqualität
(Unternehmensmeldung/unabhängiger Bericht/Kommentar) und Ereignistyp
(Earnings, M&A, Management, Recht/Regulierung, Kapitalmarkt,
Produkt/Betrieb, Cyber/Lieferkette, Sonstiges) in
`news/classification.py` — nie durch ein Sprachmodell (ADR-19).
Idempotente Ingestion (`news/ingest.py`, URL-Normalisierung inkl.
Entfernung bekannter Tracking-Parameter vor dem Dedup-Hash). Rein
funktionales, deterministisches Ereignis-Clustering
(`news/clustering.py`, `difflib.SequenceMatcher`, keine Embeddings/kein
Sprachmodell) und `NewsReport`-Orchestrierung (`news/report.py`).

**Bewusste, dokumentierte Lücke:** Die im Auftrag genannte
„KI-Zusammenfassung mit Quellenverweis" wird in dieser Milestone NICHT
umgesetzt — es gibt in dieser Entwicklungsumgebung weder eine
Claude-API-Anbindung noch einen dafür vorgesehenen `SecretStore`-
Schlüssel. Die Datengrundlage dafür ist gelegt (`NewsCluster.items`
referenziert jede Quelle zwingend über `url`); die eigentliche
Zusammenfassungs-Erzeugung ist als Punkt für die UI-/Reports-Schicht
(Milestone 6+) vorgemerkt, inkl. der Pflicht, den bereinigten Text
weiterhin als nicht vertrauenswürdige Nutzdaten zu behandeln (Auftrag
§12, „Prompt-Injection-Texte ignorieren"). Ebenfalls offen: welche
IR-RSS-Feed-URL zu welcher `Entity` gehört, ist keine automatisierte
Zuordnung — der Connector liefert nur den Abruf-/Parse-Mechanismus für
eine gegebene URL.

60 neue Tests (insgesamt 301), davon Connector-Tests (Mock-HTTP,
XML-Parsing-Fälle für RSS/Atom inkl. kaputtem XML), Dedup-/
Idempotenz-Tests gegen die Datenbank, hand-nachvollziehbare
Klassifikations- und Clustering-Fälle. `ruff`/`mypy` fehlerfrei. Wie in
Milestone 2/3/4 war eine Verifikation der Duplikaterkennung an einem
realen Testset (Abnahmekriterium) in dieser Sandbox mangels
Internetzugang nicht möglich (siehe `PROGRESS.md`).

## Milestone 6 — Portfolio und Exporte (abgeschlossen 2026-09-07)

**Erfüllt:** Neues Modul `portfolio/` (ADR-20) mit
Watchlist-/Portfolio-Import (manuell über ORM-Modelle, CSV-Import mit
Zeilen-genauer Fehlersammlung statt Abbruch oder stillem Überspringen),
Branchen-/Länder-/Währungs-Konzentrationsanalyse (nach Marktwert,
`ConcentrationBreakdown` liefert `computable=False` statt eines
irreführenden Prozentsatzes bei gemischten Bestandswährungen),
Korrelation (Pearson auf Tagesrenditen) und historischer Max-Drawdown
als reine Funktionen mit expliziter „Datenlage unzureichend"-Markierung
bei zu wenigen Kurspunkten, unverbindliche Positionsgrößen-Bandbreite
(Auftrag §8) sowie konfigurierbare `PortfolioAssumptions`
(Transaktionskosten/Steuersatz/Mindestliquidität). `PortfolioReport`-
Orchestrierung fasst alles zusammen und dokumentiert jede Lücke explizit
(`gaps`).

Neues Modul `reports/` (bisher leerer Stub) mit `ReportBundle`
(ADR-21) als einziger Quelle der Wahrheit — aggregiert
FundamentalsReport/ValuationReport/ScoreResult/NewsReport zu einem
Objekt, das JSON-, Excel- (`openpyxl`, alle sieben in Auftrag §10
geforderten Tabellenblätter: Zusammenfassung, Kennzahlen, Bewertung,
Risiken, Nachrichten, Quellen, Annahmen) und PDF-Export (`reportlab`)
strukturell identisch versorgt — beide Formate lesen ausschließlich aus
demselben `report_bundle_to_dict()`. Formel-Injection-Schutz im
Excel-Export für Zellwerte aus externen Quellen (Nachrichtentitel/-URLs,
Auftrag §12).

**Bewusste, dokumentierte Lücke — Abnahmekriterium teilweise erfüllt:**
Das Abnahmekriterium „Export enthält exakt dieselben Werte wie die
UI-Ansicht (automatisierter Abgleich)" ist strukturell, aber nicht live
erfüllt: Es existiert noch KEINE Streamlit-Detailseite, die Berichte
anzeigt (nur die Start/Datenstatus-Seite aus Milestone 1) — ein
automatisierter UI-vs.-Export-Abgleich kann daher erst erfolgen, sobald
diese UI-Seite gebaut ist (voraussichtlich Milestone 8, „Benutzer-
oberfläche"). Die strukturelle Garantie (ADR-21: ein einziges
`ReportBundle` als Datenquelle für alle Formate) stellt sicher, dass
eine künftige UI-Seite, sofern sie ebenfalls von einem `ReportBundle`
rendert, automatisch dieselben Werte zeigt.

60 neue Tests (insgesamt 372), `ruff`/`mypy` fehlerfrei. Wie in
Milestone 2/3/4/5 war eine Verifikation mit echten Marktdaten in dieser
Sandbox mangels Internetzugang nicht möglich (siehe `PROGRESS.md`).

## Milestone 7 — Backtesting (abgeschlossen 2026-09-07)

**Erfüllt:** Point-in-time-Universum (`backtesting/universe.py`,
ADR-22) — eine Entity gilt als „zum Stichtag bekannt", wenn mindestens
ein `DataPoint` mit `retrieved_at_utc <= as_of` existiert. Deterministische
Top-N-Auswahlstrategie (`backtesting/strategy.py`) auf Basis des
bereits bestehenden, festen Scoring-Systems — kein auf den Backtest-
Zeitraum gefitteter Parameter, damit strukturell gegen die in Auftrag §9
verbotene „Optimierung, die nur auf einem Zeitraum funktioniert"
abgesichert. Rebalancing-Engine (`backtesting/engine.py`) mit
gleichgewichteter Portfoliorendite je Periode (Kursänderung +
geschätzte Dividende − Transaktionskosten, `period_return.py`).
Train-/Validierungs-/Out-of-Sample-Split (`splits.py`) sowie CAGR,
Volatilität, Sharpe/Sortino, Turnover (`metrics.py`) — maximaler
Drawdown wird aus `portfolio/risk_metrics.py` (Milestone 6)
wiederverwendet statt neu implementiert. `BacktestReport`-
Orchestrierung (`report.py`) mit vollständiger Lücken-Dokumentation.

**Abnahmekriterium „kein Look-ahead" erfüllt, zweistufig nachgewiesen:**
`tests/backtesting/test_universe.py::
test_spaeter_eintreffende_daten_veraendern_frueheres_universum_nicht`
(Universums-Ebene) und `tests/backtesting/test_engine.py::
test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_backtest_
ergebnis_nicht` (vollständiger Backtest-Lauf: Auswahl UND
Portfoliorendite bit-identisch vor/nach dem Eintreffen der späteren
Daten).

**Bewusste, dokumentierte Lücken (ADR-22):** kein Benchmark-/Index-
Kursvergleich (keine Datenquelle im Kostenlos-Paket angebunden — die
Funktion akzeptiert optional eine extern gelieferte Benchmark-
Renditereihe), keine Währungsumrechnung (dieselbe Lücke wie ADR-16/
ADR-20), unvollständiges Survivorship-Universum (keine Delisting-
Historie verfügbar — das Universum umfasst „was das System bereits
erfasst hatte", nicht „was historisch existierte").

61 neue Tests (insgesamt 425), `ruff`/`mypy` fehlerfrei. Wie in
Milestone 2–6 war eine Verifikation mit echten Marktdaten in dieser
Sandbox mangels Internetzugang nicht möglich (siehe `PROGRESS.md`).

## Milestone 8 — Sicherheit und Abnahme (abgeschlossen 2026-09-08, mit offenen Punkten)

**Umgesetzt:** Security-Review in zwei Stufen — eigener Review
(ADR-23: Downloadgrößen-Begrenzung, Log-Redaction, Pflichthinweis in
Exporten, Redirect-Dokumentation; ADR-24: Ausfalltests inkl. echtem
XML-Entity-Expansion-Fund im IR-RSS-Connector, Restore-Prozess neu
gebaut) und ein separater, unabhängiger Review-Durchlauf (ADR-25), der
einen echten, für Auftrag §15 blockierenden Look-ahead-Bias in den
Warnsignal-Checks fand — noch in dieser Milestone-Runde behoben und
mit Regressionstests abgesichert — sowie zwei weitere Härtungen
(Downloadgrößen-Prüfung per Streaming, HTML-Sanitizing-Fallback) und
eine ehrlich dokumentierte Restlücke (SSRF-Time-of-check-to-time-of-
use). Windows-Setup vervollständigt (`start.ps1` sichert die Datenbank
automatisch vor jeder Migration, neue Backup-/Restore-Skripte),
`BENUTZERHANDBUCH.md` geschrieben. Kein nativer Windows-Installer
(.exe/.msi) — bewusste, dokumentierte Einschränkung (keine Windows-
Build-Werkzeuge in dieser Entwicklungsumgebung verfügbar).

**Abnahme:** ehrliche, kriterienweise Bewertung aller neun
Auftrag-§15-Kriterien in `ABNAHME.md`. Sechs von neun Kriterien
vollständig erfüllt, ein Kriterium teilweise (DCF/Kernkennzahlen nur an
Handrechnungen mit synthetischen Daten geprüft, nicht an echten
Unternehmenszahlen), zwei Kriterien strukturell fundiert aber empirisch
nicht abschließend nachweisbar (kompletter Lauf mit echten Daten;
Exporte = Oberflächenwerte, da noch keine UI-Detailseite existiert).
Unabhängiger Security-/Plausibilitätscheck dokumentiert (ADR-25) —
dieser fand einen echten Fehler, der noch behoben wurde, kein
Alibi-Durchlauf. 453 Tests grün, `ruff`/`mypy` fehlerfrei.

## Agenteneinsatz pro Milestone

Ab Milestone 1 wird vor jeder Parallelisierung eine konkrete
Agent-zu-Modul-Zuordnung in diesem Dokument (Abschnitt der jeweiligen
Milestone-Runde) ergänzt — siehe ADR-4. Diese Kopfzeile hier nennt nur
die typischerweise führende Rolle je Milestone; die tatsächliche
Aufteilung einzelner Teilaufgaben folgt erst bei Arbeitsbeginn der
jeweiligen Milestone.
