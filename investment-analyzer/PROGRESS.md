# Fortschritt — Investment-Analysator

## Milestone 0 — Klärung und Datenlizenzen

**Status: Fragen beantwortet, wartet auf ausdrückliche Freigabe für Milestone 1.**

Nutzerantworten (2026-09-07): Projektstruktur = Unterverzeichnis in
diesem Repo (bestätigt); Kostenvariante = Kostenlos; Prioritätsmärkte =
breit (USA, Deutschland, übriges Europa, weitere global offen);
Deployment = lokal Windows + SQLite. Festgehalten als ADR-7–ADR-10 in
`DECISIONS.md`, Details in `MILESTONE_0.md`.

Umgesetzt (dieser Agentenlauf, Hauptagent/project-orchestrator, keine
Parallelisierung nötig für reine Dokumentation):

- `AUFTRAG.md`: unveränderte Referenzkopie des Originalauftrags
- `CLAUDE.md`: Leitplanken, Modulgrenzen, Agentenregeln für künftige
  Sessions
- `MILESTONE_0.md`: Fragenliste (blockierend + ergänzend mit
  Standardwertvorschlag)
- `DATA_SOURCES.md`: Quellen-/Lizenzmatrix nach Auftrag-Hierarchie
  (Stufe 1–7) mit drei Kostenvarianten (kostenlos/günstig/professionell)
- `DECISIONS.md`: ADR-1 (Unterverzeichnis statt Repo-Root), ADR-2
  (Tech-Stack), ADR-3 (Modulgrenzen), ADR-4 (Agentenkoordination),
  ADR-5 (Secret-Management), ADR-6 (Provenienz-first-Datenmodell)
- `PLAN.md`: verbindlicher Implementierungsplan Milestone 0–8
- `METHODOLOGY.md`: Planungsstand Kennzahlen/Bewertung/Scoring/
  Zukunftsanalyse/Backtesting-Prinzipien
- `SECURITY.md`: Planungsstand Sicherheitsrichtlinie

**Geänderte Dateien:** ausschließlich neue Dateien unter
`investment-analyzer/` (keine bestehenden Repo-Dateien verändert).

**Tests:** keine (reine Dokumentation, kein Code in Milestone 0).

**Offene Risiken:**
- EU/DE-Meldungsabdeckung strukturell schwächer als USA in der
  Kostenlos-Variante (bekannte, dokumentierte Lücke, siehe ADR-9).
- Konkrete Schwellenwerte (Mindestmarktkapitalisierung, Mindestliquidität,
  Mindestkonfidenz für Top-10) sind als Platzhalter benannt, aber noch
  nicht zahlenmäßig festgelegt — folgt in Milestone 1/4.

**Nächster Schritt:** siehe `NEXT_STEPS.md`.

## Milestone 1 — Grundgerüst

**Status: abgeschlossen.**

Umgesetzt (Hauptagent/project-orchestrator, sequenziell ohne
Parallelisierung — die Teilschritte waren eng gekoppelt: Config, DB und
UI bauen direkt aufeinander auf):

- **Tooling:** `pyproject.toml` (Python 3.12+, FastAPI/Streamlit/
  SQLAlchemy/Alembic/httpx/pandas/numpy/pydantic/Plotly/Playwright/
  APScheduler/keyring/cryptography/openpyxl/reportlab), `.venv`
  angelegt und alle Abhängigkeiten installierbar/importierbar geprüft;
  ruff + mypy konfiguriert.
- **Paketstruktur:** `src/investment_analyzer/{connectors, normalization,
  entity_resolution, fundamentals, valuation, news, risk, scoring,
  backtesting, reports, ui, audit, config, db}` gemäß ADR-3/ADR-11.
- **Konfigurationssystem:** `config/models.py` (`NutzerProfil` mit allen
  Auftrag-§2-Feldern, Validierung), `config/defaults.py`
  (abgestimmte Startwerte), `config/settings.py` (`AppSettings`,
  SQLite-Standard-DB-URL), `config/store.py` (atomare JSON-Persistierung).
- **SecretStore:** `config/secrets.py` — `KeyringSecretStore` (OS-Keyring)
  mit Smoke-Test, `EncryptedFileSecretStore` (Fernet, PBKDF2 aus
  Master-Passwort) als Fallback, `get_secret_store()` wählt automatisch;
  bewusst KEIN unverschlüsselter Klartext-Fallback (ADR-5).
- **Datenbankschema:** `db/` (Base, Engine-/Session-Factory,
  dialektunabhängige UUID/UTC-Hilfen), Provenienz-Modelle `Entity`/
  `EntityIdentifier` (`entity_resolution`), `Source` (`connectors`),
  `DataPoint` (`normalization`, append-only, Point-in-time-fähig),
  `AuditLogEntry` (`audit`) gemäß ADR-6. Erste Alembic-Migration
  erzeugt und gegen SQLite verifiziert (Upgrade + Downgrade,
  automatisiert per Subprozess-Test).
- **Logging/Audit:** `audit/logging_setup.py` (Konsole + rotierende
  Logdatei), `audit/redaction.py` (Best-effort-Secret-Redaction in
  Logs), `audit/logger.py` (`AuditLogger` schreibt `AuditLogEntry`).
- **UI:** `ui/app.py` (Streamlit, Seite „Start/Datenstatus" +
  Ersteinrichtungsdialog gemäß Auftrag §2, Haftungsausschluss sichtbar,
  zeigt nur echte DB-Zahlen — keine Platzhalter-Marktdaten), Logik
  getrennt in `ui/bootstrap.py`, `ui/status.py`, `ui/profile_form.py`
  (ADR-12). Manuell mit echtem `streamlit run` verifiziert (HTTP 200)
  und zusätzlich per `streamlit.testing.v1.AppTest` automatisiert getestet.
- **Windows-Start:** `start.ps1` (Python-3.12-Erkennung, venv, Install,
  `alembic upgrade head`, Streamlit-Start), `start.bat` (Doppelklick-
  Wrapper), `scripts/run-tests.ps1` (ruff+mypy+pytest für Windows-Tester).
- **Doku:** `README.md` (Projektübersicht, Startanleitung), ADR-11/ADR-12
  in `DECISIONS.md`.

**Tests:** 50 automatisierte Tests (`pytest`), alle grün — deutlich über
dem Abnahmekriterium aus Auftrag §15 (mind. 30). Abdeckung: Nutzerprofil-
Validierung, Profil-Persistierung, SecretStore (beide Backends inkl.
Fehlerfällen), DB-Modelle inkl. Point-in-time-Query (Beleg für
Look-ahead-Freiheit), echte Alembic-Migration (Upgrade+Downgrade per
Subprozess), Audit-Log, Log-Redaction, UI-Bootstrap/-Status/-Formular-
Logik sowie End-to-End-Smoke-Tests der Streamlit-Seite (mit/ohne Profil,
fehlende Migration). `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
(siehe `README.md` → Projektstruktur für die vollständige Übersicht).

**Offene Risiken:**
- PostgreSQL-Pfad (Produktionsoption laut Auftrag §4/ADR-2) ist im Code
  dialektunabhängig vorbereitet, aber in dieser Sandbox-Umgebung nicht
  gegen eine echte PostgreSQL-Instanz getestet (kein Docker verfügbar).
  Nachholen, sobald eine PostgreSQL-Instanz verfügbar ist (spätestens
  Milestone 8, Abnahme).
- Die Streamlit-Oberfläche wurde nicht in einem echten Browser
  bedient (Sandbox ohne Browser-UI), sondern per `AppTest` (Headless-
  Skriptausführung) und per echtem `streamlit run` + HTTP-200-Check
  verifiziert. Ein Klick-/Browsertest steht noch aus.
- Konkrete Zahlenwerte für Mindestmarktkapitalisierung u. Ä. sind
  Startvorschläge; endgültige Feinjustierung erfolgt nutzerseitig über
  den Ersteinrichtungsdialog.

**Nächster Schritt:** Milestone 2 (Datenbeschaffung) gemäß `PLAN.md` —
siehe `NEXT_STEPS.md`.

## Milestone 2 — Datenbeschaffung

**Status: Implementierung abgeschlossen; Live-Verifikation mit realen
Daten in dieser Sandbox nicht möglich (siehe „Offene Risiken").**

Umgesetzt (Hauptagent/project-orchestrator, sequenziell — die Schritte
bauen aufeinander auf: Grundgerüst → Connectoren → Persistenz →
Ingestion):

- **Connector-Grundgerüst** (`connectors/base.py`, `errors.py`,
  `ssrf.py`, `rate_limiter.py`, `cache.py`): Timeout, exponentieller
  Retry-Backoff, injizierbarer Sliding-Window-Rate-Limiter,
  dateibasierter Cache mit TTL (abgelaufene Einträge werden NIE als
  aktuell zurückgegeben), SSRF-Schutz mit Host-Allowlist UND
  DNS-Rebinding-Prüfung (injizierbarer Resolver), einheitliches
  Fehlerprotokoll. Trennung von `params` (öffentlich, landet in der
  gespeicherten Provenienz-URL) und `secret_params` (z. B. API-Keys —
  nie in URL/Cache/Logs, siehe ADR-13).
- **SEC-EDGAR-Connector** (`connectors/sec_edgar.py`): Ticker→CIK-
  Auflösung über die offizielle Ticker-Liste, Submissions-Endpoint
  (Firmenname, Ticker/Börsen, jüngste Einreichungen), XBRL-
  Company-Concept-Endpoint (einzelne Kennzahl über alle Perioden,
  bereits mit Berichtsperiode/Einreichungsdatum/Accession Number —
  vollständige Provenienz gemäß Auftrag §5). Pflicht-User-Agent mit
  Kontaktadresse.
- **Alpha-Vantage-Connector** (`connectors/alpha_vantage.py`):
  `GLOBAL_QUOTE`-Kurs-Snapshot. Besonderheit beachtet: Alpha Vantage
  meldet Rate-Limits/Fehler als HTTP 200 mit `"Note"`/`"Information"`/
  `"Error Message"`-Feld statt als Fehlerstatus — wird explizit erkannt
  und in `ConnectorRateLimitedError`/`ConnectorValidationError`
  übersetzt. Free-Tier-Rate-Limit (5/Minute) als Default.
- **Source-Seeding** (`connectors/seed.py`): idempotentes Anlegen/
  Aktualisieren der `Source`-Zeilen für beide Connectoren.
- **Entity-Resolution-Service** (`entity_resolution/service.py`):
  `find_or_create_entity` verlangt mindestens eine stabile Kennung
  (ISIN, LEI oder CIK) — ein Ticker allein wird mit `ValueError`
  abgelehnt (Auftrag §5). Bestehende Entities werden über die stabile
  Kennung wiedergefunden, fehlende Kennungen ergänzt, ohne den Namen
  bei einem Treffer stillschweigend zu überschreiben.
- **Ingestion** (`normalization/ingest.py`): `ingest_sec_company_concept`
  wandelt XBRL-Fakten in `DataPoint`-Zeilen um (inkl. konstruierter
  EDGAR-Einreichungs-Index-URL als direktem Beleglink), idempotent über
  (Berichtsperiode, Accession Number) — eine neue Einreichung derselben
  Periode (Restatement) erzeugt eine zusätzliche Zeile statt die alte zu
  überschreiben (append-only, ADR-6, dediziert getestet).
  `ingest_alpha_vantage_quote` wandelt einen Kurs-Snapshot um; da
  `GLOBAL_QUOTE` keine Währung liefert, wird `currency` bewusst auf
  `None` gesetzt (keine geratene Annahme, Auftrag §11) und
  Qualität/Konfidenz entsprechend reduziert (0,6 statt 0,95).

**Tests:** 66 neue Tests (insgesamt 116, alle grün) — Connector-
Grundgerüst (Cache/Rate-Limit/SSRF/Retry/Fehlerfälle inkl. Secret-Leak-
Test), SEC-EDGAR- und Alpha-Vantage-Connector (gemockte, realistisch
strukturierte Antworten inkl. Alpha-Vantage-200er-Fehlerfälle),
Source-Seeding, Entity-Resolution (inkl. „zwei Firmen, gleicher Ticker,
verschiedene Börsen"), Ingestion (Provenienzfelder, Idempotenz,
Restatement-Verhalten). `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module in `connectors/`, `entity_resolution/service.py`,
`normalization/ingest.py`, zugehörige Tests unter `tests/`.

