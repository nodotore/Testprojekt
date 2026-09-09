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

## ADR-18: Eigenes `NewsItem`-Modell statt Wiederverwendung von `DataPoint`

**Kontext:** Milestone 5 benötigt provenienzbehaftete Speicherung von
Nachrichtentreffern (GDELT, IR-RSS). `DataPoint` (ADR-6) ist auf
numerische Fakten mit Berichtsperiode/Einheit/Währung zugeschnitten —
ein Nachrichtentreffer ist dagegen ein Textdokument-Verweis (Titel, URL,
Domain, Sprache, Kurz-Ausschnitt).

**Entscheidung:** `news/models.py::NewsItem` ist ein eigenständiges
ORM-Modell, folgt aber demselben Provenienz-Grundprinzip wie
`DataPoint`: Referenz auf `Source`, Abrufzeitpunkt UTC, Inhalts-Hash zur
Nachprüfbarkeit (`content_hash`, eindeutig je `source_id`). Bewusst NICHT
gespeichert wird der volle Artikeltext (Urheberrecht/Fair-Use-Grenzen
der angebundenen Quellen) — nur Titel und ein kurzer, HTML-bereinigter
Ausschnitt (`summary_text`); der Volltext bleibt über `url` referenzierbar
(Auftrag §11).

**Konsequenzen:** `db/__init__.py::register_all_models()` importiert
zusätzlich `news.models`, damit Alembic-Autogenerate und `create_all`
(Tests) die neue Tabelle kennen. IR-RSS erhält KEINE eigene Source-Zeile
je Host (uneinheitliche, pro Emittent unterschiedliche Hosts) — eine
generische `"ir_rss"`-Source-Zeile dokumentiert das Verfahren, der
konkrete Host steht je Treffer in `NewsItem.domain`/`url`.

## ADR-19: Nachrichtenklassifikation deterministisch/regelbasiert, nie durch ein Sprachmodell

