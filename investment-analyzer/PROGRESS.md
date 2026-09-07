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