**Offene Risiken:**
- **Live-Verifikation mit 10 realen Unternehmen (Abnahmekriterium)
  nicht erbracht.** In dieser Sandbox-Entwicklungsumgebung blockiert die
  Egress-Policy des Umgebungs-Proxys ausgehende Verbindungen zu
  `www.sec.gov`/`data.sec.gov` und `www.alphavantage.co` (verifiziert:
  `curl` → `403 CONNECT tunnel failed, response 403` für beide Hosts,
  2026-09-07). Die gesamte Connector-Logik ist gegen realistisch
  strukturierte, gemockte Antworten getestet, aber ein echter
  End-to-End-Abruf gegen die realen APIs steht aus. Muss in einer
  Umgebung mit echtem Internetzugang nachgeholt werden (z. B. beim
  Nutzer über `start.ps1`).
- Für Alpha Vantage liegt kein echter API-Schlüssel vor (wurde vom
  Nutzer bisher nicht bereitgestellt); der öffentliche „demo"-Schlüssel
  funktioniert nur für das Testsymbol IBM, nicht für zehn beliebige
  Unternehmen.
- Bekannte, bereits in ADR-9 dokumentierte Lücke: keine gleichwertige
  kostenlose Meldungs-Primärquelle für DE/EU (nur SEC EDGAR/USA
  angebunden).
- Alpha-Vantage-Kurse werden ohne Währungsangabe gespeichert (API-
  Limitierung); Auflösung der Notierungswährung über Börsen-Metadaten
  ist für Milestone 3 vorgesehen (siehe `TODO.md`).

**Nächster Schritt:** Milestone 3 (Fundamentalanalyse) gemäß `PLAN.md`
— siehe `NEXT_STEPS.md`. Vor produktivem Einsatz: Live-Verifikation der
Connectoren in einer Umgebung mit Internetzugang nachholen.

## Milestone 3 — Fundamentalanalyse