**Kontext:** Auftrag §6 verlangt, Nachrichten nach Quellqualität
(Unternehmensmeldung/unabhängiger Bericht/Kommentar) und implizit nach
Ereignistyp einzuordnen. Eine Sprachmodell-basierte Klassifikation wäre
naheliegend, widerspricht aber dem in ADR-6/Auftrag §8a etablierten
Grundsatz „Fakten und Einordnungen entstehen aus Code, ein Sprachmodell
fasst nur zusammen/erklärt" — sowie der fehlenden LLM-API-Anbindung in
dieser Entwicklungsumgebung (siehe `news/report.py`, offene Lücke
„KI-Zusammenfassung").

**Entscheidung:** `news/classification.py` klassifiziert ausschließlich
über einfache, im Code nachvollziehbare Regeln: Quellqualität aus dem
Connector-Ursprung (IR-RSS = per Definition Unternehmensmeldung) plus
einer kleinen, bewusst unvollständigen Domain-Liste für „Kommentar";
Ereignistyp über eine priorisierte Schlüsselwortliste (Kleinschreibung,
Teilstring-Suche, Deutsch/Englisch gemischt). Kein Treffer → `SONSTIGES`
statt eines geratenen Werts.

**Konsequenzen:** Die Klassifikation ist eine grobe, dokumentierte
Heuristik, keine redaktionelle Prüfung — Domain-/Schlüsselwortlisten
können bei Bedarf erweitert werden, ohne dass das ein Schema-Bruch wäre
(reine Konstantenlisten, keine Migration nötig). Dieselbe Prämisse gilt
für das Ereignis-Clustering (`news/clustering.py`): lexikalische
Titel-Ähnlichkeit (`difflib.SequenceMatcher`) statt Embeddings/
Sprachmodell — deterministisch reproduzierbar, auf Kosten semantischer
Präzision bei stark unterschiedlichem Wortlaut über dasselbe Ereignis.

## ADR-20: Neues Modul `portfolio/` über die ursprüngliche Auftrag-§4-Modulliste hinaus

**Kontext:** Auftrag §4 nennt eine feste Liste von Domänenmodulen
(`connectors, normalization, entity_resolution, fundamentals, valuation,
news, risk, scoring, backtesting, reports, ui, audit`). Auftrag §8
(„Portfolio- und Vergleichsfunktionen": Watchlist/Portfolio-Import,
Branchen-/Länder-/Währungs-/Faktor-Konzentration, Korrelation,
historische Drawdowns, Positionsgrößen-Bandbreiten, konfigurierbare
Transaktionskosten-/Steuer-/Liquiditäts-Annahmen) beschreibt jedoch
eigenständige Fachlogik, die in keinem der zwölf genannten Module
sauber unterzubringen ist — analog zur bereits in ADR-11 dokumentierten
Ergänzung um `config`/`db`.

**Entscheidung:** Ein neues Modul `portfolio/` wird ergänzt:
`models.py` (`WatchlistEntry`, `PortfolioPosition` — zwei getrennte,
schlanke Bestands-Snapshot-Modelle, keine Transaktionshistorie),
`csv_import.py` (manueller/CSV-Import, nutzt dieselbe
Entity-Auflösung wie alle anderen Ingestion-Pfade — nie Ticker allein,
Auftrag §5), `concentration.py`, `position_sizing.py`,
`risk_metrics.py` (reine Berechnungsfunktionen) und `report.py`
(DB-Orchestrierung zu `PortfolioReport`, dasselbe Muster wie
`fundamentals`/`valuation`/`news`).

**Konsequenz — bewusste Einschränkung ohne FX-Umrechnung:** Es existiert
kein Fremdwährungs-Umrechnungsmodell. Branchen-/Länder-Konzentration als
Prozentsatz wird nur berechnet, wenn alle einbezogenen Positionen
dieselbe Bestandswährung haben (sonst `computable=False` statt eines
irreführenden Werts, Auftrag §11); Währungs-Exposure wird deshalb separat
und ohne Prozentangabe über Währungsgrenzen hinweg ausgewiesen. Diese
Lücke ist strukturell dieselbe wie die unbekannte Alpha-Vantage-
Kurswährung (siehe ADR-16) und wird nicht durch eine erfundene
Umrechnung überbrückt.

**Konsequenz — Faktor-Konzentration nicht umgesetzt:** Wie schon bei den
zurückgestellten Warnsignalen (Milestone 3) und den beiden
nicht-berechenbaren Scoring-Komponenten (ADR-17) wird „Faktor-
Konzentration" (Value-/Growth-/Quality-Exposure je Position) explizit
als `NOT_YET_IMPLEMENTABLE_CONCENTRATIONS` benannt statt stillschweigend
wegzulassen — es existiert noch kein Faktormodell.

**Konsequenz — Korrelation/Drawdown meist „Datenlage unzureichend" in
dieser Umgebung:** Beide Kennzahlen benötigen eine Kurshistorie; Alpha
Vantage `GLOBAL_QUOTE` (Kostenlos-Paket) liefert nur den jeweils
aktuellen Kurs je Abruf. Bis genug Punkte über wiederholte Abrufe
akkumuliert sind, liefern `max_drawdown`/`pairwise_correlation`
strukturell `computable=False` — der ehrliche Normalfall, kein
Implementierungsfehler.

## ADR-21: `ReportBundle` als einzige Quelle der Wahrheit für alle Exportformate

**Kontext:** Auftrag §10 verlangt einen Excel-Export mit exakt sieben
Tabellenblättern (Zusammenfassung, Kennzahlen, Bewertung, Risiken,
Nachrichten, Quellen, Annahmen) sowie zusätzlich PDF- und JSON-Export
(Auftrag §2). Das Abnahmekriterium aus `PLAN.md` Milestone 6 verlangt,
dass der Export „exakt dieselben Werte wie die UI-Ansicht" zeigt.

**Entscheidung:** `reports/bundle.py::build_report_bundle` aggregiert
`FundamentalsReport`, `ValuationReport`, `ScoreResult` und `NewsReport`
(alle bereits unabhängig getestete, deterministische Bausteine aus
Milestone 3–5) zu einem einzigen `ReportBundle` — reine Aggregation,
keine neuen Zahlen. `reports/json_export.py::report_bundle_to_dict`
wandelt dieses Bundle strukturell in JSON-taugliche Werte um; sowohl
`reports/excel_export.py` als auch `reports/pdf_export.py` bauen
AUSSCHLIESSLICH auf demselben `report_bundle_to_dict()`-Ergebnis auf,
nie auf eigenen Datenbankabfragen.

**Begründung/Konsequenz:** Dadurch können zwei Exportformate für
dieselbe Analyse strukturell nicht unterschiedliche Werte zeigen — der
Beweis liegt im Code-Pfad, nicht in einem manuellen Abgleich. Eine
künftige UI-Detailseite (Auftrag §10 Seite 4, Milestone 8+) MUSS
ebenfalls von einem `ReportBundle` rendern, nicht von eigenen Anfragen,
damit das Abnahmekriterium „Export = UI-Werte" strukturell erhalten
bleibt — bis diese UI-Seite existiert, ist der vollständige
UI-vs.-Export-Abgleich nicht live nachprüfbar (offener Punkt, siehe
`PROGRESS.md`/`NEXT_STEPS.md`).

**Konsequenz — Formel-Injection-Schutz im Excel-Export (Auftrag §12):**
Nachrichtentitel/-URLs/-Domains stammen aus externen, nicht
vertrauenswürdigen Quellen. `excel_export.py::_sanitize_excel_string`
neutralisiert Zellwerte, die mit `=`, `+`, `-` oder `@` beginnen
(potenzielle Formel-Interpretation in Tabellenkalkulationen bzw.
Re-Import-Pfaden). Im PDF-Export läuft aus demselben Grund nur intern
generierter Text (Score-Begründungen, Annahmen) durch reportlabs
`Paragraph` (interpretiert minimales Markup) — externer Text
(Nachrichtentitel) wird aktuell nur aggregiert (Anzahl), nicht über
`Paragraph` gerendert.

## ADR-22: Point-in-time-Backtest — Universum, Strategie und dokumentierte Lücken

**Kontext:** Auftrag §9 stellt für Backtests die striktesten
Anti-Bias-Anforderungen des gesamten Auftrags: Point-in-time-Universum,
Vermeidung von Look-ahead-, Survivorship- und Selection-Bias,
Berücksichtigung von Kosten/Dividenden/Währungen, Train-/Validierungs-/
Out-of-Sample-Trennung, und ausdrücklich „keine Optimierung akzeptieren,
die nur auf einem Zeitraum oder wenigen Aktien funktioniert".

**Entscheidung — Punkt-in-Zeit-Universum:** `backtesting/universe.py::
get_point_in_time_universe(session, as_of)` definiert „zum Stichtag
bekannt" streng als „mindestens ein `DataPoint` mit `retrieved_at_utc
<= as_of`" — dieselbe Provenienz-Grundlage wie jede andere
Point-in-time-Abfrage in diesem Projekt (ADR-6). Der Nachweis „kein
Look-ahead" (Auftrag §9/PLAN.md-Abnahmekriterium) wird zweistufig
geführt: `tests/backtesting/test_universe.py` zeigt auf Ebene des
Universums, dass ein später hinzugefügter Kandidat ein früher
berechnetes Universum nicht verändert; `tests/backtesting/test_engine.py::
test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_backtest_
ergebnis_nicht` zeigt dasselbe auf Ebene eines vollständigen
Backtest-Laufs (Auswahl UND Portfoliorendite bit-identisch vor/nach dem
Eintreffen der späteren Daten).

**Entscheidung — Strategie ohne fittbaren Parameter:**
`backtesting/strategy.py::select_top_n` wählt je Rebalancing-Stichtag
die Kandidaten mit dem höchsten Score aus dem bereits bestehenden,
festen Scoring-System (Milestone 4, Startgewichtung gemäß Auftrag §7).
Es gibt in dieser Strategie keinen auf den Backtest-Zeitraum gefitteten
Parameter — eine strukturelle statt nachträglich geprüfte Absicherung
gegen „Optimierung, die nur auf einem Zeitraum funktioniert". Kandidaten
mit `total_score is None` ODER der Klassifikation „Datenlage
unzureichend" werden ausgeschlossen — `total_score` allein genügt nicht
als Filter, da die Datenqualitäts-Komponente (`_score_datenqualitaet`)
auch bei vollständig fehlenden Fundamentaldaten einen Zahlenwert (0)
liefert, keinen `None`; erst die bereits vorhandene Konfidenz-
Einstufung aus `compute_score` (ADR-17) macht diesen Fall zuverlässig
erkennbar.

**Konsequenz — drei bewusst offene Lücken, benannt statt verschwiegen**
(`backtesting/report.py::NOT_YET_IMPLEMENTABLE_BACKTEST_FEATURES`):
1. **Kein Benchmark-Vergleich:** Die Kostenlos-Datenquellen-Variante
   bindet keine Index-/Benchmark-Kursquelle an (Alpha Vantage Free
   liefert nur Einzelwerte je Symbol, siehe `DATA_SOURCES.md`).
   `build_backtest_report` akzeptiert optional eine bereits vorliegende
   Benchmark-Renditereihe; ohne sie bleibt der Vergleich `None`.
2. **Keine Währungsumrechnung:** dieselbe strukturelle Lücke wie
   ADR-16/ADR-20 — eine Portfoliorendite wird in der Kurswährung der
   zugrunde liegenden Positionen berechnet, nie umgerechnet.
3. **Unvollständiges Survivorship-Universum:** SEC EDGAR/Alpha Vantage
   liefern im Kostenlos-Paket keine systematische Delisting-Historie —
   das Punkt-in-Zeit-Universum umfasst „was das System zum Stichtag
   bereits erfasst hatte", nicht „was zum Stichtag historisch am Markt
   existierte". Ein tatsächlich delistetes, nie erfasstes Unternehmen
   fehlt weiterhin.

**Konsequenz — Dividendenrendite ist eine Schätzung:**
`backtesting/period_return.py::estimate_dividends_per_share` nähert die
Dividende je Aktie als `DIVIDENDS_PAID / SHARES_DILUTED` der jeweils
zuletzt bekannten Jahresperiode an — angewendet auf jede (i. d. R.
kürzere) Rebalancing-Periode, nicht anteilig aufgeteilt. Fehlt eine der
beiden Größen, wird 0 statt eines geratenen Werts angenommen. Dieselbe
Vereinfachung wie die bereits in Milestone 3 dokumentierte
Non-GAAP-/Ausschüttungsquote-Vereinfachung.

## ADR-23: Milestone-8-Security-Review — Befunde und Korrekturen

**Kontext:** Auftrag §15/PLAN.md verlangen zu Milestone 8 einen
dokumentierten Security-Review, der jede Behauptung in `SECURITY.md`
gegen das tatsächliche Verhalten des Codes prüft (nicht nur gegen die
Absicht). Durchgeführt: systematischer Abgleich jedes `SECURITY.md`-
Abschnitts mit dem Code (Secrets, SSRF, Downloadgrößen, Redirects,
Log-Redaction, Pflichthinweis, Abhängigkeits-Scan).

**Befund 1 — echte Implementierungslücke, behoben: fehlende
Downloadgrößen-Begrenzung.** `SECURITY.md` behauptete eine
Obergrenze je Connector; im Code existierte keine. Behoben durch
`ConnectorConfig.max_response_bytes` (Default 10 MB) und eine Prüfung
in `connectors/base.py::_request_with_retry` VOR jeder Statuscode-
Verzweigung/Parsing — eine übergroße Antwort wird ohne Retry und ohne
Cache-Schreibung mit `ConnectorValidationError` abgelehnt.

**Befund 2 — echte Implementierungslücke, behoben: unvollständige
Log-Redaction.** `RedactingFilter` bereinigte nur `record.msg`, nicht
`record.args` — ein Secret, das ausschließlich als %-Style-Platzhalter-
Argument übergeben wird (`logger.info("key=%s", value)`), taucht in
`record.msg` selbst nie auf und rutschte unredigiert durch. Behoben:
`record.args` wird jetzt ebenfalls durch `redact()` geführt (Tupel- und
Dict-Form, siehe `logging`-Konvention für Mapping-Argumente).

**Befund 3 — echte Compliance-Lücke, behoben: Pflichthinweis fehlte in
Berichtsexporten.** Auftrag §12 verlangt den Hinweis „an JEDER
Berichtsausgabe sichtbar", nicht nur in der UI. Der Hinweis existierte
bislang ausschließlich in `ui/app.py`. Behoben durch
`reports/bundle.py::MANDATORY_DISCLAIMER` (eigenständige Konstante,
NICHT aus `ui/` importiert — `reports/` darf laut Modulgrenzen ADR-3
nicht von `ui/` abhängen) als Pflichtfeld `ReportHeader.disclaimer`,
gerendert in der Zusammenfassung von JSON-, Excel- und PDF-Export.

**Befund 4 — Dokumentationsfehler, korrigiert: Redirect-Verhalten.**
`SECURITY.md` behauptete, Redirects würden „nur innerhalb derselben
Allowlist gefolgt". Tatsächlich verifiziert (`inspect.signature
(httpx.Client.__init__)`): `follow_redirects` ist `False` per Default
und wird im gesamten Code nie überschrieben — Redirects werden also nie
automatisch verfolgt (eine 3xx-Antwort ist für den Connector ein
gewöhnlicher, nicht-fehlerhafter Statuscode ohne Folgeaufruf). Das ist
strenger als die dokumentierte Allowlist-Prüfung pro Sprung, aber die
Dokumentation war sachlich falsch — korrigiert in `SECURITY.md`.

**Befund 5 — kein Fund, aber verifiziert: Prompt-Injection.** Es
existiert im gesamten Code aktuell KEIN Aufruf eines Sprachmodells
(verifiziert per Volltextsuche) — die in Auftrag §8a vorgesehene
KI-Zusammenfassung ist noch nicht implementiert (offener Punkt seit
ADR-19/`news/report.py`). Der dokumentierte Prompt-Injection-Schutz
(„abgerufener Fremdtext wird nie als Instruktion behandelt") ist damit
aktuell nicht akut prüfbar, aber auch nicht verletzt — `news/
sanitize.py` entfernt bereits jegliches HTML-Markup/Skripte, bevor der
Text überhaupt gespeichert wird. Sobald eine KI-Zusammenfassung
implementiert wird, MUSS dieser Review-Punkt erneut geprüft werden
(Nachtrag in `TODO.md`).

**Befund 6 — kein Fund, verifiziert als bereits korrekt:** Secrets
(`SecretStore`, ADR-5), SSRF-Schutz (Allowlist + DNS-Rebinding-Prüfung
vor Verbindungsaufbau, `connectors/ssrf.py`), `.gitignore`-Ausschlüsse
für lokale Secret-/DB-Dateien, Abhängigkeits-Scan (`pip-audit`: „No
known vulnerabilities found", Stand 2026-09-08).

**Offen, nicht blockierend, dokumentiert statt verschwiegen:**
`SecretStore` ist noch in keine UI-Seite eingebunden (es existiert
noch keine Screener-/Einstellungsseite, die einen API-Schlüssel
entgegennimmt) — nachzuholen, sobald diese UI-Seite gebaut wird.

## ADR-24: Milestone-8-Ausfalltests — Befunde und neue Bausteine

**Kontext:** Auftrag §15/SECURITY.md „Offene Punkte für Milestone 8"
verlangen gezielte Ausfalltests: manipulierte/böswillige Webinhalte
(inkl. simulierter Prompt-Injection), absichtlich falsche/
widersprüchliche Testdaten, Rate-Limit-Überschreitung je Connector, und
einen end-to-end getesteten Restore-Prozess.

**Befund — echte Sicherheitslücke, behoben: XML-Entity-Expansion
(„Billion Laughs") im IR-RSS-Connector.** `connectors/ir_rss.py`
parste RSS-/Atom-Feeds (externe, nicht vertrauenswürdige Quelle) über
die Python-Stdlib `xml.etree.ElementTree`. Laut Python-Dokumentation
ist diese NICHT gegen böswillig konstruiertes XML gehärtet — eine
wenige hundert Bytes große Payload mit rekursiven Entity-Definitionen
kann beim Parsen mehrere Gigabyte Speicher belegen (Denial-of-Service).
Die bereits vorhandene HTTP-Größenobergrenze
(`ConnectorConfig.max_response_bytes`, siehe ADR-23) schützt davor
NICHT, da der Angriff erst beim Parsen entsteht, nicht beim Download —
die Payload selbst ist klein. Behoben durch Ersetzen von
`xml.etree.ElementTree` durch `defusedxml.ElementTree` (neue
Abhängigkeit, `pyproject.toml`); Entity-Definitionen werden dort
grundsätzlich abgelehnt (`defusedxml.common.DefusedXmlException`,
konkret `EntitiesForbidden`) statt verarbeitet. Test mit einer
klassischen „Billion Laughs"-Payload beweist die Ablehnung
(`tests/connectors/test_ir_rss.py::
test_parse_feed_lehnt_billion_laughs_angriff_ab`). Andere Connectoren
(SEC EDGAR, Alpha Vantage, GDELT) sind reine JSON-Konsumenten — JSON
kennt kein Entity-Konstrukt, dieselbe Angriffsklasse existiert dort
nicht.

**Befund — kein Fund, verifiziert: Prompt-Injection in News-Inhalten.**
Neuer End-to-End-Test
(`tests/news/test_ingest.py::
test_prompt_injection_versuch_landet_als_reine_nutzdaten`) belegt: ein
Titel/Zusammenfassungstext mit einem klassischen Prompt-Injection-
Versuch („Ignoriere alle bisherigen Anweisungen...") durchläuft die
gesamte Ingestion-Pipeline unverändert als reine Zeichenkette — HTML-
Markup darin wird entfernt (`news/sanitize.py`), der Text selbst wird
nirgends geparst/ausgeführt/interpretiert. Bestätigt praktisch, was
ADR-23 Befund 5 bereits strukturell feststellte.

**Befund — kein Fund, verifiziert: widersprüchliche/extreme Daten
führen zu sichtbarer Warnung.** Neuer End-to-End-Test
(`tests/scoring/test_score.py::
test_score_entity_widerspruechliche_daten_fuehren_zu_sichtbarer_warnung`)
belegt am vollständigen Fundamentals→Scoring-Pipeline-Durchlauf: eine
absichtlich implausible Eingabe (Versechsfachung der verwässerten
Aktienanzahl in drei Jahren) löst das bereits bestehende
Warnsignal-System aus (`risk_deductions` nicht leer,
`total_score < raw_score`, `top_risks` nicht leer) — keine stille
Fehlkalkulation. Bestätigt die in Milestone 3/4 gebaute Mechanik
(`risk/warning_signals.py`, `scoring/score.py`) end-to-end statt nur
auf Komponentenebene.

**Befund — kein Fund, nicht implementiert (aus Datenlage strukturell
nicht möglich): Auftrag-§3-„bei Widerspruch beide Werte zeigen".** Es
existiert derzeit kein Mechanismus, der bei zwei unabhängigen Quellen
mit widersprüchlichem Wert für dieselbe Kennzahl+Periode beide Werte
sichtbar macht — `fundamentals/series.py` löst mehrere `DataPoint`-
Zeilen je Periode nach „zuletzt bekannt gewordener Wert gewinnt" auf
(Restatement-Semantik, siehe ADR-6), nicht nach „mehrere gleichzeitig
gültige Quellen". Mit den aktuell angebundenen Quellen (SEC EDGAR
liefert Fundamentaldaten, Alpha Vantage liefert ausschließlich Kurse)
gibt es strukturell noch keine zwei sich überschneidenden Quellen für
dieselbe Fundamentalkennzahl — das Szenario kann mit dem aktuellen
Kostenlos-Quellen-Set nicht auftreten. Als offene, dokumentierte Lücke
festgehalten (nicht verschwiegen) für den Zeitpunkt, an dem eine zweite
Fundamentaldatenquelle hinzukommt (siehe `TODO.md`).

**Neuer Baustein — Restore-Prozess (Backup/Wiederherstellung):**
`db/backup.py` (`backup_database`/`restore_database`). Bei lokalem
Betrieb (SQLite als einzelne Datei, Milestone-0-Entscheidung) bedeutet
Sicherung eine atomare, zeitgestempelte Dateikopie unter
`data_dir/backups/` (Kopie über temporäre Datei + `Path.replace`, um
eine sichtbare halbgeschriebene Zieldatei bei Abbruch zu vermeiden),
Wiederherstellung das Zurückkopieren derselben Datei über die aktuelle
Datenbankdatei. Bewusst NICHT für eine konfigurierte
Nicht-SQLite-`database_url` (z. B. künftiges PostgreSQL) implementiert
— dort übernimmt die jeweilige Datenbank ihr eigenes Backup-Tooling;
ein Aufruf wird mit `BackupError` klar abgelehnt statt eine falsche
Aktion vorzutäuschen. End-to-end getestet
(`tests/db/test_backup.py`): Sicherung → simulierter Datenverlust
(Live-Datei wird überschrieben) → Wiederherstellung → Daten sind
vollständig wieder da (`test_end_zu_end_restore_prozess_stellt_daten_
nach_datenverlust_wieder_her`).

**Rate-Limit-Überschreitung je Connector:** bereits durch den
bestehenden generischen Test
`tests/connectors/test_base_connector.py::
test_429_wird_als_rate_limit_fehler_gemeldet` abgedeckt — da alle
Connectoren (SEC EDGAR, Alpha Vantage, GDELT, IR-RSS) auf derselben
`Connector._request_with_retry`-Implementierung aufbauen, gilt der
Nachweis für jeden von ihnen; kein connectorspezifischer Sonderfall
gefunden. Der `RateLimiter` selbst ist bereits umfassend auf
Fensterlogik/Wartezeit getestet (`tests/connectors/
test_rate_limiter.py`, aus Milestone 1/2).

## ADR-25: Unabhängiger Security-/Plausibilitätscheck (Auftrag §15, Kriterium 9)

**Kontext:** Auftrag §15 verlangt „ein unabhängiger Security- und
Plausibilitätscheck ist dokumentiert". Der eigene Review des
implementierenden Agenten (ADR-23/ADR-24) ist gründlich, aber nicht
unabhängig — derselbe Akteur, der den Code schrieb, kann dieselben
blinden Flecken haben. Daher wurde ein separater, eigenständiger
Agentenlauf ohne Kenntnis der vorherigen Implementierungsentscheidungen
beauftragt, denselben Codestand mit frischem Blick gegen `SECURITY.md`,
`METHODOLOGY.md` und die Backtesting-Look-ahead-Garantie zu prüfen —
die in `PLAN.md` (Milestone 8) vorgesehene Rollentrennung
(„security-reviewer" + „test-agent"), hier umgesetzt über einen
zweiten, unabhängigen Agentendurchlauf statt formal getrennter
Sub-Agenten-Rollen.

**Befund 1 — BLOCKIEREND, gefunden und behoben: Look-ahead-Bias in den
Warnsignal-Checks.** `risk/warning_signals.py::run_all_checks` nahm
KEIN `as_of`-Argument entgegen; jeder einzelne Check (`check_cashflow_
divergence`, `check_strong_dilution`, `check_high_stock_based_
compensation`, `check_unusual_receivables_growth`, `check_unusual_
inventory_growth`, `check_late_filing`) griff dadurch intern auf den
Default in `series.get_*()` zurück — den AKTUELLEN Zeitpunkt, nicht den
Analysestichtag. `fundamentals/report.py::build_fundamentals_report`
rief `run_all_checks(session, entity)` ohne `as_of` auf, obwohl JEDE
andere Abfrage in derselben Funktion `reference` korrekt durchreicht.
Da `FundamentalsReport.warning_signals` direkt in
`scoring/score.py::compute_score`s `risk_deductions`/`total_score`
einfließt und `total_score` wiederum das Ranking-Kriterium von
`backtesting/strategy.py::select_top_n` ist, konnte ein Backtest „per
Februar" durch Warnsignal-relevante Daten beeinflusst werden, die erst
NACH Februar bekannt wurden (z. B. eine spätere Restatement-Zeile) —
ein struktureller Verstoß gegen das Point-in-time-Prinzip (Auftrag §9)
und damit gegen genau das Auftrag-§15-Kriterium „Backtests nachweislich
kein Look-ahead", das Milestone 8 abnehmen soll.

Warum der bereits bestehende Backtest-Look-ahead-Test
(`tests/backtesting/test_engine.py::
test_spaeter_bekannt_gewordener_kandidat_veraendert_frueheres_
backtest_ergebnis_nicht`) das nicht auffing: er fügt eine komplett NEUE
Entity erst später hinzu, nie eine später eintreffende Zeile für eine
BEREITS bekannte Entity — genau die vom Fehler betroffene Konstellation
blieb dadurch ungetestet. Eine Lücke im Testdesign, kein reiner
Implementierungsfehler.

**Behoben:** `run_all_checks` und jede einzelne `check_*`-Funktion in
`risk/warning_signals.py` nehmen jetzt ein `as_of`-Schlüsselwortargument
entgegen und reichen es an jede `series.get_*`-Abfrage durch;
`fundamentals/report.py` ruft `run_all_checks(session, entity,
as_of=reference)` auf. Zwei neue Regressionstests decken exakt das vom
Review benannte Szenario ab: eine später eintreffende Korrektur für
eine bereits bekannte Entity darf ein früheres Ergebnis nicht verändern
— einmal auf Ebene der isolierten Warnsignal-Funktion
(`tests/risk/test_warning_signals.py::
test_run_all_checks_ignoriert_zum_stichtag_noch_unbekannte_daten`) und
einmal auf Ebene der vollständigen Score-Integration
(`tests/scoring/test_score.py::
test_score_entity_ignoriert_zum_stichtag_noch_unbekanntes_
warnsignal`).

**Befund 2 — sollte behoben werden, behoben: Downloadgrößen-Prüfung
puffert erst vollständig, bevor sie greift.** `_request_with_retry`
rief `self._client.get(url, ...)` (nicht gestreamt) auf und prüfte
`len(response.content) > max_response_bytes` erst DANACH — zu diesem
Zeitpunkt hatte `httpx` die komplette Antwort bereits vollständig in
den Speicher gelesen. Die „10-MB-Obergrenze" begrenzte damit nicht den
Speicherverbrauch gegen eine böswillige/fehlerhafte Quelle, sondern
lehnte nur nachträglich ab. Behoben: `_request_with_retry` nutzt jetzt
`self._client.stream("GET", url, ...)` und bricht den Download ab,
sobald die kumulierte Byte-Anzahl die Grenze überschreitet — VOR
vollständigem Empfang. Bestehende Tests
(`tests/connectors/test_base_connector.py`) bestätigen unverändertes
Verhalten nach außen (Ablehnung, kein Retry, kein Cache-Eintrag).

**Befund 3 — sollte behoben werden, behoben: HTML-Sanitizing-Fallback
widersprach der eigenen Zusicherung.** `news/sanitize.py::
sanitize_html_to_text` fiel im (praktisch nie eintretenden) Fall einer
Ausnahme in `HTMLParser` auf `text = raw` zurück — den UNVERÄNDERTEN
Rohtext inklusive jeglichen Markups, obwohl die Modul-Zusicherung
„kein Markup bleibt erhalten" lautet. Kein akutes Risiko (kein
`unsafe_allow_html` irgendwo im Code, siehe ADR-23 Befund 6), aber eine
latente Falle für künftigen UI-Code, der sich auf diese Zusicherung
verlässt. Behoben: Fallback nutzt jetzt einen groben Regex-Tag-
Entferner (`_TAG_PATTERN`) statt des Rohtexts. Regressionstest erzwingt
eine `HTMLParser`-Ausnahme künstlich (`unittest.mock.patch.object`) und
prüft, dass kein Markup mehr durchrutscht
(`tests/news/test_sanitize.py::
test_ausnahme_im_parser_laesst_kein_rohes_markup_durch`).

**Befund 4 — bewusst NICHT behoben, ehrlich dokumentiert:
SSRF-Time-of-check-to-time-of-use-Lücke.** `connectors/ssrf.py::
assert_safe_url` löst den Hostnamen selbst auf und validiert die IP;
die tatsächliche HTTP-Anfrage über `httpx.Client` führt danach ihre
EIGENE, erneute DNS-Auflösung durch — zwischen Prüfung und
Verbindungsaufbau liegt ein theoretisches Zeitfenster (Rate-Limiter-
Wartezeit, Retry-Backoff), in dem sich ein DNS-Eintrag ändern könnte.
Eine robuste Behebung (validierte IP über einen eigenen Transport/
Resolver fest an die tatsächliche Verbindung binden) erfordert einen
nicht trivialen Umbau der HTTP-Transportschicht — als riskante,
kurzfristige Änderung an sicherheitskritischem Code bewusst NICHT in
dieser Sitzung umgesetzt, um kein neues, ungetestetes Risiko
einzuführen. Für dieses lokale Ein-Nutzer-Werkzeug (keine
Mehrbenutzer-/Internet-Dienst-Exposition) als tragbares Restrisiko
eingestuft, aber die vorherige Dokumentation (die dies implizit als
vollständig geschlossen darstellte) in `SECURITY.md` korrigiert.
Empfohlene künftige Behebung dort und in `NEXT_STEPS.md` festgehalten.

**Befund 5 — bestätigt, kein Fund:** Finanzmathematik (DCF, Multiples,
Fundamentalkennzahlen, Scoring) wurde als stimmig mit `METHODOLOGY.md`
und mit Standard-Finanzanalyse-Definitionen bewertet. Der
defusedxml-Fix aus ADR-24 wurde als korrekt eingebunden bestätigt.

**Gesamturteil des unabhängigen Reviews:** Vor Behebung von Befund 1
wäre eine Milestone-8-Abnahme nicht zu rechtfertigen gewesen — das
Look-ahead-Kriterium (Auftrag §15) war faktisch verletzt. Nach
Behebung aller vier Befunde (453 Tests grün, `ruff`/`mypy` fehlerfrei)
gilt Auftrag-§15-Kriterium 7 („Backtests nachweislich kein Look-ahead")
als erfüllt — siehe `ABNAHME.md` für die vollständige, kriterienweise
Abnahmebewertung.

## ADR-26: Marktscreener — neues `ingestion/`-Modul, Sidebar-Navigation, SecretStore in der UI

**Kontext:** Nach Abschluss von Milestone 8 (alle neun Auftrag-§15-
Kriterien bewertet, siehe ADR-25/`ABNAHME.md`) wurde mit dem Ausbau der
neun noch fehlenden Auftrag-§10-Oberflächenseiten begonnen. Erste Seite:
**Marktscreener** (Auftrag §10, Seite 2) — Unternehmen per CIK/Ticker
hinzufügen, SEC-EDGAR-Fundamentaldaten und optional einen Alpha-Vantage-
Kurs abrufen.

**Entscheidung — neues Modul `ingestion/`:** Die Orchestrierung
„Ticker/CIK → Entity finden/anlegen → alle bekannten XBRL-Kennzahlen
abrufen und speichern" passt in kein bestehendes Modul aus ADR-3 (sie
bindet `connectors/`, `entity_resolution/` und `normalization/`
zusammen, erzeugt aber selbst keine neuen Werte). Neues Modul
`ingestion/pipeline.py`, konsequent nach demselben Muster wie die
übrigen späteren Modul-Ergänzungen (`portfolio/` in Milestone 6,
`backtesting/` in Milestone 7): nimmt bereits konstruierte Connector-
Instanzen entgegen (Dependency Injection) statt selbst HTTP-Clients zu
konfigurieren — bleibt dadurch vollständig ohne echten Netzwerkzugriff
testbar (`tests/ingestion/test_pipeline.py`, `httpx.MockTransport`,
identisches Muster wie `tests/connectors/`).

**Entscheidung — XBRL-Tag-Mehrdeutigkeit:** `fundamentals/metrics.py::
SEC_US_GAAP_TAG_TO_METRIC` bildet mehrere XBRL-Tags auf dieselbe
kanonische Kennzahl ab (z. B. drei Revenue-Varianten), da Unternehmen
je nach Taxonomie-Version unterschiedliche Tags melden.
`ingestion/pipeline.py::TAG_CANDIDATES_BY_METRIC` gruppiert das Mapping
umgekehrt (Kennzahl → Tag-Kandidaten) und probiert beim Abruf jeden
Kandidaten der Reihe nach; ein HTTP 404 (dieses Unternehmen meldet
diesen konkreten Tag nicht) gilt NICHT als Fehlschlag der gesamten
Ingestion, sondern die Kennzahl landet in `nicht_gemeldete_kennzahlen`
— sichtbar für den Nutzer, aber kein Abbruch (Auftrag §4: „Fail loud"
gilt für echte Fehler, nicht für eine einzelne, von diesem Unternehmen
schlicht nicht gemeldete Kennzahl). Jeder andere Fehler (Timeout, 5xx,
kaputtes Format) wird ungefiltert durchgereicht.

**Entscheidung — neues Profilfeld `sec_edgar_kontakt_email`:** SEC
EDGAR verlangt eine Kontaktadresse im User-Agent jeder Anfrage (Fair-
Access-Policy). Bewusst NICHT automatisch aus einem Anmeldekonto/einer
Systemeinstellung übernommen — Auftrag §12 verbietet die Weitergabe
von Nutzerdaten an Dritte ohne ausdrückliche Zustimmung; SEC EDGAR ist
aus Sicht dieses Programms ein Dritter. Stattdessen ein eigenes,
ausdrücklich vom Nutzer im Ersteinrichtungsdialog gesetztes Profilfeld
(`NutzerProfil.sec_edgar_kontakt_email`, Grobformat-Validierung). Ohne
gesetztes Feld zeigt der Marktscreener eine klare Fehlermeldung statt
eines unbenutzbaren Formulars oder eines automatisch geratenen Werts.

**Entscheidung — SecretStore in `AppContext`, aber kein Master-
Passwort-Dialog:** `ui/bootstrap.py::bootstrap()` versucht jetzt
`get_secret_store()` ausschließlich über das OS-Keyring (kein Master-
Passwort-Parameter) — unter Windows funktioniert das i. d. R. ohne
weitere Einrichtung über den Credential Manager. Schlägt das fehl,
bleibt `AppContext.secret_store` bewusst `None` statt eine
Passwortabfrage zu erzwingen, für die noch keine Oberflächenseite
existiert (die „Einstellungen"-Seite, Auftrag §10 Seite 10, folgt noch
— dort gehört die Schlüsselverwaltung inkl. Datei-Fallback-Passwort
hin, siehe TODO.md). Der Marktscreener prüft `secret_store`/den
Alpha-Vantage-Schlüssel defensiv und bietet den Kursabruf einfach nicht
an, statt abzustürzen.

**Entscheidung — Sidebar-`st.radio` statt `st.navigation()`/`st.Page()`:**
Mit aktuell zwei Seiten hält eine einfache `st.sidebar.radio(...)`-
Auswahl in `app.py::main()` den bestehenden Testansatz
(`AppTest.from_file`, `tests/ui/test_app_smoke.py`) unverändert
funktionsfähig. Sobald weitere der neun Auftrag-§10-Seiten dazukommen
(spätestens ab vier bis fünf Seiten wird eine flache Radio-Liste
unübersichtlich), ist der Wechsel auf `st.navigation()`/`st.Page()`
vorgesehen — im Code als Kommentar vermerkt, in `NEXT_STEPS.md`
geführt.

**Neuer Baustein:** `AppSettings.cache_dir` (`data_dir/cache`) für
`connectors.cache.FileCache` — bislang wurde `FileCache` nur in Tests
verwendet, der Marktscreener ist die erste Stelle, die einen Connector
tatsächlich produktiv mit Cache verwendet.

**Tests:** 20 neue Tests (8 `ingestion/pipeline.py`, 4 `list_entities`,
2 Profilfeld-Validierung, 2 neue `AppTest`-Smoke-Tests für die
Marktscreener-Seite, weitere kleinere Ergänzungen) — insgesamt 471,
`ruff`/`mypy` fehlerfrei. Zusätzlich mit echtem Playwright-Browser
gegen einen laufenden Streamlit-Prozess verifiziert (Seite rendert,
Navigation funktioniert, Formularvalidierung bei leerer Eingabe zeigt
korrekt eine Fehlermeldung ohne Absturz) — ein tatsächlicher SEC-EDGAR-
Live-Abruf konnte in dieser Sandbox mangels Internetzugang nicht
getestet werden (dieselbe, seit Milestone 2 durchgängig dokumentierte
Einschränkung).

## ADR-27: Unternehmensdetail mit Quellenleiste — vollständiges Report-Rendering, Auftrag-§15-Kriterium 8 strukturell erfüllt

**Kontext:** Zweite der neun noch fehlenden Auftrag-§10-Oberflächen-
seiten nach dem Marktscreener (ADR-26): **Unternehmensdetail mit
Quellenleiste** (Auftrag §10, Seite 4) — der vollständige Bericht
(Kennzahlen, Bewertung, Score, Nachrichten, Quellen) für ein einzelnes
Unternehmen. Bewusst als zweite Seite priorisiert (vor Kandidaten-
Rangliste), weil sie die erste UI-Seite ist, die tatsächlich
`FundamentalsReport`/`ValuationReport`/`ScoreResult`-Werte anzeigt —
`ABNAHME.md` führte Auftrag-§15-Kriterium 8 („Exporte = Oberflächen-
werte") bislang als „strukturell fundiert, aber empirisch nicht
nachweisbar" auf, da mangels UI-Detailseite kein Vergleich zwischen
angezeigten und exportierten Werten möglich war.

**Entscheidung — ausschließlich aus `ReportBundle` rendern:** Neues
Modul `ui/detail.py` ruft `reports/bundle.py::build_report_bundle` auf
und rendert danach ausschließlich aus `report_bundle_to_dict(bundle)`
— demselben Dict, das `report_bundle_to_json`/`build_excel_workbook`/
`build_pdf_bytes` für die Exportformate verwenden (ADR-21). Die Seite
selbst berechnet nichts nach und rundet nichts eigenständig (Auftrag
§11: keine neuen Werte in der UI-Schicht). Damit ist strukturell
garantiert, dass UI und Exporte nie auseinanderlaufen können — Kriterium
8 gilt damit als erfüllt, siehe aktualisierte Bewertung in `ABNAHME.md`.
Die drei Download-Buttons (JSON/Excel/PDF) auf derselben Seite bauen
bewusst aus demselben bereits im Speicher vorliegenden `bundle`-Objekt,
nicht aus einer zweiten, separaten Berechnung.

**Entscheidung — Kopfzeile nach Auftrag-§10-Pflichtangaben:** Ganz oben
auf der Seite erscheinen Datenstand (`as_of`), Analysezeit
(`generated_at_utc`), Marktdatenverzögerungshinweis, Datenabdeckung und
Konfidenz (Score-Coverage) — exakt die von Auftrag §10 für jeden
Bericht geforderten Angaben, direkt aus `bundle.header` übernommen statt
neu zusammengestellt.

**Entscheidung — `_kennzahl()`-Formatierung statt Streamlit-Rohanzeige:**
Eine private Hilfsfunktion formatiert jeden Kennzahlenwert für die
Anzeige: `None` wird immer als „—" dargestellt (nie als 0 oder eine
andere geratene Zahl, Auftrag §11), `bool` wird vor dem allgemeinen
Zahlenzweig behandelt (da `bool` in Python eine `int`-Unterklasse ist
und sonst fälschlich als 1/0 formatiert würde), Prozentwerte erhalten
ein Vorzeichen. Einheitlich für Kennzahlen, Bewertung und Score
verwendet, damit „fehlend" nirgends auf der Seite wie ein echter
Messwert aussieht.

**Entscheidung — Auswahl über `ui/screener.py::list_entities`
wiederverwendet:** Statt einer zweiten Abfragefunktion nutzt die
Unternehmensauswahl (Dropdown) dieselbe `list_entities()`-Funktion wie
der Marktscreener. Beim Laden des vollständigen Berichts wird die
Entity anschließend in einer neuen Session per `session.get(Entity,
entity_id)` erneut geladen (nicht `session.add()` auf der bereits
detached-geladenen Instanz — das hätte einen SQLAlchemy-Fehler
ausgelöst, siehe Debugging-Historie in `PROGRESS.md`).

**Tests:** 7 neue Tests (5 reine Formatierungstests für `_kennzahl()`
in `tests/ui/test_detail.py`, 2 neue `AppTest`-Smoke-Tests in
`tests/ui/test_app_smoke.py` — leerer Zustand ohne erfasste
Unternehmen sowie voller Bericht mit synthetisch befüllter
Testdatenbank, gleiches Muster wie `tests/reports/test_bundle.py`) —
insgesamt 478, `ruff`/`mypy` fehlerfrei. Zusätzlich mit echtem
Playwright-Browser gegen einen laufenden Streamlit-Prozess mit
synthetisch befüllter Testdatenbank verifiziert: alle Abschnitte
(Kopfzeile, Kennzahlen, Bewertung inkl. DCF-Szenarien, Score inkl.
Risikoabzügen, Nachrichten, Quellenleiste mit Lizenzhinweisen,
Annahmen, drei Download-Buttons) rendern korrekt und ohne
Konsolenfehler (abgesehen von erwarteten, harmlosen Streamlit-
Telemetrie-Fehlschlägen mangels Internetzugang in dieser Sandbox).

## ADR-28: Kandidaten-Rangliste — Rangfolge NUR über bereits erfasste Unternehmen, ReportBundle je Zeile

**Kontext:** Dritte der neun noch fehlenden Auftrag-§10-Oberflächen-
seiten: **Kandidaten-Rangliste** (Auftrag §10, Seite 3) — eine
sortierbare Tabelle aller Unternehmen nach Gesamtscore.
`scoring/score.py::score_entity` bzw. `reports/bundle.py::
build_report_bundle` lagen bereits vollständig vor (Milestone 4/6);
es fehlte nur die Bildschirmseite.

**Entscheidung — Rangliste NUR über bereits erfasste Unternehmen, keine
Breitensuche:** Auftrag §10 nennt die vorherige Seite „Marktscreener
MIT Filtern" — dieses Programm hat aber (noch) keine Möglichkeit, eine
größere Grundgesamtheit von Aktien automatisch zu durchsuchen; der
Marktscreener (ADR-26) fügt Unternehmen einzeln per CIK/Ticker hinzu.
Die Kandidaten-Rangliste rankt deshalb bewusst NUR die bereits über den
Marktscreener erfassten Unternehmen (`ui/screener.py::list_entities`),
nicht ein größeres Universum — alles andere würde eine Fähigkeit
vortäuschen, die nicht existiert (Auftrag §16). Als dokumentierte
Lücke in `NEXT_STEPS.md` geführt: eine echte Breitensuche (z. B. über
eine SEC-EDGAR-Volltextsuche oder eine Ticker-Liste) ist ein möglicher
künftiger Ausbauschritt des Marktscreeners, kein Bestandteil dieser
Seite.

**Entscheidung — `build_report_bundle` je Zeile statt nur
`score_entity`:** Obwohl `score_entity()` laut eigenem Docstring
bereits „der bequeme Einstiegspunkt für die UI/Rangliste" ist, baut
`ui/ranking.py` stattdessen für jede Zeile den vollständigen
`ReportBundle` (wie `ui/detail.py`, ADR-27) und liest Score,
Datenabdeckung und Klassifikation aus `bundle.header`/`bundle.score`.
Grund: dieselbe strukturelle Garantie wie auf der Detailseite — die
Rangliste zeigt garantiert exakt denselben Score, dieselbe
Datenabdeckung und dieselbe Klassifikation wie die Detailseite und die
Exporte für dasselbe Unternehmen, da alle drei aus demselben
`report_bundle_to_dict()`-Dict lesen. Der zusätzliche Rechenaufwand
(Bewertung/DCF/Peers/Nachrichten werden mitberechnet, obwohl nur Score
und Datenabdeckung angezeigt werden) ist bei der aktuell kleinen,
manuell gepflegten Anzahl erfasster Unternehmen unkritisch; sollte die
Anzahl später groß werden, ist ein schlankerer Pfad über `score_entity`
direkt eine mögliche spätere Optimierung (in `NEXT_STEPS.md` vermerkt).

**Entscheidung — Score 0.0 bei fehlenden Daten ist ein echter Wert,
keine Lücke:** Beim Testen zeigte sich, dass ein Unternehmen ganz ohne
Rohdaten NICHT `total_score=None` erhält, sondern `0.0` — die
Scoring-Komponente „Datenqualität/Aktualität"
(`_score_datenqualitaet`) bewertet `data_completeness` immer
numerisch, auch bei 0 %, und ist damit die einzige verfügbare
Komponente. Das ist kein Darstellungsfehler und keine geratene Zahl,
sondern das korrekte, deterministische Ergebnis der bestehenden
Score-Formel (Milestone 4) — sie wird hier nur zum ersten Mal in der
Rangliste sichtbar. Statt einer irreführenden Meldung über „fehlende
Scores" zeigt die Seite stattdessen eine Warnung über die Anzahl
Unternehmen mit Klassifikation „Datenlage unzureichend" — diese ist
inhaltlich zutreffend und bereits an anderer Stelle etabliert
(Kriterium `_classify`, Milestone 4).

**Entscheidung — sortierbare Tabelle über natives `st.dataframe`:**
Kein eigenes Sortier-UI gebaut — Streamlits `st.dataframe` (auf
`glide-data-grid` basierend) ist bereits klick-sortierbar über die
Spaltenkopfzeile. Da dieses Raster auf `<canvas>` statt echtem DOM
rendert, lässt es sich nicht über Playwrights ARIA-Rollen-Locators
ansteuern — beim Live-Test wurde daher nur der initiale Render (Daten,
Standard-Sortierung, Warnhinweis) per Screenshot geprüft, nicht ein
Klick auf die Kopfzeile selbst; das native Sortierverhalten ist eine
von Streamlit getestete Plattform-Eigenschaft, keine hier neu gebaute
Logik.

**Tests:** 4 neue Tests (insgesamt 482) — 2 reine Tests für
`_rangliste_dataframe()` (`tests/ui/test_ranking.py`: Sortierung nach
Score absteigend, Score 0.0 bei fehlenden Daten statt eines fehlenden
Werts), 2 neue `AppTest`-Smoke-Tests (`tests/ui/test_app_smoke.py`):
leerer Zustand ohne erfasste Unternehmen sowie eine Zeile mit
synthetisch befüllter Testdatenbank. `ruff`/`mypy` fehlerfrei.
Zusätzlich mit echtem Playwright-Browser gegen einen laufenden
Streamlit-Prozess mit drei synthetisch befüllten Unternehmen
verifiziert (zwei mit unterschiedlich skalierten Finanzdaten, eines
ganz ohne Daten) — Rangfolge, Score-Werte, Klassifikationen und die
Warnung bei unzureichender Datenlage rendern korrekt, keine
unerwarteten Konsolenfehler.

## ADR-29: Peer-Vergleich — Vergleichstabelle je aus vollständigem ReportBundle, keine Größenfilterung

**Kontext:** Vierte der neun noch fehlenden Auftrag-§10-Oberflächen-
seiten: **Peer-Vergleich** (Auftrag §10, Seite 5) — eine eigenständige
Vergleichstabelle über ein ausgewähltes Unternehmen und seine Peers.
`fundamentals/peers.py::find_peers` (Milestone 3) lag bereits vor und
wird bereits in `ui/detail.py`s Bewertungsabschnitt als reine
PE-/EV-EBITDA-Momentaufnahme genutzt (ADR-27) — diese neue Seite geht
darüber hinaus mit einer vollständigen Kennzahlen-Gegenüberstellung.

**Entscheidung — je Zeile ein vollständiger `ReportBundle`, wie
`ui/ranking.py` (ADR-28):** Statt nur `find_peers()` plus einer
schlanken Multiples-Momentaufnahme zu nutzen, baut `ui/peers.py` für
das ausgewählte Unternehmen UND jeden gefundenen Peer den vollständigen
`ReportBundle` und liest Score, Klassifikation, Wachstum, Margen,
Rendite, Verschuldung und Multiples einheitlich aus
`bundle.fundamentals`/`bundle.valuation`/`bundle.score`. Damit gilt
dieselbe strukturelle Garantie wie zwischen Detailseite, Rangliste und
Exporten (ADR-21/27/28): der für das ausgewählte Unternehmen gezeigte
Score/die Margen usw. können auf dieser Seite nicht von den auf der
Unternehmensdetail-Seite gezeigten Werten abweichen.

**Entscheidung — Peers ausschließlich über `find_peers()`, keine
eigene Größenfilterung:** `fundamentals/peers.py` dokumentiert bereits
selbst, dass die Peer-Zuordnung aktuell rein über den SIC-Code läuft,
ohne Größenähnlichkeit (Marktkapitalisierung). Diese UI-Seite fügt
bewusst KEINEN eigenen Filter (z. B. „nur ähnlich große Peers")
hinzu — das wäre eine über die dokumentierte Fähigkeit von
`find_peers()` hinausgehende, hier still eingeführte Zusatzlogik. Die
bereits in `DECISIONS.md`/`TODO.md` geführte Lücke (Größenfilter für
Peer-Gruppen) bleibt an ihrem angestammten Ort dokumentiert, nicht
durch eine UI-Sonderlösung umgangen.

**Entscheidung — kein SIC-Code / keine Peers sind unterschiedliche,
beide ehrliche Zustände:** Zwei Fälle werden bewusst unterschiedlich
kommuniziert, statt beide unter einer generischen „keine Ergebnisse"-
Meldung zu verstecken: (a) das ausgewählte Unternehmen hat noch keinen
SIC-Code (wird erst beim SEC-EDGAR-Abruf über den Marktscreener
automatisch gesetzt, siehe ADR-26) — hier ist ein Peer-Vergleich
grundsätzlich nicht möglich; (b) das Unternehmen hat einen SIC-Code,
aber es gibt (noch) kein anderes erfasstes Unternehmen mit demselben
Code — hier fehlt nur die Datenbasis, nicht die Klassifikation. Beide
Meldungen erklären zusätzlich, dass Peers ausschließlich unter bereits
über den Marktscreener erfassten Unternehmen gesucht werden, nicht in
einem größeren Aktienuniversum (dieselbe dokumentierte Grenze wie bei
der Kandidaten-Rangliste, ADR-28).

**Tests:** 5 neue Tests (insgesamt 487) — 2 reine Tests
(`tests/ui/test_peers.py`: `find_peers` filtert korrekt nach SIC-Code,
`_vergleichstabelle()` enthält ausgewähltes Unternehmen und Peer mit
plausiblen Werten), 3 neue `AppTest`-Smoke-Tests
(`tests/ui/test_app_smoke.py`): kein Unternehmen erfasst, Unternehmen
ohne SIC-Code, sowie zwei Unternehmen mit identischem SIC-Code inkl.
Vergleichstabelle. `ruff`/`mypy` fehlerfrei. Zusätzlich mit echtem
Playwright-Browser gegen einen laufenden Streamlit-Prozess mit drei
synthetisch befüllten Unternehmen verifiziert (zwei mit identischem
SIC-Code, eines mit abweichendem) — der Peer mit abweichendem SIC-Code
erscheint korrekt NICHT in der Vergleichstabelle, keine unerwarteten
Konsolenfehler.

## ADR-30: DCF- und Szenarioanalyse — vollständiges DCF-Detail statt nur der Zusammenfassung, Sensitivitätsmatrizen direkt aus dem ReportBundle

**Kontext:** Fünfte der neun noch fehlenden Auftrag-§10-Oberflächen-
seiten: **DCF- und Szenarioanalyse** (Auftrag §10, Seite 6).
`valuation/dcf.py` (Milestone 4) — Zwei-Stufen-DCF-Modell mit
Sensitivitätsmatrix — lag bereits vollständig vor; `ui/detail.py`
(ADR-27) zeigt davon bislang nur eine verdichtete Zusammenfassung
(Fair-Value-Band, eine dreispaltige Szenarientabelle mit je einer
Zeile pro Szenario), keine Sensitivitätsmatrizen und keine
Jahr-für-Jahr-Cashflow-Details.

**Entscheidung — vollständiges DCF-Detail statt Duplikation der
Detailseite:** Diese neue Seite zeigt, was `ui/detail.py` bewusst NICHT
zeigt: je Szenario alle Annahmen (Umsatzwachstum, FCF-Marge, WACC,
Terminalwachstum, Projektionshorizont) UND die Jahr-für-Jahr-Tabelle
(projizierter FCF, diskontierter FCF je Jahr) UND
Terminalwert/Unternehmenswert/Eigenkapitalwert/fairer Wert je Aktie,
sowie beide Sensitivitätsmatrizen (Umsatzwachstum×WACC,
FCF-Marge×Terminalwachstum). Keine Dopplung der bereits auf der
Detailseite gezeigten verdichteten Zusammenfassung — beide Seiten
ergänzen sich, ohne denselben Inhalt zweimal in unterschiedlicher
Tiefe zu pflegen.

**Entscheidung — Sensitivitätsmatrizen direkt aus `ValuationReport`,
keine eigene Neuberechnung:** `build_valuation_report()` (Milestone 4)
berechnet die beiden Sensitivitätsmatrizen bereits als Teil des
regulären `ValuationReport` — mit denselben Standard-Variationsbereichen
(±2 Prozentpunkte Wachstum/Marge in 1-Punkt-Schritten, ±1 Prozentpunkt
WACC/Terminalwachstum in 0,5-Punkt-Schritten um die Basisannahme). Statt
diese Matrizen mit eigenen, in der UI frei wählbaren Bereichen neu zu
berechnen (was eine zweite, potenziell abweichende Berechnungslogik
bedeutet hätte), liest `ui/dcf.py` sie unverändert aus
`bundle.valuation.sensitivity_growth_wacc`/
`sensitivity_margin_terminal_growth` — dieselbe strukturelle Garantie
wie bei allen anderen neuen Seiten (ADR-27/28/29): keine zweite
Berechnung, nur Darstellung. Eine interaktive „eigene Annahmen
eingeben"-Funktion wurde deshalb bewusst NICHT gebaut — das wäre eine
neue, hier nicht vorgesehene Berechnungsfunktion (Auftrag §11) und ist
als möglicher künftiger Ausbauschritt in `NEXT_STEPS.md` vermerkt.

**Entscheidung — fehlende Zellen als „—", nie als 0:** `run_dcf()`
liefert `None` bei rechnerisch unzulässigen Annahmenkombinationen
(WACC ≤ Terminalwachstum oder WACC ≤ 0) — `build_sensitivity_matrix()`
übernimmt das unverändert als `None`-Zelle. `ui/dcf.py` zeigt solche
Zellen als leer/„—" in der Tabelle, mit einer erklärenden Caption unter
jeder Matrix, statt sie als 0 oder eine sonstige Zahl darzustellen
(Auftrag §11).

**Tests:** 7 neue Tests (insgesamt 494) — 5 reine Tests
(`tests/ui/test_dcf.py`: `_pct()`/`_zahl()`-Formatierung inkl.
`None`-Behandlung, `_sensitivitaetstabelle()` mit korrekten Zeilen-/
Spaltenbeschriftungen und korrekter `None`-Behandlung bei unzulässigen
Annahmen), 2 neue `AppTest`-Smoke-Tests (`tests/ui/test_app_smoke.py`):
kein Unternehmen erfasst, sowie ein vollständiger Durchlauf mit
synthetisch befüllter Testdatenbank (alle drei Szenario-Expander,
beide Sensitivitätsmatrizen). `ruff`/`mypy` fehlerfrei. Zusätzlich mit
echtem Playwright-Browser gegen einen laufenden Streamlit-Prozess mit
synthetisch befüllter Testdatenbank verifiziert: Basis-Szenario
aufgeklappt mit korrekter Jahr-für-Jahr-Tabelle, Optimistisch/
Pessimistisch als eingeklappte Expander mit korrekten Fair-Value-Werten
(identisch zu den auf der Detailseite gezeigten Werten), beide
Sensitivitätsmatrizen mit plausibel monotonen Werten, keine
unerwarteten Konsolenfehler.

## ADR-31: Nachrichten/Ereignisse — reine Anzeigeseite, offene Ehrlichkeit über fehlenden Abrufweg

**Kontext:** Sechste der neun noch fehlenden Auftrag-§10-Oberflächen-
seiten: **Nachrichten/Ereignisse** (Auftrag §10, Seite 7).
`news/report.py::build_news_report` (Milestone 5) — liest gespeicherte
`NewsItem`-Zeilen und clustert sie nach Ereignistyp — lag bereits
vollständig vor; `ui/detail.py` (ADR-27) zeigt davon bislang nur eine
verdichtete Tabelle je Cluster ohne Mehrquellen-Kennzeichnung.

**Entscheidung — `bundle.news` statt `build_news_report` direkt:**
Wie alle bisherigen neuen Seiten (ADR-27/28/29/30) liest `ui/news.py`
ausschließlich `bundle.news` aus dem bereits vorhandenen
`ReportBundle` (`build_report_bundle` ruft `build_news_report` intern
auf) — keine eigene, potenziell abweichende zweite Berechnung.

**Entscheidung — Mehrquellenbestätigung sichtbar machen (Auftrag
§3):** Jeder Cluster-Titel zeigt explizit, ob er von mehreren
unabhängigen Domains bestätigt wird (`NewsCluster.is_multi_source`)
oder nur aus einer einzelnen Quelle stammt — „nur eine Quelle — noch
nicht unabhängig bestätigt" statt einer neutralen Formulierung, die
diesen für Auftrag §3 („mindestens zwei unabhängige Quellen für
kritische Angaben") relevanten Unterschied verschleiern würde. Zusätzlich
früheste/jüngste Meldung je Cluster und die Anzahl unabhängiger Domains.

**Entscheidung — Quelle als klickbarer Link:** Die Cluster-Tabelle
nutzt `st.column_config.LinkColumn` für die Quell-URL — Nutzer können
die Originalmeldung direkt öffnen, statt nur einen Domainnamen ohne
Beleg zu sehen (Auftrag §11: jede Aussage muss auf ein Quellenobjekt
zurückführbar sein).

**Entscheidung — offene Kommunikation der fehlenden automatischen
Abrufkette:** Anders als beim Marktscreener (SEC EDGAR/Alpha Vantage,
ADR-26) ist der Abruf über die GDELT-/IR-RSS-Connectoren in KEINER
Oberflächenseite eingebunden — `NewsItem`-Zeilen gelangen aktuell nur
über eigene Skripte/Tests in die Datenbank. Diese neue Seite verschweigt
das nicht: Modul-Docstring UND die im Nutzerkontext leere-Zustand-
Meldung nennen den fehlenden Abrufweg explizit, statt eine
funktionierende, aber in der Praxis leere Seite ohne Erklärung zu
zeigen (Auftrag §16). Als offener Ausbauschritt weiterhin in
`NEXT_STEPS.md` geführt — Priorität niedriger als die verbleibenden
UI-Seiten, da er einen neuen Ingestion-Pfad statt nur eine Anzeige
erfordert.

**Tests:** 3 neue Tests (insgesamt 497) — 1 reiner Test
(`tests/ui/test_news.py`: `_cluster_tabelle()` enthält alle Meldungen
inkl. Quelle, über den bestehenden `ingest_gdelt_articles`-Testpfad aus
`tests/news/test_report.py` befüllt), 2 neue `AppTest`-Smoke-Tests
(`tests/ui/test_app_smoke.py`): keine gespeicherten Meldungen, sowie
ein mehrquellenbestätigter Cluster mit zwei GDELT-Artikeln
unterschiedlicher Domains. `ruff`/`mypy` fehlerfrei. Zusätzlich mit
echtem Playwright-Browser gegen einen laufenden Streamlit-Prozess mit
drei synthetisch befüllten Meldungen verifiziert (zwei ähnliche Titel
von unterschiedlichen Domains → korrekt als ein mehrquellenbestätigter
Cluster erkannt, eine dritte, thematisch andere Meldung → korrekt als
eigener Einzelquellen-Cluster; aufgeklappter Cluster zeigt Tabelle mit
klickbarem Quell-Link) — keine unerwarteten Konsolenfehler.

## Noch zu treffende Entscheidungen

Keine blockierenden Entscheidungen mehr offen für Milestone 1–7 (alle
abgeschlossen, siehe `PROGRESS.md`). Verbleibende Detailfragen aus
`MILESTONE_0.md` Abschnitt B (z. B. weitere Feinjustierung der
Mindestmarktkapitalisierung) bleiben über den Ersteinrichtungsdialog im
laufenden Betrieb änderbar (Auftrag §2). Weiterhin offen: Priorisierung
der EU/DE-Meldungsquellen-Lücke (ADR-9), Auflösung der
Notierungswährung für Alpha-Vantage-Kurse (jetzt zusätzlich relevant für
die Portfolio-Konzentrationsanalyse, ADR-20, und für Backtest-
Währungsumrechnung, ADR-22), unternehmensspezifische CAPM-Herleitung
des WACC statt des groben Standardwerts, ob die Peer-Gruppen-Zuordnung
um einen Größenfilter ergänzt werden soll, wie die Zuordnung
„IR-RSS-Feed-URL ↔ Entity" gepflegt werden soll, sowie — neu aus
Milestone 7 — ob/wie eine Benchmark-/Index-Kursquelle künftig
angebunden werden soll (siehe `TODO.md`).
