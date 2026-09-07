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

## Milestone 2 — Datenbeschaffung

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

## Milestone 3 — Fundamentalanalyse

Normalisierung, Kennzahlen (Auftrag §6 „Fundamentaldaten"), Zeitreihen
(1/3/5/10 Jahre), Peer-Gruppen-Zuordnung, Warnsignale (Auftrag §6
„Risiken und Warnsignale", Teilmenge ohne News-Abhängigkeit).
Abnahme: manuell nachgerechnete Testfälle (mind. 3 reale Unternehmen,
Handrechnung vs. Code) stimmen überein (financial-analysis-agent +
test-agent).

## Milestone 4 — Bewertung und Score

Multiples, DCF mit drei Szenarien + Sensitivitätsmatrix (Auftrag §6
„Bewertung"), erklärbares Scoring mit Startgewichtung aus Auftrag §7,
Konfidenzlogik (fehlende Daten → Konfidenzabschlag statt Nullwertung),
Gegenargumente/Ausgabeklassen. Abnahme: DCF-Handrechnung stimmt;
Scoring-Gewichte konfigurierbar und nachvollziehbar geloggt
(financial-analysis-agent + test-agent).

## Milestone 5 — Nachrichtenanalyse

Abruf (GDELT + IR-RSS gemäß `DATA_SOURCES.md`), Deduplizierung,
Sprach-/Ereigniserkennung, Clustering, Quellenqualitätsklassifikation
(Unternehmensmeldung/unabhängiger Bericht/Kommentar), KI-Zusammenfassung
mit Quellenverweis. Abnahme: Duplikaterkennung nachweislich funktionsfähig
an realem Testset; kein KI-Text ohne Quellenverweis (data-source-agent +
news-Modul, security-reviewer prüft Prompt-Injection-Behandlung).

## Milestone 6 — Portfolio und Exporte

Watchlist/Portfolio-Import (manuell + CSV), Konzentrationsanalysen,
Korrelation/Drawdown, Positionsgrößen-Bandbreiten, Excel/PDF/JSON-Export
mit allen in Auftrag §10 geforderten Tabellenblättern. Abnahme: Export
enthält exakt dieselben Werte wie die UI-Ansicht (automatisierter
Abgleich) (frontend-agent + backend-agent + test-agent).

## Milestone 7 — Backtesting

Point-in-time-Universum, Bias-Vermeidung (Look-ahead/Survivorship/
Selection), Kosten/Spreads/Dividenden/Währungen, Train/Validierung/
Out-of-Sample-Trennung, Kennzahlen (CAGR, Vola, Sharpe/Sortino, MaxDD,
Turnover) gegen Indexvergleich. Abnahme: dokumentierter Nachweis „kein
Look-ahead" durch gezielten Test (Kandidat, der erst nach Stichtag
bekannt wurde, darf Ergebnis vor Stichtag nicht beeinflussen)
(backtest-agent + test-agent).

## Milestone 8 — Sicherheit und Abnahme

Security-Review (Secrets, Webinhalte/Prompt-Injection, SSRF,
Abhängigkeits-Scan), Ausfalltests (manipulierte Webseiten, falsche
Daten, Rate-Limit-Überschreitung, Restore-Prozess), Windows-Installer,
Benutzerhandbuch. Abnahme: alle Kriterien aus Auftrag §15 erfüllt,
unabhängiger Security-/Plausibilitätscheck dokumentiert
(security-reviewer + test-agent + project-orchestrator).

## Agenteneinsatz pro Milestone

Ab Milestone 1 wird vor jeder Parallelisierung eine konkrete
Agent-zu-Modul-Zuordnung in diesem Dokument (Abschnitt der jeweiligen
Milestone-Runde) ergänzt — siehe ADR-4. Diese Kopfzeile hier nennt nur
die typischerweise führende Rolle je Milestone; die tatsächliche
Aufteilung einzelner Teilaufgaben folgt erst bei Arbeitsbeginn der
jeweiligen Milestone.