**Status: Implementierung abgeschlossen; Verifikation an drei realen
Unternehmen mangels Internetzugang nicht möglich (siehe „Offene
Risiken", dieselbe Einschränkung wie in Milestone 2).**

Umgesetzt (Hauptagent/project-orchestrator, sequenziell — jeder Schritt
baut auf dem vorigen auf: Vokabular → Berechnungskern → Zeitreihen →
Klassifikation → Warnsignale → Orchestrierung):

- **Kennzahlen-Vokabular** (`fundamentals/metrics.py`): 22 kanonische
  Kennzahlen (`Metric`-Enum) mit Mapping von gängigen US-GAAP-XBRL-Tags.
  `normalization/ingest.py::ingest_sec_company_concept` löst nun jeden
  XBRL-Tag verbindlich auf eine kanonische Kennzahl auf (oder verlangt
  einen expliziten Override) — ein unbekannter Tag wird nicht mehr unter
  einem uneinheitlichen Rohnamen gespeichert.
- **Berechnungskern** (`fundamentals/calculations.py`): reine,
  DB-unabhängige Funktionen für CAGR/Wachstumsraten (1/3/5/10 Jahre),
  Brutto-/operative/Nettomarge inkl. Stabilität (Stichproben-
  Standardabweichung), ROE, ROIC (mit explizit sichtbarem
  Steuersatz-Parameter, kein stiller Default), Cash Conversion,
  Investitionsquote, Working Capital, EBITDA-Näherung, Nettoverschuldung/
  EBITDA, Zinsdeckung, Ausschüttungsquote, Aktienverwässerung. Grundsatz
  durchgängig: fehlende Eingabe → `None`, niemals eine geschätzte Zahl.
- **Zeitreihen-Repository** (`fundamentals/series.py`): point-in-time-
  fähige Abfrage von `DataPoint`-Zeitreihen je Entity/Kennzahl; robuste,
  metadatenfreie Trennung von Jahres- und Quartalswerten (Greedy-
  Rückwärts-Auswahl nach Mindestabstand statt auf ein zusätzliches
  „FY"/„Q1"-Feld angewiesen zu sein).
- **SIC-Klassifikation + Peer-Gruppen** (`entity_resolution/models.py`
  erweitert um `sic_code`/`sic_description`, neue Alembic-Migration
  gegen SQLite verifiziert; `connectors/sec_edgar.py::SecSubmissions`
  liefert SIC jetzt mit; `normalization/ingest.py::
  update_entity_classification`; `fundamentals/peers.py::find_peers`).
  Peer-Zuordnung bewusst nur branchenbasiert — Größenähnlichkeit
  (Marktkapitalisierung) folgt erst mit Milestone 4.
- **Warnsignale** (`risk/warning_signals.py`): sechs zahlenbasierte
  Checks (sinkender Cashflow trotz steigendem Gewinn, starke
  Verwässerung, hohe aktienbasierte Vergütung, ungewöhnliches
  Forderungs-/Vorratswachstum, verspätete Einreichung). Acht aus
  Auftrag §6 geforderte, aber textbasierte Signale (Going-Concern,
  Rechtsstreitigkeiten, Sanktionen, Cybervorfälle u. a.) werden explizit
  als noch nicht implementierbar aufgeführt (`NOT_YET_IMPLEMENTABLE_
  SIGNALS`) statt stillschweigend als „unauffällig" vorgetäuscht.
- **FundamentalsReport-Orchestrierung** (`fundamentals/report.py`):
  fasst Wachstum, Margen, Renditen, Cashflow, Verschuldung,
  Ausschüttung/Verwässerung, Warnsignale und Peers zu einem Bericht
  zusammen; `data_completeness`/`missing_fields` machen sichtbar, wie
  viele der 33 versuchten Kennzahlen tatsächlich berechnet werden
  konnten (Auftrag §7: fehlende Daten reduzieren die Aussagekraft,
  werden nicht neutral mit Null bewertet).

**Tests:** 66 neue Tests (insgesamt 182, alle grün) — u. a. 33
Handrechnungs-Tests für den Berechnungskern mit exakt nachrechenbaren
Zahlen (z. B. 1,1³ = 1,331 für 10 % CAGR über 3 Jahre), vier
Integrationstests für `FundamentalsReport` mit drei durchgängig
hand-verifizierten synthetischen Beispielunternehmen (vollständige
Kennzahlen, Datenlücken-Fall, Peer-Zuordnung) plus ein Point-in-time-
Test. `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module in `fundamentals/`, `risk/warning_signals.py`, Erweiterung
von `entity_resolution/models.py` und `connectors/sec_edgar.py`, neue
Alembic-Migration, zugehörige Tests unter `tests/`.

**Offene Risiken:**
- **Verifikation an drei realen Unternehmen (Abnahmekriterium) nicht
  erbracht.** Wie bereits in Milestone 2 dokumentiert, ist in dieser
  Sandbox kein Zugriff auf `sec.gov` möglich. Die Handrechnungs-Tests
  verwenden daher bewusst gekennzeichnete, synthetische Beispieldaten,
  die die Korrektheit der Formeln beweisen, aber die Verifikation gegen
  tatsächlich veröffentlichte Geschäftszahlen nicht ersetzen. Nachzuholen
  in einer Umgebung mit Internetzugang.
- Nur eine Teilmenge der Auftrag-§6-Warnsignale ist implementierbar ohne
  Volltextauswertung der Filings (siehe `NOT_YET_IMPLEMENTABLE_SIGNALS`
  in `risk/warning_signals.py`); die übrigen acht bleiben bis
  Milestone 5 (Nachrichtenanalyse) bzw. einer künftigen
  Filing-Text-Auswertung offen.
- Peer-Gruppen basieren aktuell ausschließlich auf dem SIC-Code, ohne
  Größenfilter (keine Marktkapitalisierungsdaten vor Milestone 4).
- `FundamentalsReport.data_completeness`/`missing_fields` sind ein
  einfacher Konfidenz-Indikator für Milestone 3 — das vollständige,
  gewichtete Scoring mit Ausgabeklassen („Vertieft prüfen" etc.) ist
  explizit Aufgabe von Milestone 4.

**Nächster Schritt:** Milestone 4 (Bewertung und Score) gemäß `PLAN.md`
— siehe `NEXT_STEPS.md`.

## Milestone 4 — Bewertung und Score

**Status: Implementierung abgeschlossen; Verifikation mit realen
Marktdaten/DCF-Annahmen mangels Internetzugang nicht möglich (dieselbe
Einschränkung wie Milestone 2/3, siehe „Offene Risiken").**

Umgesetzt (Hauptagent/project-orchestrator, sequenziell — Multiples →
DCF → Valuation-Orchestrierung → Scoring bauen aufeinander auf):

- **Multiples** (`valuation/multiples.py`): KGV, EV/EBITDA, EV/EBIT,
  KBV, Kurs/FCF, FCF-Rendite. Bei negativem/Null-Nenner (z. B. negativer
  Gewinn) bewusst `None` statt einer irreführenden Zahl.
- **DCF-Modell** (`valuation/dcf.py`): zweistufiges Discounted-Cashflow-
  Modell (explizite Projektionsjahre + Gordon-Growth-Terminalwert).
  Dokumentierte Vereinfachung: konstante FCF-Marge auf den projizierten
  Umsatz statt einzeln modelliertem Capex/Working-Capital/Abschreibungs-
  pfad. `run_dcf` liefert `None` bei rechnerisch unzulässigen Annahmen
  (WACC ≤ Terminalwachstum oder ≤ 0) statt eines Fantasiewerts.
  `build_sensitivity_matrix` deckt alle vier in Auftrag §6 genannten
  Dimensionen über zwei 2D-Matrizen ab (Wachstum×WACC,
  Marge×Terminalwachstum). `safety_margin()` = (unteres Band −
  aktueller Kurs) / unteres Band, wie in `METHODOLOGY.md` festgelegt.
- **Valuation-Report-Orchestrierung** (`valuation/report.py`):
  Multiples aus aktuellem Kurs (`Metric.PRICE_CLOSE`, neu im
  Kennzahlen-Vokabular ergänzt, siehe unten) + Fundamentaldaten; Peer-
  Multiples über dieselbe SIC-Peer-Gruppe wie in Milestone 3, ohne
  erfundene Werte für Peers ohne Datenlage; Standard-DCF-Szenarien
  (`derive_default_scenarios`) leiten Wachstum/Marge deterministisch
  aus der 3-/1-Jahres-Historie ab, WACC/Terminalwachstum sind explizit
  gekennzeichnete Annahmen (Default 9 % / 2 %) — liefert `None` statt
  einer erfundenen Annahme, wenn die Historie nicht reicht.
- **Kennzahlen-Vokabular erweitert:** `Metric.PRICE_CLOSE` ergänzt
  (Marktdaten, weder Fluss- noch Bestandsgröße), `ingest_alpha_vantage_
  quote` nutzt es jetzt statt eines Roh-Strings — nutzt dieselbe
  point-in-time-Zeitreihen-Infrastruktur wie die Fundamentaldaten.
  `fundamentals/series.py::get_latest_value` ergänzt für Kennzahlen ohne
  Jahresrhythmus (Kurse werden täglich beobachtet, nicht jährlich).
- **Scoring** (`scoring/score.py`): exakte Umsetzung der Auftrag-§7-
  Startgewichtung (25/20/15/15/10/5/5/5). Jede Teilkennzahl wird über
  eine dokumentierte lineare Skala auf 0–100 abgebildet
  (`_linear_score`), nie durch ein Sprachmodell bewertet. Zwei
  Komponenten („Wettbewerbsvorteil", „Nachrichten und Katalysatoren")
  sind strukturell nicht berechenbar und werden explizit als nicht
  verfügbar markiert statt mit 0 bewertet — `coverage` (max. 85 % in
  dieser Milestone) macht das sichtbar. Risiken aus den Milestone-3-
  Warnsignalen wirken als sichtbare, benannte Punktabzüge. Konfidenz-
  Schwellen (`coverage`, `data_completeness`) stufen unsichere
  Kandidaten auf „Beobachten"/„Datenlage unzureichend" herab, auch wenn
  der reine Score hoch wäre. Bis zu fünf positive Faktoren, fünf
  Risiken, Gegenargumente und Ungültigkeitsbedingungen werden
  deterministisch aus den berechneten Werten generiert. Verbotene
  Formulierungen aus Auftrag §7 kommen nirgends vor (dediziert
  getestet).

**Tests:** 59 neue Tests (insgesamt 241, alle grün) — Multiples-
Handrechnungen, ein exakt von Hand nachrechenbarer DCF-Fall
(Wachstum = WACC, wodurch sich jede Jahresdiskontierung exakt zu
`base_revenue × fcf_margin` kürzt), Sensitivitätsmatrix-Tests,
Valuation-Report-Integrationstests (inkl. Peer-Vergleich und
Datenlücken-Fall), sowie Scoring-Tests auf zwei Ebenen (reine
Komponentenfunktionen mit von Hand gebauten Berichten + eine
End-to-End-Datenbankprüfung). `ruff check .` und `mypy src` beide
fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module `valuation/multiples.py`, `valuation/dcf.py`,
`valuation/report.py`, `scoring/score.py`, `scoring/__init__.py`;
Erweiterungen in `fundamentals/metrics.py`, `fundamentals/series.py`,
`normalization/ingest.py`; zugehörige Tests unter `tests/`.

**Offene Risiken:**
- **Verifikation mit realen Marktdaten (Abnahmekriterium „DCF-
  Handrechnung stimmt") nur mit synthetischen Daten erbracht.** Wie in
  Milestone 2/3 blockiert die Egress-Policy dieser Sandbox den Zugriff
  auf `sec.gov`/`alphavantage.co`. Die DCF-/Multiples-Arithmetik ist
  exakt hand-verifiziert, aber nicht gegen echte Kurs- und
  Geschäftsberichtsdaten realer Unternehmen geprüft. Nachzuholen in
  einer Umgebung mit Internetzugang und echtem Alpha-Vantage-Schlüssel.
- Scoring-Komponente „Bewertung/Sicherheitsmarge" basiert in
  Milestone 4 ausschließlich auf der DCF-Sicherheitsmarge — ein
  historischer Multiples-Vergleich (eigene 5-/10-Jahres-Historie) ist
  noch nicht möglich, da bislang keine mehrjährige Kurshistorie
  akkumuliert wurde (Alpha Vantage GLOBAL_QUOTE liefert nur den
  aktuellen Kurs je Abruf).
- Scoring-Komponente „Management/Kapitalallokation" ist bewusst schmal
  (nur Aktienverwässerung) — Insidertransaktionen und Vergütungsdaten
  sind über keine angebundene Quelle strukturiert verfügbar.
- WACC-Standardwert (9 %) ist eine grobe marktübliche Schätzung, kein
  unternehmensspezifisch hergeleiteter Kapitalkostensatz (z. B. via
  CAPM mit Beta) — Verbesserung als späterer Punkt vorgemerkt.
- `ScoreResult`/`ValuationReport`/`FundamentalsReport` werden aktuell
  nur zur Laufzeit berechnet, nicht in der Datenbank persistiert oder
  ins Audit-Log geschrieben — das „nachvollziehbar geloggt" aus dem
  Abnahmekriterium ist über die vollständig in `ScoreResult`
  eingebetteten Gewichte/Notizen erfüllt, eine dauerhafte
  Audit-Log-Persistenz folgt mit der UI-/Rangliste (Milestone 6/8a).

**Nächster Schritt:** Milestone 5 (Nachrichtenanalyse) gemäß `PLAN.md`
— siehe `NEXT_STEPS.md`.

## Milestone 5 — Nachrichtenanalyse

**Status:** Implementierung abgeschlossen (2026-09-07).

**Umgesetzt:**

- Connector-Grundgerüst (`connectors/base.py`) um `get_text()` erweitert
  (Rohtext statt JSON, für Quellen ohne JSON-API), ohne `get_json()`-
  Verhalten zu ändern — beide teilen sich jetzt eine gemeinsame `_get()`-
  Kernmethode mit austauschbarem Parser.
- GDELT-DOC-2.0-Connector (`connectors/gdelt.py`): Volltextsuche nach
  Firmenname, kein API-Schlüssel nötig, konservativ gedrosselt (kein
  dokumentiertes Rate Limit bei GDELT).
- Generischer IR-RSS-Connector (`connectors/ir_rss.py`): RSS-2.0- und
  Atom-Parsing über `xml.etree` (Standardbibliothek, keine neue
  Abhängigkeit). Jede Instanz ist an genau eine Feed-URL gebunden; die
  Host-Allowlist wird daraus zur Laufzeit abgeleitet — der SSRF-/
  DNS-Rebinding-Schutz bleibt davon unabhängig vollständig aktiv.
- `NewsItem`-ORM-Modell (`news/models.py`, ADR-18) mit Provenienz
  (Quelle, URL, Abrufzeitpunkt UTC, Inhalts-Hash) plus Alembic-Migration;
  Source-Seeding um `gdelt` und `ir_rss` erweitert.
- HTML-Bereinigung zu reinem Klartext (`news/sanitize.py`): Skript-/
  Stilinhalte werden verworfen, Entities aufgelöst, auf einen kurzen
  Ausschnitt gekürzt (kein Artikel-Volltext, Auftrag §12/Fair-Use).
- Deterministische, regelbasierte Klassifikation (`news/classification.py`,
  ADR-19): Quellqualität (Unternehmensmeldung/unabhängiger
  Bericht/Kommentar — IR-RSS ist per Definition eine Unternehmensmeldung)
  und Ereignistyp (Earnings, M&A, Management, Recht/Regulierung,
  Kapitalmarkt, Produkt/Betrieb, Cyber/Lieferkette, Sonstiges) — beide
  rein lexikalisch, nie durch ein Sprachmodell.
- Idempotente Ingestion (`news/ingest.py`): URL-Normalisierung
  (Fragment + bekannte Tracking-Parameter entfernt) vor dem
  Dedup-Hashing, damit dieselbe Meldung nicht mehrfach gespeichert wird.
- Rein funktionales Ereignis-Clustering (`news/clustering.py`): gleicher
  Ereignistyp + zeitliche Nähe + Titel-Ähnlichkeit
  (`difflib.SequenceMatcher`, Standardbibliothek) — keine Embeddings,
  kein Sprachmodell, deterministisch nachvollziehbar.
- `NewsReport`-Orchestrierung (`news/report.py`): liest `NewsItem`-Zeilen
  einer Entity, clustert sie, zählt Meldungen ohne bekanntes Datum.

**Bewusste, dokumentierte Lücke:** Die im Auftrag genannte
„KI-Zusammenfassung mit Quellenverweis" wird NICHT umgesetzt — in dieser
Entwicklungsumgebung gibt es weder eine Claude-API-Anbindung noch einen
dafür vorgesehenen `SecretStore`-Schlüssel. Die Datengrundlage ist
gelegt (`NewsCluster.items` referenziert jede Quelle zwingend über
`url`); die eigentliche Erzeugung ist für die UI-/Reports-Schicht
(Milestone 6+) vorgemerkt, inklusive der Pflicht, den bereinigten Text
weiterhin als nicht vertrauenswürdige Nutzdaten zu behandeln, nie als
Anweisung (Auftrag §12). Ebenfalls offen: die Zuordnung „welche
IR-RSS-Feed-URL gehört zu welcher `Entity`" ist nicht automatisiert —
der Connector liefert nur den Abruf-/Parse-Mechanismus für eine
gegebene URL, keine Feed-Erkennung.

**Tests:** 60 neue Tests (insgesamt 301, alle grün) — Connector-Tests
mit Mock-HTTP (inkl. kaputtem XML/JSON als Fehlerfall), Idempotenz-/
Dedup-Tests gegen die Datenbank (inkl. Tracking-Parameter-Normalisierung),
hand-nachvollziehbare Klassifikations- und Clustering-Fälle (u. a.
Multi-Source-Cluster-Erkennung). `ruff check .` und `mypy src` beide
fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module `connectors/gdelt.py`, `connectors/ir_rss.py`,
`news/models.py`, `news/sanitize.py`, `news/classification.py`,
`news/ingest.py`, `news/clustering.py`, `news/report.py`; Erweiterungen
in `connectors/base.py`, `connectors/seed.py`, `db/__init__.py`; neue
Alembic-Migration `news_items`; zugehörige Tests unter
`tests/connectors/`, `tests/news/`.

**Offene Risiken:**
- **Verifikation der Duplikaterkennung an einem realen Testset**
  (Auftrag-Abnahmekriterium) nur mit synthetischen Daten erbracht. Wie
  in Milestone 2/3/4 blockiert die Egress-Policy dieser Sandbox den
  Zugriff auf `api.gdeltproject.org` und beliebige IR-RSS-Hosts.
  Nachzuholen in einer Umgebung mit Internetzugang.
- KI-Zusammenfassung mit Quellenverweis fehlt vollständig (s. o.) —
  technische Grundlage vorhanden, Erzeugung nicht implementiert.
- Quellqualitäts-Heuristik für „Kommentar" beruht auf einer kleinen,
  bewusst unvollständigen Domain-Liste (`classification.py::
  KNOWN_COMMENTARY_DOMAINS`) — keine redaktionelle Prüfung.
- IR-RSS-Feed-URL-zu-Entity-Zuordnung ist nicht automatisiert (s. o.).
- Clustering ist eine lexikalische Heuristik (Titel-Ähnlichkeit) ohne
  semantisches Verständnis — kann inhaltlich verwandte Meldungen mit
  sehr unterschiedlichem Wortlaut verpassen (bewusst konservativ: lieber
  zu viele Cluster als fälschlich zusammengeführte Ereignisse).

**Nächster Schritt:** Milestone 6 (Portfolio und Exporte) gemäß
`PLAN.md` — siehe `NEXT_STEPS.md`.

## Milestone 6 — Portfolio und Exporte

**Status:** Implementierung abgeschlossen (2026-09-07).

**Umgesetzt:**

- Neues Modul `portfolio/` (ADR-20, über die ursprüngliche
  Auftrag-§4-Modulliste hinaus ergänzt): `WatchlistEntry`/
  `PortfolioPosition`-ORM-Modelle (Bestands-Snapshot, keine
  Transaktionshistorie) + Alembic-Migration.
- CSV-Import (`portfolio/csv_import.py`) für Watchlist und Portfolio —
  nutzt dieselbe Entity-Auflösung wie jede andere Ingestion (nie Ticker
  allein, Auftrag §5), sammelt Fehler zeilengenau statt abzubrechen
  oder still zu überspringen, ist idempotent (erneuter Import
  aktualisiert bestehende Zeilen).
- Konzentrationsanalyse (`portfolio/concentration.py`): Branchen-/
  Länder-Konzentration nach Marktwert, nur berechenbar bei einheitlicher
  Bestandswährung (sonst `computable=False` statt Fantasiewert);
  Währungs-Exposure separat und ohne Prozentangabe über Währungsgrenzen
  hinweg. „Faktor-Konzentration" explizit als nicht berechenbar
  dokumentiert (`NOT_YET_IMPLEMENTABLE_CONCENTRATIONS`).
- Positionsgrößen-Bandbreite (`portfolio/position_sizing.py`) —
  unverbindlich, nie ein einzelner empfohlener Wert (Auftrag §8).
- Konfigurierbare `PortfolioAssumptions` (`portfolio/assumptions.py`):
  Transaktionskosten, Steuersatz, Mindestliquidität, mit dokumentierten
  Default-Näherungen.
- Historischer Max-Drawdown und Pearson-Korrelation der Tagesrenditen
  (`portfolio/risk_metrics.py`) — reine Funktionen mit expliziter
  „Datenlage unzureichend"-Markierung bei zu wenigen Kurspunkten.
- `PortfolioReport`-Orchestrierung (`portfolio/report.py`): liest
  Bestände + jüngste Kurse, wendet alle obigen Bausteine an, dokumentiert
  jede Lücke explizit in `gaps` statt sie wegzulassen.
- Neues Modul `reports/` (bisher leerer Stub) mit `ReportBundle`
  (ADR-21) als einziger Quelle der Wahrheit für alle Exportformate:
  aggregiert FundamentalsReport/ValuationReport/ScoreResult/NewsReport
  (`reports/bundle.py`), JSON-Export (`json_export.py`), Excel-Export
  mit allen sieben in Auftrag §10 geforderten Tabellenblättern
  (Zusammenfassung, Kennzahlen, Bewertung, Risiken, Nachrichten,
  Quellen, Annahmen — `excel_export.py`, `openpyxl`), PDF-Export
  (`pdf_export.py`, `reportlab`). Excel- und PDF-Export lesen
  ausschließlich aus demselben `report_bundle_to_dict()` — zwei
  Exportformate können dadurch strukturell keine unterschiedlichen
  Werte zeigen. Formel-Injection-Schutz (Auftrag §12) für Zellwerte aus
  externen Quellen (Nachrichtentitel/-URLs) im Excel-Export.

**Bewusste, dokumentierte Lücke:** Das Milestone-6-Abnahmekriterium
„Export enthält exakt dieselben Werte wie die UI-Ansicht
(automatisierter Abgleich)" ist strukturell, aber nicht live erfüllt —
es existiert noch keine Streamlit-Detailseite, die Berichte anzeigt
(nur die Start/Datenstatus-Seite aus Milestone 1). Der automatisierte
Abgleich kann erst erfolgen, sobald diese UI-Seite gebaut ist
(voraussichtlich Milestone 8). Die ADR-21-Architekturentscheidung (ein
einziges `ReportBundle` als Datenquelle) stellt sicher, dass eine
künftige UI-Seite automatisch dieselben Werte zeigt, sofern sie
ebenfalls von einem `ReportBundle` rendert.

**Tests:** 60 neue Tests (insgesamt 372, alle grün) — CSV-Import-
Fehlerfälle, hand-nachrechenbare Konzentrations-/Drawdown-/
Korrelations-Fälle (u. a. ein exakt konstruierter Fall mit Korrelation
= -1.0), PortfolioReport-Integrationstests gegen die Datenbank
(inkl. gemischte-Währungen-Lücke), ReportBundle-Konsistenztests (Score
aus dem Bundle ist bit-identisch mit einer unabhängigen
`compute_score`-Berechnung), JSON-Rundtrip-Test, Excel-Tabellenblatt-
Struktur- und Wertetests, PDF-Erzeugungstests (Magic-Bytes-Prüfung, da
kein PDF-Parser als Testabhängigkeit vorhanden ist). `ruff check .` und
`mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module `portfolio/` (models, csv_import, concentration,
position_sizing, assumptions, risk_metrics, report) und `reports/`
(bundle, json_export, excel_export, pdf_export); neue Alembic-Migration
`watchlist_entries`/`portfolio_positions`; Erweiterung in
`db/__init__.py`; zugehörige Tests unter `tests/portfolio/`,
`tests/reports/`.

**Offene Risiken:**
- **UI-vs.-Export-Abgleich nicht live nachprüfbar** (s. o.) — strukturell
  durch ADR-21 abgesichert, aber erst mit einer echten Report-UI-Seite
  (Milestone 8) tatsächlich testbar.
- Keine FX-Umrechnung: Konzentrationsanalyse bei gemischten
  Bestandswährungen liefert `computable=False` statt eines Werts.
- Korrelation/Drawdown liefern in dieser Sandbox mangels Kurshistorie
  (Alpha Vantage GLOBAL_QUOTE nur Einzelabruf-Snapshots) für die
  meisten synthetischen Testfälle „Datenlage unzureichend" — realistisch
  auch im späteren Produktivbetrieb, bis genug Kurspunkte akkumuliert
  sind.
- IR-RSS-Feed-URL-zu-Entity-Zuordnung weiterhin nicht automatisiert
  (aus Milestone 5 offen).
- PDF-Export rendert Nachrichtentitel/-URLs bewusst nicht (nur
  aggregierte Zahlen) — Sicherheitsentscheidung gegen reportlabs
  Markup-Parsing für externen Text (siehe ADR-21); bei Bedarf später als
  reine Tabellen-Zellen (kein Markup-Parsing) nachrüstbar.
- Portfolio-Konzentration/-Positionsgrößen nutzen den zuletzt bekannten
  Kurs ohne Altersprüfung — ein sehr alter Kurs würde nicht gesondert
  markiert (kleinere Lücke, nicht behebbar ohne echte Marktdaten in
  dieser Sandbox zu testen).

**Nächster Schritt:** Milestone 7 (Backtesting) gemäß `PLAN.md` — siehe
`NEXT_STEPS.md`.

## Milestone 7 — Backtesting

**Status:** Implementierung abgeschlossen (2026-09-07).

**Umgesetzt:**

- Point-in-time-Universum (`backtesting/universe.py`, ADR-22): eine
  Entity gilt als „zum Stichtag bekannt", wenn mindestens ein
  `DataPoint` mit `retrieved_at_utc <= as_of` existiert — dieselbe
  Provenienz-Grundlage wie jede andere Point-in-time-Abfrage (ADR-6).
- Perioden-Rendite (`backtesting/period_return.py`): Kursänderung +
  geschätzte Dividende je Aktie (`DIVIDENDS_PAID / SHARES_DILUTED`,
  als Näherung dokumentiert) abzüglich Transaktionskosten
  (`portfolio.assumptions.PortfolioAssumptions`, Milestone 6).
- Train-/Validierungs-/Out-of-Sample-Split (`backtesting/splits.py`):
  reine, chronologische Dreiteilung eines Datumsbereichs.
- Kennzahlen (`backtesting/metrics.py`): CAGR, annualisierte
  Volatilität, Sharpe/Sortino (konfigurierbarer risikofreier Zins),
  Turnover. Maximaler Drawdown wird aus `portfolio/risk_metrics.py`
  (Milestone 6) wiederverwendet, nicht neu implementiert.
- Deterministische Top-N-Auswahlstrategie (`backtesting/strategy.py`):
  nutzt ausschließlich das bereits bestehende, feste Scoring-System
  (Milestone 4) — kein auf den Backtest-Zeitraum gefitteter Parameter,
  strukturelle Absicherung gegen Overfitting (Auftrag §9). Schließt
  Kandidaten mit `total_score is None` ODER Klassifikation „Datenlage
  unzureichend" aus (nicht `total_score` allein, da die
  Datenqualitäts-Komponente auch bei fehlenden Daten einen Zahlenwert
  liefert — beim ersten Testlauf entdeckt und korrigiert).
