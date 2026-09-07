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
