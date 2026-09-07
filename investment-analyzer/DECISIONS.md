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

## ADR-11: Zwei zusätzliche Infrastruktur-Pakete (`config`, `db`)

**Kontext:** Auftrag §4 nennt eine feste Liste von Domänenmodulen
(`connectors, normalization, entity_resolution, fundamentals, valuation,
news, risk, scoring, backtesting, reports, ui, audit`). Für das
Grundgerüst (Milestone 1) werden aber Querschnittsbelange benötigt, die
zu keinem dieser Domänenmodule gehören: Nutzerprofil-/App-Einstellungen
inkl. Secret-Store, sowie die SQLAlchemy-`Base`-Klasse und Engine-/
Session-Hilfsfunktionen.

**Entscheidung:** Zwei zusätzliche Pakete `config/` (Nutzerprofil,
App-Einstellungen, Secret-Store) und `db/` (SQLAlchemy-Grundgerüst:
`Base`, Engine-/Session-Factory, dialektunabhängige Typ-Hilfen) werden
ergänzt. Die eigentlichen Provenienz-Domänenmodelle bleiben bei den in
ADR-3 zugewiesenen Modulen: `Entity`/`EntityIdentifier` in
`entity_resolution/models.py`, `Source` in `connectors/models.py`,
`DataPoint` in `normalization/models.py`, `AuditLogEntry` in
`audit/models.py` — `db/__init__.py` importiert diese nur zentral, damit
Alembic-Autogenerate und `create_all_tables()` (Test-/Dev-Bootstrap) alle
Tabellen kennen.

**Konsequenzen:** Die Modulliste aus ADR-3 bleibt fachlich unverändert;
`config`/`db` sind reine Infrastruktur ohne eigene Fachlogik. Künftige
Agenten, die an einem Domänenmodul arbeiten, finden dessen ORM-Modelle
weiterhin im jeweils zuständigen Paket, nicht in `db/`.

## ADR-12: UI-Logik von Streamlit-Rendering getrennt

**Entscheidung:** Die Streamlit-Seite (`ui/app.py`) enthält nur
Rendering-Code. Testbare Logik liegt in separaten, Streamlit-freien
Modulen: `ui/bootstrap.py` (Anwendungskontext: Engine, Sessions,
Logging, Audit-Logger, Profilspeicher; prüft per `check_database_ready`,
ob Alembic-Migrationen bereits gelaufen sind, statt selbst Tabellen
anzulegen), `ui/status.py` (wahrheitsgemäßer Datenstatus aus der DB,
niemals Platzhalterzahlen) und `ui/profile_form.py` (Formular-Rohdaten →
validiertes `NutzerProfil`).

**Begründung:** Ermöglicht normale `pytest`-Unit-Tests für die Logik
sowie zusätzlich End-to-End-Smoke-Tests der eigentlichen Seite über
`streamlit.testing.v1.AppTest` (siehe `tests/ui/test_app_smoke.py`),
ohne einen Browser zu benötigen. Ein echter `streamlit run`-Start wurde
zusätzlich manuell verifiziert (HTTP 200, siehe `PROGRESS.md`).

**Konsequenz für „Fail loud, nicht silent" (CLAUDE.md):** `app.py` legt
beim Start NIE selbst Datenbanktabellen an (`create_all`) — das würde
den Alembic-Versionsstand umgehen und stille Schema-Abweichungen
zwischen Entwicklungs- und Produktivumgebung ermöglichen. Fehlt die
Migration, zeigt die Oberfläche einen expliziten Fehler mit Anweisung,
`start.ps1`/`start.bat` (führt `alembic upgrade head` aus) zu verwenden.

## ADR-13: Trennung von `params` und `secret_params` im Connector-Grundgerüst

**Kontext:** Alpha Vantage (und potenziell weitere kostenpflichtige
Quellen) übergibt den API-Schlüssel als Query-Parameter
(`?apikey=...`). Auftrag §12 verlangt, dass Zugangsdaten niemals in
Logs, Exportdateien oder — implizit — in dauerhaft gespeicherten
Provenienz-Feldern (`DataPoint.document_url`) landen.

**Entscheidung:** `Connector.get_json()` unterscheidet zwischen
`params` (fließt in die tatsächliche Anfrage UND in die zurückgegebene/
gespeicherte `FetchResult.url`) und `secret_params` (fließt NUR in die
tatsächliche HTTP-Anfrage; taucht nie in `FetchResult.url`, im
Cache-Klartext oder in Logs auf). Der Cache-Schlüssel wird zwar aus
beidem gebildet, aber nur als SHA-256-Hash — nicht umkehrbar, kein
Klartext-Leck.