- Rebalancing-Engine (`backtesting/engine.py`): führt die Strategie
  über eine Folge von Stichtagen aus, gleichgewichtete Portfoliorendite
  je Periode, NAV-Zeitreihe. Positionen ohne berechenbaren Kurs werden
  je Periode ausgeschlossen, nicht geraten.
- `BacktestReport`-Orchestrierung (`backtesting/report.py`): aggregiert
  alle Kennzahlen, dokumentiert offene Lücken explizit
  (`NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES`).

**Abnahmekriterium „kein Look-ahead" — zweistufig nachgewiesen:**
1. Universums-Ebene (`tests/backtesting/test_universe.py`): ein
   Backtest-Universum zu einem Stichtag ist identisch, bevor und
   nachdem ein erst später bekannt gewordener Kandidat in die
   Datenbank aufgenommen wurde.
2. Vollständiger Backtest-Lauf (`tests/backtesting/test_engine.py::
   test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_
   backtest_ergebnis_nicht`): Auswahl UND Portfoliorendite einer
   bereits abgeschlossenen Periode sind bit-identisch, bevor und
   nachdem ein neuer, erst später bekannt gewordener Kandidat mit
   einem auffällig hohen Kurs hinzugefügt wurde.

**Bewusste, dokumentierte Lücken (ADR-22):**
- Kein Benchmark-/Index-Kursvergleich — keine Index-Datenquelle im
  Kostenlos-Paket angebunden (Alpha Vantage Free liefert nur
  Einzelwerte je Symbol). `build_backtest_report` akzeptiert optional
  eine extern gelieferte Benchmark-Renditereihe.
