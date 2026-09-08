# Changelog — Investment-Analysator

## Unreleased

- Milestone 7 (Backtesting) umgesetzt: Point-in-time-Universum
  (`backtesting/universe.py`, ADR-22 — eine Entity gilt als „zum
  Stichtag bekannt", wenn mindestens ein `DataPoint` mit
  `retrieved_at_utc <= as_of` existiert), Perioden-Rendite inkl.
  geschätzter Dividende je Aktie und Transaktionskosten
  (`period_return.py`), Train-/Validierungs-/Out-of-Sample-Split
  (`splits.py`), Kennzahlen CAGR/Volatilität/Sharpe/Sortino/Turnover
  (`metrics.py`, Max-Drawdown aus Milestone 6 wiederverwendet),
  deterministische Top-N-Auswahlstrategie auf Basis des bereits
  bestehenden, festen Scoring-Systems ohne auf den Backtest-Zeitraum
  gefitteten Parameter (`strategy.py`), Rebalancing-Engine
  (`engine.py`) und `BacktestReport`-Orchestrierung (`report.py`) mit
  vollständiger Lücken-Dokumentation. Abnahmekriterium „kein
  Look-ahead" zweistufig nachgewiesen (Universums-Ebene und
  vollständiger Backtest-Lauf: Auswahl und Portfoliorendite
  bit-identisch vor/nach dem Eintreffen später bekannt gewordener
  Kandidaten). 61 neue Tests (insgesamt 425), `ruff`/`mypy` fehlerfrei.
  Bewusste, dokumentierte Lücken: kein Benchmark-/Index-Kursvergleich
  (keine Datenquelle im Kostenlos-Paket), keine Währungsumrechnung,
  unvollständiges Survivorship-Universum (siehe PROGRESS.md/ADR-22).