**Begründung:** Ohne diese Trennung würde `AlphaVantageQuote.source_url`
(und darüber `DataPoint.document_url`) den API-Schlüssel enthalten und
dauerhaft in der Datenbank sowie in jedem Export (Excel/PDF/JSON,
Milestone 6) landen — ein klarer Verstoß gegen Auftrag §12.

**Konsequenzen:** Jeder künftige Connector mit API-Schlüssel im
Query-String (z. B. eine spätere „günstig"-Tarif-Quelle) MUSS den
Schlüssel über `secret_params` übergeben, nicht über `params`. Ein
Test (`test_secret_params_landen_im_request_aber_nicht_in_der_
provenienz_url`, `tests/connectors/test_base_connector.py`) sichert
dieses Verhalten dauerhaft ab.

## ADR-14: Kanonisches Kennzahlen-Vokabular verbindlich ab Milestone 3

**Kontext:** `DataPoint.metric_name` speicherte bis Milestone 2 den
rohen XBRL-Tag-Namen der Quelle (z. B. `"Revenues"`). Der Docstring in
`normalization/models.py` kündigte bereits an, dass dieser Namensraum
„ab Milestone 3 im fundamentals-Modul verbindlich" definiert wird.

**Entscheidung:** `fundamentals/metrics.py` definiert ein kanonisches,
quellenunabhängiges Kennzahlen-Vokabular (`Metric`-Enum, z. B.
`Metric.REVENUE = "revenue"`) mit einem Mapping von SEC-US-GAAP-XBRL-
Tags auf diese Kennzahlen. `normalization/ingest.py::
ingest_sec_company_concept` löst jeden Tag verbindlich auf eine
kanonische Kennzahl auf (oder verlangt einen expliziten `metric`-
Override) und speichert `DataPoint.metric_name` fortan als kanonischen
Namen (z. B. `"revenue"` statt `"Revenues"`). Ein unbekannter Tag löst
einen `ValueError` aus, statt uneinheitlich unter dem Rohnamen
gespeichert zu werden.

**Konsequenz — bewusste Abhängigkeit `normalization` → `fundamentals`:**
Dies führt zu einer gerichteten Abhängigkeit von `normalization` auf
`fundamentals.metrics` (nicht umgekehrt, kein Zyklus: `fundamentals.
metrics` hat keine Abhängigkeit zurück zu `normalization`). Das weicht
von der reinen ADR-3-Modultrennung geringfügig ab, ist aber die
konsistente Umsetzung der bereits in Milestone 1 dokumentierten
Absicht. Migrationspfad für bereits gespeicherte Milestone-2-Testdaten:
keiner nötig, da in dieser Sandbox noch keine Produktivdaten aus echten
Quellenabrufen bestehen (siehe „Offene Risiken" in `PROGRESS.md`).

## ADR-15: Jahres-/Quartalstrennung ohne zusätzliches Metadatenfeld

**Kontext:** Der SEC-XBRL-Company-Concept-Endpoint liefert pro Fakt ein
`fp`-Feld (`"Q1"`/`"Q2"`/`"Q3"`/`"FY"`), das Quartals- von
Jahreswerten unterscheidet. `DataPoint` speichert dieses Feld bewusst
nicht separat (siehe `normalization/models.py`), um das Datenmodell
nicht auf eine quellenspezifische Konvention festzulegen, die für
künftige, nicht-SEC-Quellen ggf. nicht existiert.

**Entscheidung:** `fundamentals/series.py::select_annual_points` wählt
Jahrespunkte stattdessen geometrisch: vom jüngsten Zeitreihenpunkt
rückwärts wird ein weiterer Punkt nur aufgenommen, wenn er mindestens
330 Tage vor dem zuletzt aufgenommenen liegt. Funktioniert unabhängig
von Metadaten und sowohl für Fluss- als auch für Bestandsgrößen.

**Konsequenz:** Bei sehr unregelmäßiger Berichtsfrequenz (z. B.
Rumpfgeschäftsjahre nach einer Restrukturierung) kann die Heuristik
einzelne Perioden falsch einordnen. Dieses Risiko wird als vertretbar
eingestuft, da eine falsch eingeordnete Periode zu einem fehlenden
(`None`) statt einem falschen Wachstumswert führt — die
`growth_rate`-Funktion verlangt ohnehin eine exakte Kalenderjahr-
Übereinstimmung (siehe `calculations.py`) und liefert sonst `None`,
nie eine erfundene Zahl.

## ADR-16: Marktdaten (`PRICE_CLOSE`) als eigene Kategorie im Kennzahlen-Vokabular

**Kontext:** `valuation/` benötigt für Multiples und Sicherheitsmarge
den aktuellsten bekannten Kurs, ohne die Jahres-/Quartals-Heuristik aus
ADR-15 (die für Fundamentaldaten aus Filings gedacht ist) auf tägliche
Kursdaten anzuwenden.

**Entscheidung:** `fundamentals/metrics.py::Metric` erhält
`PRICE_CLOSE`, dokumentiert als Marktdatum, das weder zu
`FLOW_METRICS` noch zu `STOCK_METRICS` gehört, aber dieselbe
provenienzbehaftete, point-in-time-fähige Zeitreiheninfrastruktur
nutzt. `normalization/ingest.py::ingest_alpha_vantage_quote` speichert
fortan `Metric.PRICE_CLOSE.value` statt eines Literal-Strings (keine
Verhaltensänderung, nur Formalisierung). Neu:
`fundamentals/series.py::get_latest_value` liefert den jüngsten
bekannten Wert einer Kennzahl ohne Jahres-/Quartalsfilterung — für
Kurse ist „letzter bekannter Wert" die richtige Semantik, nicht
„letzter Jahreswert".

**Konsequenzen:** `valuation/report.py` nutzt `get_latest_value` für
den aktuellen Kurs; alle anderen Kennzahlen bleiben über
`get_latest_annual_value`/`select_annual_points` (ADR-15) angebunden.

## ADR-17: Scoring — nicht berechenbare Komponenten werden aus der Gewichtssumme entfernt, nicht mit 0 bewertet

**Kontext:** Auftrag §7 verlangt eine Startgewichtung über acht
Komponenten (Finanzqualität, Bewertung, Wachstum, Bilanzstärke,
Wettbewerbsvorteil, Management, Nachrichten, Datenqualität), verbietet
aber ausdrücklich, fehlende Daten neutral mit 0 zu bewerten. Zwei
Komponenten („Wettbewerbsvorteil", „Nachrichten und Katalysatoren")
sind mit dem aktuellen Datenstand (keine Textanalyse/News-Modul vor
Milestone 5) strukturell nicht berechenbar.

**Entscheidung:** `scoring/score.py::compute_score` berechnet den
Gesamtscore als gewichteten Durchschnitt ausschließlich über die
tatsächlich berechenbaren Komponenten; deren Gewichte werden auf 100 %
renormiert. Die nicht berechenbaren Komponenten werden explizit in
`NOT_YET_IMPLEMENTABLE_COMPONENTS` benannt und tauchen weder als
Teilscore noch als versteckte 0 auf. `coverage` (Anteil der
tatsächlich genutzten Gewichtssumme an der vollen Auftrag-§7-Gewichtung,
in dieser Milestone max. 85 %) macht diese Einschränkung sichtbar und
fließt zusätzlich als Konfidenzschwelle in die Klassifikation ein
(niedrige `coverage` oder niedrige `data_completeness` stufen auf
„Beobachten"/„Datenlage unzureichend" herab, auch bei hohem reinen
Score).

**Begründung:** Verhindert exakt das in Auftrag §7 verbotene Verhalten
(fehlende Daten = neutraler Malus), ohne die Berechenbarkeit der
übrigen sechs Komponenten zu verzögern; folgt demselben „ehrliche
Lücke dokumentieren statt vortäuschen"-Muster wie die zurückgestellten
textbasierten Warnsignale in Milestone 3
(`risk/warning_signals.py::NOT_YET_IMPLEMENTABLE_SIGNALS`).

**Konsequenzen:** Sobald das `news`-Modul (Milestone 5) und eine
strukturierte Wettbewerbsvorteil-Quelle verfügbar sind, werden die
beiden Komponenten ergänzt und `coverage` steigt entsprechend — kein
Schema-Bruch, da `ComponentScore`/`ScoreResult` bereits für eine
variable Anzahl an Komponenten ausgelegt sind.

## Noch zu treffende Entscheidungen

Keine blockierenden Entscheidungen mehr offen für Milestone 1–4 (alle
abgeschlossen, siehe `PROGRESS.md`). Verbleibende Detailfragen aus
`MILESTONE_0.md` Abschnitt B (z. B. weitere Feinjustierung der
Mindestmarktkapitalisierung) bleiben über den Ersteinrichtungsdialog im
laufenden Betrieb änderbar (Auftrag §2). Weiterhin offen: Priorisierung
der EU/DE-Meldungsquellen-Lücke (ADR-9), Auflösung der
Notierungswährung für Alpha-Vantage-Kurse, unternehmensspezifische
CAPM-Herleitung des WACC statt des groben Standardwerts, und ob die
Peer-Gruppen-Zuordnung um einen Größenfilter ergänzt werden soll (siehe
`TODO.md`).