- Keine Währungsumrechnung — dieselbe strukturelle Lücke wie ADR-16/
  ADR-20.
- Unvollständiges Survivorship-Universum — keine systematische
  Delisting-Historie verfügbar; das Punkt-in-Zeit-Universum umfasst
  „was das System zum Stichtag bereits erfasst hatte", nicht „was zum
  Stichtag historisch am Markt existierte".
- Dividende je Aktie ist eine Schätzung (Gesamt-Dividende / verwässerte
  Aktienanzahl der zuletzt bekannten Jahresperiode), keine gemeldete
  Größe.

**Tests:** 61 neue Tests (insgesamt 425, alle grün) — Punkt-in-Zeit-
Universums-Tests, hand-nachrechenbare Perioden-Renditen/Kennzahlen
(u. a. CAGR/Sharpe/Sortino mit exakt konstruierten Beispielen),
Train/Validation/OOS-Split-Tests, Strategie-Rankingtest (starke vs.
schwache synthetische Firma), Engine-Integrationstests gegen die
Datenbank (inkl. der beiden Look-ahead-Nachweis-Tests),
BacktestReport-Tests. `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** ausschließlich unter `investment-analyzer/`
— neue Module in `backtesting/` (universe, period_return, splits,
metrics, strategy, engine, report); zugehörige Tests unter
`tests/backtesting/` (inkl. gemeinsamer Testdaten-Hilfsfunktionen in
`_fixtures.py`).

**Offene Risiken:**
- Verifikation mit echten Marktdaten/realer Benchmark-Kursreihe
  mangels Internetzugang in dieser Sandbox nicht möglich (dieselbe
  Einschränkung wie Milestone 2–6).
- Kein Index-/Benchmark-Datenquelle angebunden (s. o.) — Auftrag-§9-
  Anforderung „Ergebnisse gegen einfache Indizes vergleichen" ist nur
  strukturell (Parameter-Schnittstelle), nicht mit echten Daten erfüllt.
- Survivorship-Bias nicht vollständig ausgeschlossen (s. o.).
- Dividendenrendite ist eine grobe Jahres-Näherung, nicht periodengenau.
- Sharpe/Sortino nutzen einen konfigurierbaren, aber standardmäßig
  auf 0 gesetzten risikofreien Zins — keine automatisch bezogene
  Zinsreihe (z. B. aus EZB/FRED-Daten) hinterlegt.

**Nächster Schritt:** Milestone 8 (Sicherheit und Abnahme) gemäß
`PLAN.md` — siehe `NEXT_STEPS.md`.

## Milestone 8 — Sicherheit und Abnahme

**Status:** in Bearbeitung (2026-09-08). Security-Review abgeschlossen,
Ausfalltests/Windows-Setup/Benutzerhandbuch/Abnahme-Checkliste stehen
noch aus.

**Umgesetzt (Security-Review, siehe ADR-23):**

- Systematischer Abgleich jeder `SECURITY.md`-Behauptung mit dem
  tatsächlichen Codeverhalten (nicht nur mit der Absicht).
- **Drei echte Lücken gefunden und behoben:**
  1. Downloadgrößen-Begrenzung fehlte im Code trotz Dokumentation —
     `ConnectorConfig.max_response_bytes` (Default 10 MB) ergänzt,
     Prüfung in `connectors/base.py::_request_with_retry` vor jedem
     Parsing/Caching; übergroße Antwort → `ConnectorValidationError`
     ohne Retry, ohne Cache-Schreibung.
  2. `RedactingFilter` bereinigte nur `record.msg`, nicht
     `record.args` — ein Secret als %-Style-Platzhalter-Argument wäre
     unredigiert ins Log gelangt. Behoben: `record.args` (Tupel- und
     Dict-Form) läuft jetzt ebenfalls durch `redact()`.
  3. Der Auftrag-§12-Pflichthinweis existierte nur in der UI, nicht in
     den Berichtsexporten (JSON/Excel/PDF) — Auftrag §12 verlangt ihn
     „an JEDER Berichtsausgabe sichtbar". Behoben:
     `reports/bundle.py::MANDATORY_DISCLAIMER` als Pflichtfeld
     `ReportHeader.disclaimer`, gerendert in allen drei Exportformaten.
- **Ein Dokumentationsfehler korrigiert:** `SECURITY.md` behauptete,
  Redirects würden „nur innerhalb der Allowlist gefolgt" — tatsächlich
  (verifiziert per `inspect.signature`) folgt `httpx.Client` nie
  automatisch einem Redirect (`follow_redirects=False`, nie
  überschrieben). Strenger als dokumentiert, aber die Doku war
  sachlich falsch — korrigiert.
- **Verifiziert, keine Lücke:** Secrets-Handling (`SecretStore`),
  SSRF-Schutz (Allowlist + DNS-Rebinding-Prüfung), `.gitignore`-
  Ausschlüsse, Prompt-Injection-Schutz (kein LLM-Aufruf existiert
  aktuell im Code — `news/sanitize.py` entfernt HTML/Skripte bereits
  vor jeder Speicherung; erneut zu prüfen, sobald die KI-
  Zusammenfassung aus ADR-19 implementiert wird).
- `pip-audit`: „No known vulnerabilities found" (Stand 2026-09-08).

**Tests:** 10 neue Tests (insgesamt 435, alle grün) — 3 für die
Downloadgrößen-Begrenzung (`tests/connectors/test_base_connector.py`),
4 für die `record.args`-Redaction (`tests/audit/test_audit.py`), 3 für
den Pflichthinweis in allen drei Exportformaten
(`tests/reports/test_bundle.py`, `test_excel_export.py`,
`test_pdf_export.py`). `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte Dateien:** `connectors/base.py`, `audit/redaction.py`,
`reports/bundle.py`, `reports/excel_export.py`, `reports/pdf_export.py`,
`SECURITY.md`, zugehörige Tests.

