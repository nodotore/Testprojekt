# Entscheidungen (Architecture Decision Records)

Format je Eintrag: Kontext → Entscheidung → Begründung → Konsequenzen.
Neue Entscheidungen werden angehängt, bestehende nicht rückwirkend
verändert (bei Revision: neuer Eintrag „ADR-N ersetzt ADR-M").

## ADR-1: Eigenes Unterverzeichnis statt Repo-Root

**Kontext:** Das Repo `nodotore/Testprojekt` enthält bereits ein
unabhängiges Projekt (statische Website „Nordlicht Studio" +
CD-Musikfinder-PWA) mit eigenen Root-Dokumenten (`PLAN.md`,
`PROGRESS.md`, `DECISIONS.md`, `TODO.md`, `CHANGELOG.md`,
`NEXT_STEPS.md`), die für Use Case UC-001 aktiv genutzt werden. Der
Investment-Analysator ist ein komplett anderer, technisch unabhängiger
Stack (Python statt statisches HTML/JS).

**Entscheidung:** Der Investment-Analysator wird in einem eigenen
Unterverzeichnis `investment-analyzer/` entwickelt, das als eigener
„Projektstamm" im Sinne von Auftrag §13 behandelt wird — mit eigenem
`CLAUDE.md`, `PLAN.md`, `PROGRESS.md`, `TODO.md`, `DECISIONS.md`,
`CHANGELOG.md`, `NEXT_STEPS.md`, `DATA_SOURCES.md`, `METHODOLOGY.md`,
`SECURITY.md`.

**Begründung:** Vermeidet, die bestehende, in Arbeit befindliche
CD-Musikfinder-Dokumentation zu überschreiben oder zu vermischen.
Entspricht sinngemäß Auftrag §4 („im gewählten Projektordner planen").
Der Nutzer kann diese Entscheidung im Rahmen der Milestone-0-Fragen
noch korrigieren (z. B. eigenes, separates Repository stattdessen).

**Konsequenzen:** Alle künftigen Pfadangaben in diesem Projekt sind
relativ zu `investment-analyzer/`. Python-Tooling (venv, `pyproject.toml`
etc.) wird ebenfalls in diesem Unterverzeichnis verankert, nicht im
Repo-Root.

## ADR-2: Technologie-Stack

**Entscheidung:** Der im Auftrag §4 vorgeschlagene Stack wird
unverändert übernommen:

- Python 3.12+
- FastAPI (Backend/API)
- Streamlit (deutschsprachige UI, Version 1)
- SQLite (lokale Entwicklung) / PostgreSQL (Produktion)
- SQLAlchemy 2.x + Alembic (Migrationen)
- httpx (async HTTP), pandas + numpy (Datenverarbeitung), pydantic
  (Validierung/Settings)
- Plotly (Charts)
- Playwright — ausschließlich für rechtlich erlaubte Webseiten ohne
  geeignete API, nicht als Standardweg
- APScheduler zum Start (Celery/Redis erst bei nachgewiesenem Bedarf an
  verteilter Job-Ausführung — YAGNI, vermeidet unnötige Infrastruktur)
- pytest, ruff, mypy, Playwright für Tests
- Docker Compose optional; Windows-Startskripte (`.bat`/PowerShell)
  verbindlich

**Begründung:** Auftraggeber-Vorgabe; alle Komponenten sind etabliert,
gut dokumentiert, lizenzunkritisch (Open Source) und passen zu den
Anforderungen (async I/O für viele Connectoren, typsichere Modelle,
austauschbare DB für Dev/Prod).

**Konsequenzen:** SQLite-Dev-Modus muss dieselben Constraints wie
PostgreSQL abbilden können (keine SQLite-spezifischen Sonderfälle im
Domainmodell); Alembic-Migrationen müssen gegen beide Dialekte getestet
werden, bevor Milestone 1 als abgeschlossen gilt.

## ADR-3: Modulgrenzen und Paketstruktur

**Entscheidung:** Ab Milestone 1 folgende Package-Struktur unter
`investment-analyzer/src/investment_analyzer/`:

```
connectors/         # ein Unterpaket je externer Quelle, gemeinsame Basisklasse
normalization/       # Einheiten, Währungen, Geschäftsjahre, Splits/Dividenden
entity_resolution/   # Ticker/ISIN/LEI → stabile interne Entity-ID
fundamentals/        # Kennzahlenberechnung aus normalisierten Rohdaten
valuation/           # Multiples, DCF, Sensitivitäten
news/                # Abruf, Dedup, Clustering, Klassifikation
risk/                # Warnsignale, Konzentrationsrisiken
scoring/             # deterministisches Scoring, Konfidenz, Gegenargumente
backtesting/         # Point-in-time-Backtests
reports/              # PDF/Excel/JSON-Export
ui/                    # Streamlit-Seiten
audit/                # Audit-Log, Belegprüfung, Herkunftsnachweis
```

Jedes Modul besitzt eigene Tests unter `tests/<modulname>/` und darf nur
über definierte Schnittstellen (Pydantic-Modelle/Funktionssignaturen) mit
anderen Modulen kommunizieren — kein direkter Zugriff auf interne
Implementierungsdetails eines fremden Moduls.

**Begründung:** Direkte Umsetzung von Auftrag §4 („Module strikt
trennen"); ermöglicht parallele Agentenarbeit ohne Dateikonflikte (ein
Agent = ein oder mehrere klar abgegrenzte Module).

**Konsequenzen:** Bei Parallelisierung wird jedem Agenten vor Arbeitsbeginn
genau die Modulliste zugewiesen, an der er arbeiten darf (siehe
`PLAN.md`). Cross-Modul-Änderungen (z. B. gemeinsames Datenmodell in
`connectors`/`normalization`) übernimmt ausschließlich der Hauptagent.

## ADR-4: Agentenkoordination und Dateibesitz

**Entscheidung:** Pro Arbeitsrunde erstellt der Hauptagent (Orchestrator)
vor jeder Parallelisierung eine explizite Zuordnung „Agent → Module/
Dateien → Abnahmekriterien" in `PLAN.md`. Zwei Agenten erhalten nie
Schreibrechte auf dieselbe Datei in derselben Runde. Jeder Agent liefert
einen strukturierten Ergebnisbericht (Auftrag, Ergebnis, geänderte
Dateien, Tests, offene Risiken, nächster Schritt), der vom Hauptagenten
geprüft wird, bevor ein Merge in den Hauptstand erfolgt.

**Begründung:** Direkte Umsetzung Auftrag §4.

**Konsequenzen:** Erhöhter Koordinationsaufwand, aber verhindert
Race-Conditions/Merge-Konflikte und stellt sicher, dass ein
verantwortlicher Hauptagent jederzeit den Gesamtstand kennt.

## ADR-5: Secret-Management

**Entscheidung:** API-Schlüssel werden ausschließlich über das
Betriebssystem-Keyring (`keyring`-Paket, unter Windows: Windows
Credential Manager) gespeichert. Ist kein Keyring verfügbar, Fallback auf
lokal verschlüsselte Datei (Fernet/AES, Schlüssel abgeleitet aus einem
vom Nutzer gesetzten Master-Passwort, nie im Klartext auf Platte).
Niemals Secrets in Code, Logs, Git-Historie oder Exportdateien (Auftrag
§2, §12).

**Begründung:** Direkte Auftragsvorgabe; Windows-Keyring ist der
robusteste Standardweg auf der Zielplattform.

**Konsequenzen:** `backend-agent` implementiert ein `SecretStore`-
Interface mit zwei Implementierungen (Keyring, verschlüsselte Datei);
alle Connectoren beziehen Schlüssel ausschließlich über dieses
Interface, nie über Umgebungsvariablen im Klartext-Logging-Pfad.

## ADR-6: Datenmodell-Grundprinzip — Provenienz-first

**Entscheidung:** Jeder gespeicherte Datenpunkt ist ein eigenständiges,
unveränderliches (append-only) Objekt mit allen in Auftrag §5 genannten
Feldern (Quelle, URL, Abrufzeitpunkt UTC, roh/normalisiert, geschätzt/
gemeldet/berechnet, Qualität/Konfidenz, Hash/Dokument-ID). Abgeleitete
Kennzahlen referenzieren ihre Eingabedatenpunkte per Fremdschlüssel,
nie per Kopie ohne Referenz. Entity-Auflösung (Ticker/ISIN/LEI →
stabile interne ID) ist ein eigener Schritt vor jeder Aggregation.

**Begründung:** Ermöglicht Nachvollziehbarkeit, Point-in-time-Queries für
Backtests (Auftrag §5, §9) und die Belegprüfung vor jeder Ausgabe
(Auftrag §11).

**Konsequenzen:** Höherer Speicher-/Modellierungsaufwand als ein
einfaches „letzter Wert gewinnt"-Schema, aber notwendige Voraussetzung
für alle nachgelagerten Anforderungen (Backtesting ohne Look-ahead,
Widerspruchsanzeige, Audit-Log).

## ADR-7: Projektstruktur bestätigt

**Entscheidung:** Nutzer hat ADR-1 (Unterverzeichnis `investment-analyzer/`
in `nodotore/Testprojekt`, statt separatem Repository) am 2026-09-07
bestätigt. Keine Änderung nötig.

## ADR-8: Start-Kostenvariante = Kostenlos

**Entscheidung:** Der Investment-Analysator startet mit der
Kostenlos-Datenquellen-Variante aus `DATA_SOURCES.md` (SEC EDGAR, EZB
SDW, Weltbank, GDELT, Alpha Vantage Free, Unternehmens-IR-Seiten/RSS).
Vom Nutzer am 2026-09-07 bestätigt.

**Konsequenzen:** Engere Rate Limits (insb. Alpha Vantage 5 req/min)
müssen im Connector-Caching/Scheduling (Milestone 2) explizit
berücksichtigt werden. EU/DE-Meldungsabdeckung ist strukturell
schwächer als US-Abdeckung (siehe ADR-9); dies wird im UI als
Datenabdeckungs-/Konfidenzhinweis sichtbar gemacht, nicht verschwiegen.
Ein späteres Upgrade auf die „günstig"-Variante bleibt möglich und wird
bei Bedarf als neuer ADR dokumentiert.

## ADR-9: Marktauswahl breit, ohne initiale Einschränkung

**Entscheidung:** Der Nutzer wünscht keine Vorfestlegung auf einzelne
Märkte — USA, Deutschland, übriges Europa und weitere/globale Märkte
sollen grundsätzlich unterstützt werden (bestätigt 2026-09-07). Die
konkrete Filterung erfolgt weiterhin je nach Auftrag §2 individuell über
das Nutzerprofil im Ersteinrichtungsdialog.

**Konsequenzen für Milestone 2:** Da pro Auftrag §14 zunächst nur zwei
Connectoren gebaut werden (eine Primärquelle Meldungen + eine
Marktdatenquelle), wird mit der in der Kostenlos-Variante am breitesten
tragfähigen Kombination begonnen: SEC EDGAR (Meldungen, zunächst nur
USA) + Alpha Vantage Free (Marktdaten, technisch auch nicht-US-Ticker,
aber mit engen Limits). Die Lücke bei EU/DE-Meldungsquellen ist bekannt
und wird in `DATA_SOURCES.md`/`MILESTONE_0.md` offen dokumentiert statt
stillschweigend übergangen.

## ADR-10: Deployment-Ziel Version 1 = lokal, Windows + SQLite

**Entscheidung:** Version 1 läuft rein lokal unter Windows mit SQLite,
ohne Docker-Voraussetzung (bestätigt 2026-09-07). Dies bekräftigt die in
ADR-2 bereits vorgesehene Dev-Konfiguration; PostgreSQL/Docker Compose
bleiben als optionaler, späterer Produktionspfad im Code vorbereitet
(SQLAlchemy-Dialektunabhängigkeit, siehe ADR-2), werden aber für V1
nicht zwingend benötigt und nicht in den Windows-Startskripten
vorausgesetzt.

## Noch zu treffende Entscheidungen

Keine blockierenden Entscheidungen mehr offen für den Start von
Milestone 1. Verbleibende Detailfragen aus `MILESTONE_0.md` Abschnitt B
(z. B. konkrete Zahlenwerte für Mindestmarktkapitalisierung) werden als
konfigurierbare Standardwerte in Milestone 1 vorgeschlagen und im
Ersteinrichtungsdialog vom Nutzer bestätigt/angepasst (Auftrag §2).