- Milestone 6 (Portfolio und Exporte) umgesetzt: neues Modul
  `portfolio/` (ADR-20) mit Watchlist-/Portfolio-CSV-Import
  (zeilengenaue Fehlersammlung, idempotent, dieselbe Entity-Auflösung
  wie jede andere Ingestion), Branchen-/Länder-/Währungs-
  Konzentrationsanalyse nach Marktwert (liefert `computable=False`
  statt Fantasiewert bei gemischten Bestandswährungen; „Faktor-
  Konzentration" explizit als nicht berechenbar dokumentiert),
  unverbindliche Positionsgrößen-Bandbreite, konfigurierbare
  `PortfolioAssumptions` (Transaktionskosten/Steuersatz/
  Mindestliquidität), historischer Max-Drawdown und Pearson-Korrelation
  der Tagesrenditen mit expliziter „Datenlage unzureichend"-Markierung,
  sowie `PortfolioReport`-Orchestrierung. Neues Modul `reports/` mit
  `ReportBundle` (ADR-21) als einziger Quelle der Wahrheit für JSON-,
  Excel- (alle sieben Auftrag-§10-Tabellenblätter: Zusammenfassung,
  Kennzahlen, Bewertung, Risiken, Nachrichten, Quellen, Annahmen) und
  PDF-Export — beide Formate lesen strukturell aus demselben
  `report_bundle_to_dict()`, inkl. Formel-Injection-Schutz für
  Zellwerte aus externen Quellen (Auftrag §12). 60 neue Tests
  (insgesamt 372), `ruff`/`mypy` fehlerfrei. Das Abnahmekriterium
  „Export = UI-Werte" ist strukturell (ADR-21), aber mangels
  existierender Report-UI-Seite noch nicht live nachprüfbar (siehe
  PROGRESS.md).

- Milestone 5 (Nachrichtenanalyse) umgesetzt: Connector-Grundgerüst um
  `get_text()` erweitert (Rohtext statt JSON, für Quellen ohne
  JSON-API), GDELT-DOC-2.0-Connector (`connectors/gdelt.py`,
  Volltextsuche nach Firmenname, kein API-Schlüssel nötig) und
  generischer IR-RSS-Connector (`connectors/ir_rss.py`, RSS-2.0-/
  Atom-Parsing über stdlib `xml.etree`, Host-Allowlist wird pro
  Feed-URL zur Laufzeit gesetzt, SSRF-/DNS-Rebinding-Schutz bleibt
  unabhängig davon aktiv). Neues provenienzbehaftetes `NewsItem`-Modell
  (`news/models.py`, ADR-18) mit Migration, Source-Seeding um
  `gdelt`/`ir_rss` erweitert. HTML-Bereinigung zu reinem Klartext
  (`news/sanitize.py`, Auftrag §12) sowie deterministische,
  regelbasierte Klassifikation von Quellqualität und Ereignistyp
  (`news/classification.py`, ADR-19) — nie durch ein Sprachmodell.
  Idempotente Ingestion mit URL-Normalisierung/Dedup-Hash
  (`news/ingest.py`), rein funktionales Ereignis-Clustering über
  Titel-Ähnlichkeit (`news/clustering.py`, `difflib`, keine Embeddings)
  und `NewsReport`-Orchestrierung (`news/report.py`). 60 neue Tests
  (insgesamt 301), `ruff`/`mypy` fehlerfrei. Die im Auftrag genannte
  KI-Zusammenfassung mit Quellenverweis wird bewusst NICHT umgesetzt
  (keine Claude-API-Anbindung in dieser Umgebung) — Datengrundlage
  dafür ist gelegt, siehe PROGRESS.md. Verifikation der
  Duplikaterkennung an einem realen Testset mangels Internetzugang in
  dieser Sandbox nicht möglich.

- Milestone 4 (Bewertung und Score) umgesetzt: Multiples (KGV,
  EV/EBITDA, EV/EBIT, KBV, KCFV, FCF-Rendite) als reine Funktionen
  (`valuation/multiples.py`), Zwei-Phasen-DCF mit drei Szenarien
  (Basis/optimistisch/pessimistisch) und Sensitivitätsmatrix
  (`valuation/dcf.py`), Valuation-Report-Orchestrierung inkl.
  Peer-Vergleich und expliziter Datenlücken-Dokumentation
  (`valuation/report.py`), Kennzahlen-Vokabular um `PRICE_CLOSE`
  erweitert (ADR-16) mit point-in-time-fähigem Zugriff auf den
  jüngsten Kurswert (`fundamentals/series.py::get_latest_value`), sowie
  deterministisches, erklärbares Scoring nach Auftrag §7
  (`scoring/score.py`): Startgewichtung über sechs aktuell berechenbare
  Komponenten mit Renormierung und sichtbarem `coverage`-
  Konfidenzsignal statt Nullbewertung fehlender Daten (ADR-17),
  sichtbare Risikoabzüge aus den Milestone-3-Warnsignalen,
  Konfidenzschwellen für die Klassifikation, sowie deterministisch
  generierte positive Faktoren/Risiken/Gegenargumente/
  Ungültigkeitsbedingungen ohne verbotene Formulierungen. 59 neue Tests
  (insgesamt 241), davon hand-verifizierte Multiples-/DCF-Fälle (u. a.
  ein exakt nachrechenbarer Fall mit Wachstum = WACC) und
  Scoring-Komponententests auf zwei Ebenen (reine Funktionen +
  End-to-End-Datenbankprüfung); `ruff`/`mypy` fehlerfrei. Verifikation
  an realen Unternehmen weiterhin mangels Internetzugang in dieser
  Sandbox nicht möglich (siehe PROGRESS.md).

- Milestone 3 (Fundamentalanalyse) umgesetzt: kanonisches Kennzahlen-
  Vokabular mit XBRL-Tag-Mapping (`fundamentals/metrics.py`, ADR-14),
  reiner Berechnungskern für Wachstum (1/3/5/10 Jahre), Margen +
  Stabilität, ROE/ROIC, Cashflow-Kennzahlen, Verschuldung, Ausschüttung/
  Verwässerung (`fundamentals/calculations.py`), point-in-time-fähiges
  Zeitreihen-Repository mit metadatenfreier Jahres-/Quartalstrennung
  (`fundamentals/series.py`, ADR-15), SIC-Klassifikation (neue Alembic-
  Migration) und Peer-Gruppen-Zuordnung (`fundamentals/peers.py`),
  sechs zahlenbasierte Warnsignal-Checks mit expliziter Auflistung der
  noch nicht implementierbaren, textbasierten Signale
  (`risk/warning_signals.py`), sowie die Orchestrierung zu einem
  `FundamentalsReport` mit `data_completeness`/`missing_fields`
  (`fundamentals/report.py`). 66 neue Tests (insgesamt 182), davon 33
  Handrechnungs-Tests für den Berechnungskern und vier
  Integrationstests mit drei hand-verifizierten synthetischen
  Beispielunternehmen; `ruff`/`mypy` fehlerfrei. Verifikation an drei
  realen Unternehmen mangels Internetzugang in dieser Sandbox nicht
  möglich (offener Punkt, siehe PROGRESS.md).

- Milestone 2 (Datenbeschaffung) umgesetzt: Connector-Grundgerüst
  (Timeout, exponentieller Retry-Backoff, injizierbarer Rate-Limiter,
  dateibasierter TTL-Cache ohne stillen Stale-Fallback, SSRF-Schutz mit
  Host-Allowlist + DNS-Rebinding-Prüfung, Trennung von `params`/
  `secret_params` damit API-Schlüssel nie in Provenienz-URL/Cache/Logs
  landen, ADR-13), SEC-EDGAR-Connector (Ticker→CIK, Submissions,
  XBRL Company Concept), Alpha-Vantage-Connector (GLOBAL_QUOTE, inkl.
  Erkennung der Alpha-Vantage-Eigenheit „Rate-Limit als HTTP 200"),
  idempotentes Source-Seeding, Entity-Resolution-Service (lehnt Ticker
  allein als Identität ab, Auftrag §5), Ingestion-Schicht
  (Connector-Ergebnisse → provenienzbehaftete, idempotente,
  Restatement-fähige `DataPoint`-Zeilen). 66 neue Tests (insgesamt 116),
  `ruff`/`mypy` fehlerfrei. Live-Verifikation mit realen Daten in dieser
  Sandbox mangels Internetzugang nicht möglich (Egress-Policy blockiert
  SEC EDGAR/Alpha Vantage) — als offener Punkt dokumentiert.

- Milestone 1 (Grundgerüst) umgesetzt: Python-3.12-Projektgerüst
  (`pyproject.toml`, venv), Paketstruktur gemäß ADR-3/ADR-11
  (`connectors, normalization, entity_resolution, fundamentals,
  valuation, news, risk, scoring, backtesting, reports, ui, audit,
  config, db`), Konfigurationssystem für das Nutzerprofil (Auftrag §2),
  SecretStore mit OS-Keyring- und verschlüsseltem Datei-Fallback (ADR-5),
  provenienzbehaftetes Datenbankschema (`Entity`, `EntityIdentifier`,
  `Source`, `DataPoint`, `AuditLogEntry`, ADR-6) mit erster
  Alembic-Migration (gegen SQLite verifiziert, Up-/Downgrade),
  Logging- und Audit-Log-Grundgerüst inkl. Secret-Redaction in Logs,
  Streamlit-Oberfläche „Start/Datenstatus" mit Ersteinrichtungsdialog
  (ADR-12; zeigt ausschließlich echte, aus der DB gelesene Zahlen statt
  Platzhaltern), Windows-Startskripte (`start.ps1`/`start.bat`,
  `scripts/run-tests.ps1`) sowie `README.md`. 50 automatisierte Tests
  grün, `ruff`/`mypy` fehlerfrei.

- Nutzer hat die vier blockierenden Milestone-0-Fragen beantwortet
  (Projektstruktur = Unterverzeichnis bestätigt, Kostenvariante =
  Kostenlos, Prioritätsmärkte = breit/USA+DE+EU+global offen,
  Deployment = lokal Windows + SQLite). Festgehalten als ADR-7–ADR-10 in
  `DECISIONS.md`; Connector-Reihenfolge für Milestone 2 (SEC EDGAR +
  Alpha Vantage Free) in `PLAN.md`/`DATA_SOURCES.md` konkretisiert.

- Milestone 0 (Klärung und Datenlizenzen) umgesetzt: Projektauftrag
  vollständig referenziert (`AUFTRAG.md`), Fragenliste (`MILESTONE_0.md`),
  Quellen-/Lizenzmatrix mit drei Kostenvarianten (`DATA_SOURCES.md`),
  Architekturentscheidungen ADR-1–ADR-6 (`DECISIONS.md`), verbindlicher
  Implementierungsplan Milestone 0–8 (`PLAN.md`), Methodik-Planungsstand
  (`METHODOLOGY.md`), Sicherheitsrichtlinie-Planungsstand (`SECURITY.md`),
  Leitplanken für künftige Sessions (`CLAUDE.md`). Projekt als eigenes
  Unterverzeichnis `investment-analyzer/` angelegt, um bestehende
  Projektdokumentation im Repo-Root (CD Musikfinder, UC-001) nicht zu
  überschreiben. Noch keine Produktivimplementierung — Milestone 1
  wartet auf Nutzer-Freigabe.