**Umgesetzt (Ausfalltests, siehe ADR-24):**

- **Echte Sicherheitslücke gefunden und behoben:** `connectors/
  ir_rss.py` parste externe RSS-/Atom-Feeds über die Stdlib
  `xml.etree.ElementTree`, die laut Python-Dokumentation nicht gegen
  „Billion Laughs"-Entity-Expansion gehärtet ist (winzige Payload →
  mehrere GB Speicherverbrauch beim Parsen; die bestehende HTTP-
  Größenobergrenze schützt NICHT davor, da der Angriff erst beim
  Parsen entsteht). Behoben durch Wechsel auf `defusedxml`
  (neue Abhängigkeit in `pyproject.toml`). Test mit echter „Billion
  Laughs"-Payload beweist die Ablehnung.
- **Zwei Ausfalltests bestätigen bereits bestehende Mechanismen
  end-to-end statt nur auf Komponentenebene, kein Fund:**
  Prompt-Injection-Versuch in News-Titel/-Zusammenfassung durchläuft
  die komplette Ingestion-Pipeline unverändert als reine Nutzdaten
  (`tests/news/test_ingest.py`); absichtlich widersprüchliche/extreme
  Testdaten (Versechsfachung der verwässerten Aktienanzahl) lösen das
  bestehende Warnsignal-System sichtbar aus (`risk_deductions`,
  reduzierter `total_score`, `top_risks`) statt einer stillen
  Fehlkalkulation (`tests/scoring/test_score.py`).
- **Neuer Baustein — Restore-Prozess:** `db/backup.py`
  (`backup_database`/`restore_database`) für die lokale SQLite-
  Datenbankdatei (atomare, zeitgestempelte Dateikopie); end-to-end
  getestet: Sicherung → simulierter Datenverlust → Wiederherstellung →
  Daten vollständig wieder da (`tests/db/test_backup.py`, 7 neue
  Tests). Ergänzt den bereits bestehenden Alembic-Up-/Downgrade-Test
  (`tests/db/test_schema.py::test_alembic_migration_gegen_sqlite`).
- Rate-Limit-Überschreitung je Connector: bereits durch den
  bestehenden gemeinsamen Basis-Connector-Test abgedeckt (alle
  Connectoren teilen sich dieselbe `_request_with_retry`-
  Implementierung) — kein connectorspezifischer Sonderfall gefunden.
- **Offene, dokumentierte Lücke statt stillschweigend übergangen:**
  Auftrag §3 „bei Widerspruch beide Werte zeigen" (zwei unabhängige
  Quellen mit unterschiedlichem Wert für dieselbe Kennzahl) ist mit
  dem aktuellen Kostenlos-Quellen-Set strukturell nicht auftretbar (nur
  SEC EDGAR liefert Fundamentaldaten) und daher nicht implementiert —
  nachzuholen, sobald eine zweite Fundamentaldatenquelle angebunden wird.

**Tests:** 10 neue Tests (insgesamt 445, alle grün) — 1 für die
Billion-Laughs-Ablehnung, 1 für den Prompt-Injection-Ausfalltest, 1 für
den widersprüchliche-Daten-Ausfalltest, 7 für Backup/Restore. `ruff
check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** `connectors/ir_rss.py` (defusedxml),
`pyproject.toml` (neue Abhängigkeit `defusedxml`), neues Modul
`db/backup.py`, zugehörige Tests unter `tests/connectors/`,
`tests/news/`, `tests/scoring/`, neues `tests/db/test_backup.py`.

**Umgesetzt (Windows-Setup + Benutzerhandbuch):**

- `start.ps1` sichert die Datenbankdatei jetzt automatisch vor jeder
  Alembic-Migration (neuer `db/backup.py`-Baustein aus dem
  Ausfalltest-Schritt wird hier erstmals in den echten Nutzerablauf
  eingebunden, nicht nur in Tests) — best-effort: ein Fehlschlag (z. B.
  beim allerersten Start ohne bestehende Datenbank) bricht den
  Programmstart NICHT ab, sondern erscheint nur als Hinweis.
  Überspringbar mit `-NoBackup`.
- Neue Endnutzer-Skripte `scripts/backup-database.ps1`/
  `scripts/restore-database.ps1`, die auf ein neues CLI-Werkzeug
  `db/backup_cli.py` (`sichern`/`wiederherstellen`/`auflisten`)
  aufsetzen — bislang war Backup/Restore nur über die Python-API
  nutzbar (`tests/db/test_backup.py`), jetzt auch für Endnutzer ohne
  Python-Kenntnisse per Doppelklick-Skript.
- `BENUTZERHANDBUCH.md` neu geschrieben: Installation/erster Start,
  Speicherorte, Analyseprofil, Datenschutz/Sicherheit, Datensicherung,
  Fehlerbehebung, weiterführende Dokumente. Enthält einen bewusst
  ehrlichen Abschnitt „Was die Oberfläche heute zeigt — und was noch
  nicht": nur die Start-/Datenstatus-Seite existiert als Bildschirmseite,
  die übrigen neun Auftrag-§10-Seiten (Screener, Rangliste,
  Unternehmensdetail, Peer-Vergleich, DCF, Nachrichten, Portfolio,
  Backtest, Einstellungen) sind noch nicht gebaut — der komplette
  Analysemotor dahinter (Datenabruf, Kennzahlen, Bewertung, Scoring,
  Nachrichten, Portfolio, Backtesting, Exporte) ist implementiert und
  getestet, aber aktuell nur über die Python-API bzw. die Testsuite
  aufrufbar, nicht über einen Bedienknopf. Kein Doppelklick-Installer
  (.exe/.msi) — als bewusste Einschränkung dokumentiert (kein Zugriff
  auf Windows-Build-Werkzeuge in dieser Entwicklungsumgebung).
- `README.md` aktualisiert: Projektstand-Hinweis (Milestone 8 statt
  „Milestone 1"), Verweis auf `BENUTZERHANDBUCH.md`, neuer Abschnitt
  „Datensicherung", Hinweis auf den fehlenden nativen Installer,
  Projektstruktur-Baum ergänzt.

**Tests:** 5 neue Tests (insgesamt 450, alle grün) für
`db/backup_cli.py`. `ruff check .` und `mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** `start.ps1`, neue Skripte
`scripts/backup-database.ps1`/`scripts/restore-database.ps1`, neues
Modul `db/backup_cli.py`, neues `tests/db/test_backup_cli.py`, neues
`BENUTZERHANDBUCH.md`, `README.md`.

**Nächster Schritt:** Finale Abnahme-Checkliste gegen Auftrag §15 +
Milestone-8-/Projekt-Doku-Abschluss — siehe `NEXT_STEPS.md`.

## Milestone 8 — Abschluss: unabhängiger Review + Abnahme-Checkliste

**Status:** Milestone 8 abgeschlossen (2026-09-08), mit ehrlich
dokumentierten offenen Punkten (siehe `ABNAHME.md`).

**Unabhängiger Security-/Plausibilitätscheck (Auftrag §15 Kriterium
9):** Der eigene Review (ADR-23/24) ist gründlich, aber nicht
unabhängig — derselbe Akteur, der den Code baute, kann dieselben
blinden Flecken haben. Deshalb wurde ein separater Agentenlauf ohne
Kenntnis der vorherigen Implementierungsentscheidungen beauftragt,
denselben Codestand mit frischem Blick zu prüfen (Sicherheit + Code-
und Finanzmathematik-Plausibilität). Das war kein Alibi-Durchlauf:

- **Blockierender Fund, noch in dieser Runde behoben:**
  `risk/warning_signals.py::run_all_checks` nahm kein `as_of` entgegen
  — jeder Warnsignal-Check griff dadurch auf den AKTUELLEN Zeitpunkt
  statt den Analysestichtag zurück. Da Warnsignale direkt in
  `total_score` einfließen und `total_score` das Ranking-Kriterium von
  `backtesting/strategy.py::select_top_n` ist, konnte ein Backtest
  „per Februar" durch erst nach Februar bekannt gewordene Daten
  beeinflusst werden — ein struktureller Verstoß gegen Auftrag §9, den
  der bestehende Look-ahead-Test nicht abdeckte (er testet eine neue
  Entity, nicht eine später eintreffende Zeile für eine bereits
  bekannte Entity). Behoben: `as_of` wird jetzt durch jeden Warnsignal-
  Check gereicht; zwei neue Regressionstests beweisen exakt das
  gefundene Szenario.
- **Zwei weitere Härtungen, behoben:** Downloadgrößen-Prüfung puffert
  nicht mehr erst vollständig, bevor sie greift (jetzt `httpx`-
  Streaming mit Abbruch während des Downloads). HTML-Sanitizing-
  Fallback (`news/sanitize.py`) lässt im Ausnahmefall kein rohes
  Markup mehr durch (Regex-Tag-Entferner statt Rohtext-Rückfall).
- **Eine Restlücke, bewusst nicht behoben, ehrlich dokumentiert:**
  SSRF-Time-of-check-to-time-of-use — die DNS-Validierung und die
  tatsächliche Verbindung nutzen zwei getrennte DNS-Auflösungen; ein
  robuster Fix (IP-Pinning über einen eigenen Transport) hätte einen
  riskanten Umbau der HTTP-Transportschicht ohne ausreichende Testzeit
  bedeutet. Als tragbares Restrisiko für dieses lokale
  Ein-Nutzer-Werkzeug eingestuft, `SECURITY.md` entsprechend korrigiert
  (vorherige Formulierung stellte den Schutz als vollständiger dar, als
  er tatsächlich ist).
- **Finanzmathematik (DCF, Multiples, Fundamentalkennzahlen, Scoring)
  bestätigt:** stimmig mit `METHODOLOGY.md`, keine Fehlbezeichnungen
  oder Vorzeichenfehler gefunden.

Vollständig dokumentiert in `DECISIONS.md` ADR-25.

