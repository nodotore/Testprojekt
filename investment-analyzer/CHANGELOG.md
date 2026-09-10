# Changelog — Investment-Analysator

## Unreleased

- Backtest (Auftrag §10, Seite 9) umgesetzt — neunte von neun
  ursprünglich noch fehlenden Oberflächenseiten (siehe ADR-33); nur
  noch „Einstellungen, Quellen und Prüfprotokoll" (Seite 10) offen.
  Neue Seite `ui/backtest.py`: Zeitraum/Rebalancing-Intervall/Top-N-
  Auswahl baut die vom Backend erwartete Stichtagsliste, vollständige
  Kennzahlen-Anzeige (Gesamtrendite, CAGR, Volatilität, Sharpe/
  Sortino, maximaler Drawdown, Turnover, Benchmark-Vergleich),
  NAV-Verlaufsdiagramm, Rebalancing-Perioden-Tabelle mit
  Unternehmensnamen. Backend-Lücken-Schlüssel werden in verständliche
  Sätze übersetzt statt als rohe Bezeichner gezeigt. Aus ADR-32 direkt
  angewendete Lehre: Prozentwerte von Anfang an korrekt skaliert. 6
  neue Tests (insgesamt 510), `ruff`/`mypy` fehlerfrei, zusätzlich mit
  echtem Browser verifiziert (inkl. Lösung der react-aria-DateField-
  Interaktion für Playwright).

- Watchlist/Portfolio (Auftrag §10, Seite 8) umgesetzt — achte von
  neun noch fehlenden Oberflächenseiten (siehe ADR-32). Neue Seite
  `ui/watchlist.py`: zwei Tabs (Watchlist/Portfolio) mit CSV-Import und
  vollständigem `PortfolioReport`-Rendering (Positionen, Branchen-/
  Länderkonzentration, Währungsexposure, Positionsgrößen-Bandbreite,
  Drawdown, Korrelation, offene Lücken). Beim Live-Test einen echten
  Prozent-Skalierungsfehler gefunden und behoben: Bruchzahlen aus dem
  Backend (Konzentrationsanteile, `max_drawdown_pct`) wurden
  ungeskaliert mit `%.1f%%` formatiert, sodass 66,7 % als „0.7%"
  erschien — jetzt mit expliziter ×100-Skalierung und
  Regressionstests. 7 neue Tests (insgesamt 504), `ruff`/`mypy`
  fehlerfrei, zusätzlich mit echtem Browser gegen zwei Portfolio-
  Positionen verifiziert.

- Nachrichten/Ereignisse (Auftrag §10, Seite 7) umgesetzt — sechste
  von neun noch fehlenden Oberflächenseiten (siehe ADR-31). Neue Seite
  `ui/news.py`: aufklappbare Ereignis-Cluster mit sichtbarer
  Mehrquellenbestätigung (Auftrag §3: mehrere unabhängige Domains vs.
  nur eine Quelle), frühester/jüngster Meldung je Cluster und
  klickbaren Links zur Originalquelle — liest `bundle.news` aus dem
  bereits vorhandenen `ReportBundle`, keine eigene Berechnung. Offen
  und ehrlich kommuniziert: ein automatischer Abrufweg über GDELT/
  IR-RSS ist bislang in keiner Oberflächenseite eingebunden. 3 neue
  Tests (insgesamt 497), `ruff`/`mypy` fehlerfrei, zusätzlich mit
  echtem Browser gegen synthetisch befüllte GDELT-Meldungen
  verifiziert.

- DCF- und Szenarioanalyse (Auftrag §10, Seite 6) umgesetzt — fünfte
  von neun noch fehlenden Oberflächenseiten (siehe ADR-30). Neue Seite
  `ui/dcf.py`: vollständiges DCF-Detail je Szenario (Annahmen,
  Jahr-für-Jahr-Cashflow-Tabelle, Terminalwert/Unternehmenswert/
  Eigenkapitalwert/fairer Wert je Aktie) sowie beide
  Sensitivitätsmatrizen (Umsatzwachstum×WACC, FCF-Marge×
  Terminalwachstum) — liest die Matrizen unverändert aus dem bereits
  vorhandenen `ValuationReport`, keine eigene Neuberechnung. Ergänzt
  die verdichtete Zusammenfassung auf der Unternehmensdetail-Seite,
  ohne sie zu duplizieren. Rechnerisch unzulässige Zellen erscheinen
  als leer, nie als 0. 7 neue Tests (insgesamt 494), `ruff`/`mypy`
  fehlerfrei, zusätzlich mit echtem Browser gegen eine synthetisch
  befüllte Testdatenbank verifiziert.