**Abnahme-Checkliste (`ABNAHME.md`):** ehrliche, kriterienweise
Bewertung aller neun Auftrag-§15-Kriterien. Ergebnis:
- **Vollständig erfüllt (6/9):** keine unbelegte Kennzahl (strukturell),
  Datenalter/Marktdatenverzögerung sichtbar, klarer Fehler bei
  Quellenausfall, ≥30 Tests (453 statt 30), Backtests ohne Look-ahead
  (nach Behebung des o. g. Fundes), unabhängiger Security-Check
  dokumentiert.
- **Teilweise erfüllt (1/9):** DCF/Kernkennzahlen nur an präzisen
  synthetischen Testfällen hand-verifiziert, nicht an echten,
  veröffentlichten Geschäftszahlen (Internetzugang in dieser Sandbox
  weiterhin blockiert, dieselbe Einschränkung seit Milestone 2).
- **Nicht erfüllt/nicht verifizierbar (2/9):** „kompletter Lauf
  reproduzierbar" — nur mit synthetischen Daten nachgewiesen, nie mit
  echten externen Quellen tatsächlich ausgeführt; „Exporte = UI-Werte"
  — strukturell abgesichert (ADR-21), aber es existiert noch keine
  UI-Seite, die Berichtswerte überhaupt anzeigt, also nichts zum
  Vergleichen.

**Tests:** 3 neue Tests (insgesamt 453, alle grün) — Look-ahead-
Regressionstest auf Warnsignal-Ebene, auf Score-Integrationsebene, und
HTML-Sanitizing-Fallback-Regressionstest. `ruff check .` und
`mypy src` beide fehlerfrei.

**Geänderte/neue Dateien:** `risk/warning_signals.py`,
`fundamentals/report.py`, `connectors/base.py`, `news/sanitize.py`,
`SECURITY.md`, `DECISIONS.md` (ADR-25), neues `ABNAHME.md`, zugehörige
Tests.

**Verbleibende offene Punkte** (ehrlich dokumentiert, nicht
blockierend für den Abschluss dieser Entwicklungssession):
Lockfile für Abhängigkeits-Pinning, SSRF-IP-Pinning, Live-Verifikation
mit echten Daten/API-Schlüsseln, Hand-Verifikation an realen
Unternehmenszahlen, restliche neun UI-Seiten aus Auftrag §10, Auftrag-
§3-Mehrquellen-Widerspruchsanzeige (strukturell mit dem aktuellen
Kostenlos-Quellen-Set nicht auftretbar). Alle in `TODO.md`/
`NEXT_STEPS.md`/`SECURITY.md` geführt.

**Nächster Schritt:** Keiner innerhalb des ursprünglichen
Milestone-0–8-Plans — alle acht Milestones sind implementiert,
getestet und ehrlich abgenommen. Siehe `NEXT_STEPS.md` für die
Prioritätenliste künftiger, nicht mehr durch den ursprünglichen
Auftragsplan vorgegebener Arbeit (Live-Datenverifikation, restliche
UI-Seiten, KI-Zusammenfassung).

## Nach Milestone 8 — Marktscreener (Auftrag §10, Seite 2)

**Status:** umgesetzt (2026-09-09), auf Nutzerwunsch als erste von neun
noch fehlenden Auftrag-§10-Oberflächenseiten (siehe ADR-26).

**Umgesetzt:**

- Neues Modul `ingestion/pipeline.py`: Ticker/CIK → Entity finden/
  anlegen (`entity_resolution/service.py::find_or_create_entity`) →
  alle im Kennzahlen-Vokabular bekannten XBRL-Kennzahlen abrufen und
  speichern (`normalization/ingest.py::ingest_sec_company_concept`).
  `TAG_CANDIDATES_BY_METRIC` probiert bei mehreren möglichen XBRL-Tags
  je Kennzahl (unterschiedliche Taxonomie-Versionen) jeden Kandidaten;
  ein HTTP 404 (Unternehmen meldet diesen Tag nicht) gilt als „nicht
  gemeldet", nicht als Fehlschlag der gesamten Ingestion. Nimmt bereits
  konstruierte Connector-Instanzen entgegen (Dependency Injection) —
  vollständig ohne echten Netzwerkzugriff testbar.
- Neues Profilfeld `NutzerProfil.sec_edgar_kontakt_email` (SEC-
  Pflichtangabe für den User-Agent) — bewusst ein eigenes, vom Nutzer
  ausdrücklich gesetztes Feld statt automatisch aus dem Anmeldekonto
  übernommen (Auftrag §12).
- `AppContext.secret_store` (nur OS-Keyring, kein Master-Passwort-
  Dialog — der ist Aufgabe der noch fehlenden Einstellungen-Seite).
  Neuer `AppSettings.cache_dir` für `connectors.cache.FileCache` —
  erste produktive `FileCache`-Nutzung (bislang nur in Tests).
- Neue UI-Seite `ui/screener.py`: Formular zum Hinzufügen per CIK/
  Ticker, klare Fehlermeldungen bei fehlender Kontakt-E-Mail oder
  Connector-Fehlern (kein stiller Fehlschlag), optionaler Alpha-
  Vantage-Kursabruf (nur falls Schlüssel hinterlegt), Liste bereits
  erfasster Unternehmen mit Namenssuche. Jede Ingestion-Aktion landet
  im Audit-Log (`log_data_fetch`/`log_data_fetch_error`/
  `log_secret_accessed`).
- `app.py`: einfache Sidebar-Navigation (`st.sidebar.radio`) zwischen
  „Start/Datenstatus" und „Marktscreener"; gemeinsamer Hinweis-Baustein
  nach `ui/components.py` ausgelagert (vermeidet Zirkelimport).

**Tests:** 20 neue Tests (insgesamt 471, alle grün) — 8 für
`ingestion/pipeline.py` (inkl. Idempotenz, 404-Behandlung, echter
Serverfehler wird nicht verschluckt), 4 für `list_entities`, 4 für das
neue Profilfeld/`cache_dir`, 2 neue `AppTest`-Smoke-Tests für die
Marktscreener-Seite (inkl. Sidebar-Navigation), 2 für `secret_store` in
`AppContext`. `ruff check .` und `mypy src` beide fehlerfrei.

**Manuell mit echtem Browser verifiziert** (Playwright gegen einen
laufenden Streamlit-Prozess, nicht nur `AppTest`): Ersteinrichtung mit
Kontakt-E-Mail, Wechsel zur Marktscreener-Seite, Formular korrekt
gerendert, leeres Formular zeigt die erwartete Fehlermeldung ohne
Absturz. Ein echter SEC-EDGAR-Live-Abruf konnte mangels Internetzugang
in dieser Sandbox nicht getestet werden — dieselbe, seit Milestone 2
durchgängig dokumentierte Einschränkung; der Nutzer muss dies auf dem
eigenen Rechner (`start.bat`) selbst prüfen.

**Geänderte/neue Dateien:** neues Modul `ingestion/` (`__init__.py`,
`pipeline.py`), neue `ui/screener.py`, neue `ui/components.py`,
`ui/app.py`, `ui/bootstrap.py`, `config/models.py`, `config/settings.py`,
`config/secrets.py` (keine funktionale Änderung, nur Re-Export-Kontext),
`ui/profile_form.py`, `connectors/alpha_vantage.py`
(`API_KEY_SECRET_NAME`), zugehörige Tests.

**Offene Punkte** (siehe `TODO.md`): acht weitere Auftrag-§10-Seiten,
Einstellungen-Seite für die Alpha-Vantage-Schlüsselverwaltung (aktuell
nur nutzbar, wenn der Schlüssel bereits anderweitig im OS-Keyring
liegt), Umstieg auf `st.navigation()` sobald mehr Seiten existieren.

**Nächster Schritt:** Kandidaten-Rangliste oder Unternehmensdetail
(nächste sinnvolle Seite, da beide bereits fertige Backend-Bausteine
haben) — siehe `NEXT_STEPS.md`.

## Nach Milestone 8 — Unternehmensdetail mit Quellenleiste (Auftrag §10, Seite 4)

**Status:** umgesetzt (2026-09-09), zweite von neun noch fehlenden
Auftrag-§10-Oberflächenseiten (siehe ADR-27), auf Nutzerwunsch ohne
Zwischenrückfrage direkt im Anschluss an den Marktscreener gebaut.

**Umgesetzt:**

- Neue UI-Seite `ui/detail.py`: rendert ausschließlich aus
  `reports/bundle.py::build_report_bundle` →
  `report_bundle_to_dict()` — demselben Dict, das auch die Excel-/
  PDF-/JSON-Exporte verwenden (ADR-21). Kopfzeile mit den laut
  Auftrag §10 vorgeschriebenen Pflichtangaben (Datenstand,
  Analysezeit, Marktdatenverzögerung, Datenabdeckung, Konfidenz),
  Kennzahlen (Wachstum über vier Horizonte, Margen, Renditen,
  Verschuldung, fehlende Kennzahlen explizit ausgewiesen), Bewertung
  (Multiples, Fair-Value-Band, DCF-Szenarien, Peer-Vergleich),
  Score (Gesamtscore, Klassifikation, positive Faktoren, Risiken,
  Gegenargumente, Ungültigkeitsbedingungen, Risikoabzüge), Nachrichten
  (Ereignis-Cluster), Quellenleiste mit Lizenzhinweis je Quelle
  (Auftrag-§10-Titel „... MIT Quellenleiste"), Annahmen, sowie JSON-/
  Excel-/PDF-Download-Buttons aus demselben bereits berechneten
  `ReportBundle`.
- Private Hilfsfunktion `_kennzahl()`: formatiert Werte für die
  Anzeige, `None` immer als „—" (nie als 0 oder geratene Zahl,
  Auftrag §11), `bool` vor dem allgemeinen Zahlenzweig behandelt (ist
  in Python eine `int`-Unterklasse).
- `app.py`: Sidebar-Navigation um „Unternehmensdetail" als dritte
  Option erweitert.
- Unternehmensauswahl nutzt dieselbe `ui/screener.py::list_entities`
  wie der Marktscreener; der vollständige Bericht lädt die Entity
  anschließend per `session.get(Entity, entity_id)` in einer neuen
  Session (nicht `session.add()` auf der bereits detached-geladenen
  Instanz — dieser Fehler wurde beim ersten Entwurf selbst gefunden
  und vor jedem Testlauf korrigiert).

**Tests:** 7 neue Tests (insgesamt 478, alle grün) — 5 reine
Formatierungstests für `_kennzahl()` (`tests/ui/test_detail.py`), 2
neue `AppTest`-Smoke-Tests (`tests/ui/test_app_smoke.py`): leerer
Zustand ohne erfasste Unternehmen sowie voller Bericht mit
synthetisch befüllter Testdatenbank (gleiches Muster wie
`tests/reports/test_bundle.py`, Firma G). `ruff check .` und
`mypy src` beide fehlerfrei.

**Manuell mit echtem Browser verifiziert** (Playwright gegen einen
laufenden Streamlit-Prozess mit synthetisch befüllter Testdatenbank,
nicht nur `AppTest`): alle Seitenabschnitte rendern korrekt inkl.
DCF-Szenarien-Tabelle, Score-Risikoabzüge, Quellenleiste mit
Lizenzhinweisen und den drei funktionierenden Download-Buttons; keine
unerwarteten Konsolenfehler (nur harmlose Streamlit-Telemetrie-
Fehlschläge mangels Internetzugang in dieser Sandbox).

**Geänderte/neue Dateien:** neue `ui/detail.py`, `ui/app.py`
(Navigation, Docstring), zugehörige Tests
(`tests/ui/test_detail.py`, `tests/ui/test_app_smoke.py`).

**Auswirkung auf Abnahme:** Auftrag-§15-Kriterium 8 („Exporte =
Oberflächenwerte") gilt jetzt als strukturell UND durch eine echte
UI-Seite erfüllt — siehe aktualisierte Bewertung in `ABNAHME.md`.

**Offene Punkte** (siehe `TODO.md`): sieben weitere Auftrag-§10-Seiten,
Einstellungen-Seite für die Alpha-Vantage-Schlüsselverwaltung, Umstieg
auf `st.navigation()` sobald mehr Seiten existieren.

**Nächster Schritt:** Kandidaten-Rangliste (Auftrag §10, Seite 3) —
siehe `NEXT_STEPS.md`.

## Nach Milestone 8 — Kandidaten-Rangliste (Auftrag §10, Seite 3)

**Status:** umgesetzt (2026-09-09), dritte von neun noch fehlenden
Auftrag-§10-Oberflächenseiten (siehe ADR-28).

**Umgesetzt:**

- Neue UI-Seite `ui/ranking.py`: sortierbare Tabelle aller bereits
  über den Marktscreener erfassten Unternehmen, gerankt nach
  Gesamtscore (absteigend als Vorsortierung, per Klick auf eine
  Spaltenkopfzeile durch Streamlits eingebautes `st.dataframe`
  zusätzlich frei sortierbar). Baut je Zeile den vollständigen
  `ReportBundle` (wie `ui/detail.py`, ADR-27) statt nur
  `score_entity()` direkt aufzurufen — garantiert dadurch dieselbe
  strukturelle Konsistenz wie zwischen Detailseite und Exporten: Score,
  Datenabdeckung und Klassifikation können zwischen Rangliste und
  Detailseite für dasselbe Unternehmen nicht auseinanderlaufen.
- Rankt bewusst NUR bereits erfasste Unternehmen, keine automatische
  Breitensuche über ein größeres Aktienuniversum — diese Fähigkeit
  existiert im Programm noch nicht (dokumentierte Lücke, siehe
  ADR-28/`NEXT_STEPS.md`).
- Warnung, wenn Unternehmen mit Klassifikation „Datenlage
  unzureichend" in der Liste stehen — entdeckt beim Testen: ein
  Unternehmen ganz ohne Rohdaten erhält `total_score=0.0` (kein
  fehlender Wert, sondern das korrekte Ergebnis der bestehenden
  Score-Formel aus Milestone 4, da die Komponente „Datenqualität/
  Aktualität" immer numerisch bewertet).
- `app.py`: Sidebar-Navigation um „Kandidaten-Rangliste" als dritte
  Option erweitert (zwischen Marktscreener und Unternehmensdetail).

**Tests:** 4 neue Tests (insgesamt 482, alle grün) — 2 reine Tests für
`_rangliste_dataframe()` (`tests/ui/test_ranking.py`: Sortierung,
Score 0.0 statt fehlendem Wert bei leeren Daten), 2 neue
`AppTest`-Smoke-Tests (`tests/ui/test_app_smoke.py`): leerer Zustand
sowie eine Zeile mit synthetisch befüllter Testdatenbank. `ruff check .`
und `mypy src` beide fehlerfrei.

**Manuell mit echtem Browser verifiziert** (Playwright gegen einen
laufenden Streamlit-Prozess mit drei synthetisch befüllten
Unternehmen — zwei mit unterschiedlich skalierten Finanzdaten, eines
ganz ohne Daten): Rangfolge korrekt (höherer Score zuerst), Score-,
Datenabdeckungs- und Konfidenzwerte korrekt, Warnung bei
unzureichender Datenlage erscheint korrekt für das datenlose
Unternehmen, keine unerwarteten Konsolenfehler. Ein Klick-Sortiertest
auf die Spaltenkopfzeile selbst war über Playwright nicht möglich, da
`st.dataframe` auf `<canvas>` statt echtem DOM rendert (siehe ADR-28)
— das Sortierverhalten selbst ist eine von Streamlit getestete
Plattform-Eigenschaft.

**Geänderte/neue Dateien:** neue `ui/ranking.py`, `ui/app.py`
(Navigation, Docstring), zugehörige Tests (`tests/ui/test_ranking.py`,
`tests/ui/test_app_smoke.py`).

**Offene Punkte** (siehe `TODO.md`): sechs weitere Auftrag-§10-Seiten,
Einstellungen-Seite für die Alpha-Vantage-Schlüsselverwaltung, Umstieg
auf `st.navigation()` sobald mehr Seiten existieren, künftig ggf. eine
echte Breitensuche über ein größeres Aktienuniversum für den
Marktscreener (würde auch die Kandidaten-Rangliste aussagekräftiger
machen).

**Nächster Schritt:** Peer-Vergleich oder DCF-/Szenarioanalyse (Auftrag
§10, Seiten 5/6 — nutzen dieselben Daten wie die Detailseite) — siehe
`NEXT_STEPS.md`.

## Nach Milestone 8 — Peer-Vergleich (Auftrag §10, Seite 5)

**Status:** umgesetzt (2026-09-09), vierte von neun noch fehlenden
Auftrag-§10-Oberflächenseiten (siehe ADR-29).

**Umgesetzt:**

- Neue UI-Seite `ui/peers.py`: Unternehmen auswählen, dann
  Vergleichstabelle mit allen über `fundamentals/peers.py::find_peers`
  (identischer SIC-Code, Milestone 3) gefundenen Peers. Baut je Zeile
  den vollständigen `ReportBundle` (wie `ui/ranking.py`, ADR-28) und
  zeigt Score, Klassifikation, Umsatzwachstum, Nettomarge, ROE,
  Verschuldung, KGV und EV/EBITDA nebeneinander.
- Zwei unterschiedliche, ehrlich getrennte Meldungen statt einer
  generischen „keine Ergebnisse": (a) ausgewähltes Unternehmen hat noch
  keinen SIC-Code (wird erst beim SEC-EDGAR-Abruf über den
  Marktscreener automatisch gesetzt), (b) SIC-Code vorhanden, aber
  keine anderen erfassten Unternehmen mit demselben Code.
- Fügt bewusst KEINEN eigenen Größenfilter für Peers hinzu — die
  bereits dokumentierte Lücke „Peer-Gruppen-Zuordnung ohne
  Größenähnlichkeit" (`fundamentals/peers.py`-Docstring) bleibt
  unverändert an ihrem angestammten Ort in `TODO.md`/`DECISIONS.md`
  geführt.
- `app.py`: Sidebar-Navigation um „Peer-Vergleich" als fünfte Option
  erweitert.

**Tests:** 5 neue Tests (insgesamt 487, alle grün) — 2 reine Tests
(`tests/ui/test_peers.py`: `find_peers`-Filterung, Inhalt der
Vergleichstabelle), 3 neue `AppTest`-Smoke-Tests
(`tests/ui/test_app_smoke.py`): kein Unternehmen erfasst, Unternehmen
ohne SIC-Code, zwei Unternehmen mit identischem SIC-Code inkl.
Vergleichstabelle. `ruff check .` und `mypy src` beide fehlerfrei.

**Manuell mit echtem Browser verifiziert** (Playwright gegen einen
laufenden Streamlit-Prozess mit drei synthetisch befüllten
Unternehmen — zwei mit identischem SIC-Code, eines mit abweichendem):
Peer korrekt gefunden und in der Tabelle angezeigt, das Unternehmen
mit abweichendem SIC-Code korrekt NICHT in der Vergleichstabelle,
Score-/Kennzahlenwerte plausibel unterschiedlich, keine unerwarteten
Konsolenfehler.

**Geänderte/neue Dateien:** neue `ui/peers.py`, `ui/app.py`
(Navigation, Docstring), zugehörige Tests (`tests/ui/test_peers.py`,
`tests/ui/test_app_smoke.py`).

**Offene Punkte** (siehe `TODO.md`): fünf weitere Auftrag-§10-Seiten,
Einstellungen-Seite für die Alpha-Vantage-Schlüsselverwaltung, Umstieg
auf `st.navigation()` sobald mehr Seiten existieren, Größenfilter für
Peer-Gruppen (bereits vor dieser Seite als Lücke dokumentiert,
weiterhin offen).

**Nächster Schritt:** DCF-/Szenarioanalyse (Auftrag §10, Seite 6 —
nutzt dieselben Daten wie die Detailseite, `valuation/dcf.py` inkl.
Sensitivitätsmatrix bereits vorhanden) — siehe `NEXT_STEPS.md`.