- Peer-Vergleich (Auftrag §10, Seite 5) umgesetzt — vierte von neun
  noch fehlenden Oberflächenseiten (siehe ADR-29). Neue Seite
  `ui/peers.py`: Vergleichstabelle für ein ausgewähltes Unternehmen und
  seine über `fundamentals/peers.py::find_peers` (identischer SIC-Code)
  gefundenen Peers, baut je Zeile den vollständigen `ReportBundle` (wie
  die Kandidaten-Rangliste) statt nur eine schlanke
  Multiples-Momentaufnahme zu nutzen — Score, Klassifikation, Wachstum,
  Margen, Rendite, Verschuldung und Multiples zeigen garantiert
  dieselben Werte wie auf der Unternehmensdetail-Seite. Unterscheidet
  klar zwischen „kein SIC-Code" und „SIC-Code vorhanden, aber keine
  anderen erfassten Peers". 5 neue Tests (insgesamt 487), `ruff`/`mypy`
  fehlerfrei, zusätzlich mit echtem Browser gegen drei synthetisch
  befüllte Unternehmen verifiziert.

- Kandidaten-Rangliste (Auftrag §10, Seite 3) umgesetzt — dritte von
  neun noch fehlenden Oberflächenseiten (siehe ADR-28). Neue Seite
  `ui/ranking.py`: sortierbare Tabelle aller bereits erfassten
  Unternehmen nach Gesamtscore, baut je Zeile den vollständigen
  `ReportBundle` (wie die Detailseite) statt nur `score_entity()`
  direkt aufzurufen, damit Score/Datenabdeckung/Klassifikation
  garantiert dieselben Werte zeigen wie auf der Unternehmensdetail-
  Seite und in den Exporten. Rankt bewusst nur bereits erfasste
  Unternehmen (keine Breitensuche über ein größeres Universum, noch
  nicht vorhanden). Warnung bei Unternehmen mit Klassifikation
  „Datenlage unzureichend". 4 neue Tests (insgesamt 482), `ruff`/`mypy`
  fehlerfrei, zusätzlich mit echtem Browser gegen eine synthetisch
  befüllte Testdatenbank mit drei Unternehmen verifiziert.

- Unternehmensdetail mit Quellenleiste (Auftrag §10, Seite 4) umgesetzt
  — zweite von neun noch fehlenden Oberflächenseiten (siehe ADR-27).
  Neue Seite `ui/detail.py` rendert ausschließlich aus demselben
  `ReportBundle`/`report_bundle_to_dict()`-Dict wie die Excel-/PDF-/
  JSON-Exporte (ADR-21) — Kopfzeile mit Datenstand/Analysezeit/
  Marktdatenverzögerung/Datenabdeckung/Konfidenz, Kennzahlen, Bewertung
  inkl. DCF-Szenarien/Peer-Vergleich, Score inkl. Risikoabzügen/
  Gegenargumenten/Ungültigkeitsbedingungen, Nachrichten-Cluster,
  Quellenleiste mit Lizenzhinweis je Quelle, Annahmen, sowie JSON-/
  Excel-/PDF-Download-Buttons aus demselben Bericht. Damit gilt
  Auftrag-§15-Kriterium 8 („Exporte = Oberflächenwerte") jetzt als
  strukturell und durch eine echte UI-Seite erfüllt (siehe `ABNAHME.md`).
  7 neue Tests (insgesamt 478), `ruff`/`mypy` fehlerfrei, zusätzlich mit
  echtem Browser gegen einen laufenden Streamlit-Prozess mit
  synthetisch befüllter Testdatenbank verifiziert.

- Marktscreener (Auftrag §10, Seite 2) umgesetzt — erste von neun noch
  fehlenden Oberflächenseiten nach Abschluss des ursprünglichen
  Milestone-0–8-Plans (siehe ADR-26). Neues Modul `ingestion/
  pipeline.py`: Ticker/CIK → Entity finden/anlegen → alle bekannten
  XBRL-Kennzahlen abrufen und speichern, mehrere mögliche XBRL-Tags je
  Kennzahl werden der Reihe nach versucht, ein von diesem Unternehmen
  nicht gemeldeter Tag (HTTP 404) gilt nicht als Fehlschlag der
  gesamten Ingestion. Neues Profilfeld `sec_edgar_kontakt_email`
  (SEC-Pflichtangabe, bewusst nicht automatisch aus dem Nutzerkonto
  übernommen). `SecretStore` erstmals in `AppContext` verfügbar (nur
  OS-Keyring). Neue Seite `ui/screener.py` mit Formular, Fehler-
  behandlung, Audit-Log-Anbindung und einer durchsuchbaren Liste
  bereits erfasster Unternehmen; einfache Sidebar-Navigation in
  `app.py`. 20 neue Tests (insgesamt 471), `ruff`/`mypy` fehlerfrei,
  zusätzlich mit echtem Browser gegen einen laufenden Streamlit-Prozess
  verifiziert.

- Fix: `alembic/env.py` rief `AppSettings.ensure_data_dirs()` nicht auf,
  bevor die SQLite-Verbindung für die Migration aufgebaut wurde. Beim
  allerersten Start auf einem frischen Rechner existiert
  `%USERPROFILE%\InvestmentAnalyzer` noch nicht — `start.ps1` ruft die
  Migration jedoch VOR dem Start der Oberfläche auf (die einzige Stelle,
  die das Verzeichnis bisher anlegte, war `ui/bootstrap.py`). Ergebnis:
  `sqlite3.OperationalError: unable to open database file` bei jedem
  echten Erststart (in freier Wildbahn auf einem realen Windows-Rechner
  gefunden — die bestehende Test-Suite prüfte die Migration bislang nur
  gegen ein bereits existierendes `tmp_path`-Verzeichnis, nie gegen ein
  wirklich neues). Behoben: `ensure_data_dirs()` wird jetzt in
  `alembic/env.py` vor dem Verbindungsaufbau aufgerufen; bestehender
  Migrationstest um ein verschachteltes, noch nicht existierendes
  Verzeichnis erweitert, damit dieses Szenario künftig abgedeckt ist.
  Verifiziert mit komplett frischem venv + frischem Datenverzeichnis
  end-to-end (Migration + Streamlit-Oberfläche). 453 Tests grün.

- Fix: `pyproject.toml`s `numpy<2.1`-Obergrenze entfernt. Erste reale
  Windows-Installation nach Milestone 8 schlug fehl
  (`metadata-generation-failed` beim Bauen von `numpy` aus dem
  Quellcode, da auf dem Zielrechner kein C-Compiler installiert ist und
  für den dortigen Python-Stand kein vorgefertigtes Wheel innerhalb der
  alten `numpy`-Version existierte). `numpy` wird im Code nirgends
  direkt verwendet (nur transitiv über `pandas`), die Obergrenze war
  eine willkürliche, nicht dokumentierte Absicherung aus Milestone 1.
  Mit einer frischen Installation (`numpy` 2.5.3, `pandas` 3.0.5, die
  aktuell neuesten Versionen) verifiziert: 453 Tests grün, `ruff`/
  `mypy` fehlerfrei.

- Milestone 8 (Sicherheit und Abnahme) abgeschlossen — unabhängiger
  Security-/Plausibilitätscheck (ADR-25): ein separater Agentenlauf
  ohne Kenntnis der Implementierungsentscheidungen fand einen echten,
  für Auftrag §15 blockierenden Look-ahead-Bias in
  `risk/warning_signals.py` (Warnsignal-Checks nutzten den aktuellen
  statt den Analysestichtag-Zeitpunkt, floss über `total_score` in die
  Backtest-Kandidatenauswahl ein) — noch in dieser Runde behoben und
  mit zwei neuen Regressionstests abgesichert. Zwei weitere Härtungen:
  Downloadgrößen-Prüfung jetzt per Streaming statt erst nach
  vollständiger Pufferung; HTML-Sanitizing-Fallback lässt kein rohes
  Markup mehr durch. Eine SSRF-Time-of-check-to-time-of-use-Restlücke
  bewusst nicht behoben, aber ehrlich dokumentiert (`SECURITY.md`
  entsprechend korrigiert). Ehrliche Abnahme-Checkliste gegen alle
  neun Auftrag-§15-Kriterien: `ABNAHME.md` (6/9 vollständig erfüllt,
  1/9 teilweise, 2/9 strukturell fundiert aber noch nicht empirisch
  nachweisbar — v. a. mangels Internetzugang in dieser Sandbox und
  fehlender UI-Detailseite, beides seit früheren Milestones
  dokumentiert). 3 neue Tests (insgesamt 453), `ruff`/`mypy` fehlerfrei.

- Milestone 8 (Sicherheit und Abnahme, in Bearbeitung) — Windows-Setup
  vervollständigt + `BENUTZERHANDBUCH.md`: `start.ps1` sichert die
  Datenbank jetzt automatisch vor jeder Migration (`db/backup.py` aus
  dem Ausfalltest-Schritt erstmals in den echten Nutzerablauf
  eingebunden, überspringbar mit `-NoBackup`, best-effort); neue
  Endnutzer-Skripte `scripts/backup-database.ps1`/
  `scripts/restore-database.ps1` und CLI-Werkzeug `db/backup_cli.py`.
  Neues `BENUTZERHANDBUCH.md` (Installation, Datenschutz/Sicherheit,
  Datensicherung, Fehlerbehebung) mit einem bewusst ehrlichen
  Abschnitt zum aktuellen UI-Stand: nur die Start-/Datenstatus-Seite
  ist als Bildschirmseite gebaut, der vollständige Analysemotor
  dahinter ist implementiert/getestet, aber noch nicht über die
  Oberfläche bedienbar. Kein nativer Windows-Installer (.exe/.msi) —
  als bewusste, dokumentierte Einschränkung festgehalten. `README.md`
  aktualisiert (Projektstand, Datensicherung). 5 neue Tests (insgesamt
  450), `ruff`/`mypy` fehlerfrei.

- Milestone 8 (Sicherheit und Abnahme, in Bearbeitung) — Ausfalltests
  (ADR-24): echte Sicherheitslücke gefunden und behoben —
  `connectors/ir_rss.py` parste externe RSS-/Atom-Feeds über die
  ungehärtete Stdlib `xml.etree.ElementTree` (anfällig für „Billion
  Laughs"-Entity-Expansion, von der HTTP-Größenobergrenze NICHT
  abgedeckt); jetzt `defusedxml` (neue Abhängigkeit). Zwei Ausfalltests
  bestätigen bereits bestehende Mechanismen end-to-end (kein Fund):
  Prompt-Injection-Versuch in News-Inhalten bleibt reine Nutzdaten,
  widersprüchliche/extreme Testdaten lösen sichtbar das Warnsignal-
  System aus statt einer stillen Fehlkalkulation. Neuer Baustein:
  `db/backup.py` (Sicherung/Wiederherstellung der lokalen SQLite-
  Datenbankdatei), end-to-end getestet (Sicherung → simulierter
  Datenverlust → Wiederherstellung → Daten vollständig da). Rate-
  Limit-Überschreitung je Connector bereits durch bestehenden
  gemeinsamen Test abgedeckt. Eine echte Datenlücke dokumentiert statt
  verschwiegen: Auftrag-§3-„bei Widerspruch beide Werte zeigen" ist mit
  dem aktuellen Kostenlos-Quellen-Set strukturell nicht auftretbar. 10
  neue Tests (insgesamt 445), `ruff`/`mypy` fehlerfrei.

- Milestone 8 (Sicherheit und Abnahme, in Bearbeitung) — Security-Review
  abgeschlossen (ADR-23): systematischer Abgleich jeder `SECURITY.md`-
  Behauptung mit dem tatsächlichen Codeverhalten. Drei echte Lücken
  gefunden und behoben — Downloadgrößen-Begrenzung je Connector
  (`ConnectorConfig.max_response_bytes`, kein Retry/Cache bei
  Überschreitung), unvollständige Log-Redaction (`RedactingFilter`
  bereinigt jetzt auch `record.args`, nicht nur `record.msg`),
  fehlender Auftrag-§12-Pflichthinweis in den Berichtsexporten
  (`reports/bundle.py::MANDATORY_DISCLAIMER`, jetzt in JSON-/Excel-/
  PDF-Export sichtbar, zuvor nur in der UI). Ein Dokumentationsfehler
  korrigiert (Redirect-Verhalten von `httpx.Client`, tatsächlich
  strenger als dokumentiert). `pip-audit`: keine bekannten
  Schwachstellen. 10 neue Tests (insgesamt 435), `ruff`/`mypy`
  fehlerfrei. Ausfalltests, Windows-Setup-Härtung, Benutzerhandbuch und
  die finale Auftrag-§15-Abnahme-Checkliste stehen noch aus.

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
