# TODO — Investment-Analysator

## Milestone 0

- [x] Auftrag vollständig gelesen und als `AUFTRAG.md` referenziert
- [x] Fragenliste erstellt (`MILESTONE_0.md`)
- [x] Quellen-/Lizenzmatrix + Kostenvarianten erstellt (`DATA_SOURCES.md`)
- [x] Architekturentscheidung dokumentiert (`DECISIONS.md`)
- [x] Verbindlicher Implementierungsplan erstellt (`PLAN.md`)
- [x] Methodik-Planungsstand dokumentiert (`METHODOLOGY.md`)
- [x] Sicherheitsrichtlinie-Planungsstand dokumentiert (`SECURITY.md`)
- [x] Nutzer beantwortet die blockierenden Fragen A1–A4 in
      `MILESTONE_0.md` (2026-09-07)
- [ ] Nutzer gibt Milestone 1 ausdrücklich frei

## Milestone 1 — Grundgerüst (abgeschlossen)

- [x] `pyproject.toml` + Tooling-Setup (ruff, mypy, pytest)
- [x] Paketstruktur gemäß ADR-3/ADR-11 anlegen
- [x] Konfigurationssystem für Nutzerprofil (Auftrag §2)
- [x] SecretStore (Keyring + verschlüsselte Datei)
- [x] Datenbankschema + Alembic-Migrationen (gegen SQLite getestet)
- [x] Logging + Audit-Log-Grundgerüst
- [x] Streamlit-Startseite + Ersteinrichtungsdialog
- [x] Windows-Startskripte (`start.ps1`/`start.bat`)
- [x] Grundgerüst-Tests (50 Tests grün, ruff+mypy fehlerfrei)
- [ ] PostgreSQL-Migrationspfad gegen echte Instanz testen (nachholen,
      sobald verfügbar — siehe `PROGRESS.md` „Offene Risiken")
- [ ] Streamlit-Oberfläche in echtem Browser bedienen (Sandbox hatte nur
      Headless-/HTTP-Verifikation)

## Milestone 2 — Datenbeschaffung (Implementierung abgeschlossen)

- [x] Connector-Basisklasse (Timeout, Retry+Backoff, Rate Limiting,
      Cache, Validierung, Fehlerprotokoll, Lizenzhinweis)
- [x] SSRF-Schutz + URL-Allowlist je Connector (inkl. DNS-Rebinding-Prüfung)
- [x] Connector A: SEC EDGAR (Meldungen, USA — Submissions + XBRL Company Concept)
- [x] Connector B: Alpha Vantage Free (Marktdaten — GLOBAL_QUOTE)
- [x] Entity Resolution (Ticker/ISIN/LEI/CIK → interne Entity-ID),
      Ticker allein wird abgelehnt
- [x] Source-Seeding (idempotent)
- [x] Ingestion: Connector-Ergebnisse → provenienzbehaftete DataPoints
      (idempotent, append-only/Restatement-fähig)
- [x] Tests: Cache, Rate-Limit-Einhaltung, simulierter Quellenausfall
      (66 neue Tests, insgesamt 116 grün, ruff+mypy fehlerfrei)
- [ ] **Offen:** Live-Verifikation mit mind. 10 realen Unternehmen gegen
      die echten APIs — in dieser Sandbox durch Egress-Policy blockiert
      (siehe `PROGRESS.md`). Nachholen in Umgebung mit Internetzugang;
      für Alpha Vantage zusätzlich echten API-Schlüssel vom Nutzer nötig
      (siehe `NEXT_STEPS.md`).
- [ ] Notierungswährung für Alpha-Vantage-Kurse auflösen (aktuell
      bewusst `None`, siehe ADR/`normalization/ingest.py`) — vorgesehen
      für Milestone 3 zusammen mit Börsen-/Währungs-Normalisierung.
- [ ] EU/DE-Meldungsquellen-Lücke (ADR-9): ggf. in späterer Milestone
      schließen, falls Nutzer das priorisiert.

## Milestone 3 — Fundamentalanalyse (Implementierung abgeschlossen)

- [x] Kennzahlen-Vokabular + XBRL-Tag-Mapping (`fundamentals/metrics.py`)
- [x] Berechnungskern: Wachstum, Margen+Stabilität, ROE/ROIC, Cashflow-
      Kennzahlen, Verschuldung, Ausschüttung/Verwässerung
- [x] Point-in-time-Zeitreihen-Repository mit Jahres-/Quartalstrennung
- [x] SIC-Klassifikation (Migration) + Peer-Gruppen-Zuordnung
- [x] Sechs zahlenbasierte Warnsignal-Checks; textbasierte Signale
      explizit als offen dokumentiert (kein Fake-Coverage)
- [x] FundamentalsReport-Orchestrierung mit `data_completeness`/
      `missing_fields`
- [x] Tests: 66 neue (insgesamt 182 grün), `ruff`/`mypy` fehlerfrei
- [ ] **Offen:** Handrechnungs-Verifikation an mind. 3 realen
      Unternehmen (Auftrag-Abnahmekriterium) — in dieser Sandbox mangels
      Internetzugang nicht möglich (siehe `PROGRESS.md`, dieselbe
      Einschränkung wie Milestone 2). Nachholen, sobald Internetzugang
      verfügbar ist.
- [ ] Notierungswährung für Alpha-Vantage-Kurse auflösen (aus
      Milestone 2 verschoben, weiterhin offen)
- [ ] Peer-Gruppen um Größenfilter (Marktkapitalisierung) erweitern,
      sobald in Milestone 4 verfügbar

## Milestone 4 — Bewertung und Score (Implementierung abgeschlossen)

- [x] Multiples (KGV, EV/EBITDA, EV/EBIT, KBV, KCFV, FCF-Rendite) als
      reine Funktionen (`valuation/multiples.py`)
- [x] DCF mit drei Szenarien (Basis/optimistisch/pessimistisch) +
      Sensitivitätsmatrix (`valuation/dcf.py`)
- [x] Valuation-Report-Orchestrierung inkl. Peer-Vergleich und
      Datenlücken-Dokumentation (`valuation/report.py`)
- [x] Kennzahlen-Vokabular um `PRICE_CLOSE` erweitert, point-in-time-
      Zugriff auf den jüngsten Kurswert (`fundamentals/series.py::
      get_latest_value`)
- [x] Deterministisches, erklärbares Scoring mit Startgewichtung aus
      Auftrag §7, `coverage`-Konfidenzsignal, sichtbaren Risikoabzügen,
      Ausgabeklassen, Gegenargumenten/Ungültigkeitsbedingungen
      (`scoring/score.py`)
- [x] Tests: 59 neue (insgesamt 241 grün), `ruff`/`mypy` fehlerfrei
- [ ] **Offen:** DCF-/Multiples-/Scoring-Handrechnung an realen
      Unternehmen (Auftrag-Abnahmekriterium) — in dieser Sandbox mangels
      Internetzugang nicht möglich (siehe `PROGRESS.md`, dieselbe
      Einschränkung wie Milestone 2/3).
- [ ] Bewertungskomponente „Sicherheitsmarge" um historischen Multiples-
      Vergleich (eigene 5-/10-Jahres-Historie) erweitern, sobald
      mehrjährige Kurshistorie akkumuliert ist.
- [ ] Scoring-Komponente „Management/Kapitalallokation" um
      Insidertransaktionen/Vergütungsdaten erweitern, sobald eine
      strukturierte Quelle angebunden ist.
- [ ] WACC-Standardwert (9 %) durch unternehmensspezifische CAPM-
      Herleitung (mit Beta) ersetzen.
- [ ] `ScoreResult`/`ValuationReport` dauerhaft persistieren und ins
      Audit-Log schreiben (vorgesehen für Milestone 6/8a, UI/Rangliste).

## Milestone 5 — Nachrichtenanalyse (Implementierung abgeschlossen)

- [x] Connector-Grundgerüst um `get_text()` erweitert (RSS/Atom-Abruf)
- [x] GDELT-DOC-2.0-Connector (Volltextsuche, kein API-Schlüssel nötig)
- [x] Generischer IR-RSS-Connector (RSS-2.0/Atom-Parsing über stdlib)
- [x] `NewsItem`-Modell + Migration + Source-Seeding (`gdelt`/`ir_rss`)
- [x] HTML-Bereinigung zu Klartext (`news/sanitize.py`)
- [x] Deterministische Klassifikation: Quellqualität + Ereignistyp
      (`news/classification.py`)
- [x] Idempotente Ingestion mit URL-Normalisierung/Dedup-Hash
      (`news/ingest.py`)
- [x] Deterministisches Ereignis-Clustering (`news/clustering.py`) +
      `NewsReport`-Orchestrierung (`news/report.py`)
- [x] Tests: 60 neue (insgesamt 301 grün), `ruff`/`mypy` fehlerfrei
- [ ] **Offen:** Duplikaterkennung an einem realen Testset verifizieren
      (Auftrag-Abnahmekriterium) — in dieser Sandbox mangels
      Internetzugang nicht möglich (siehe `PROGRESS.md`).
- [ ] KI-Zusammenfassung mit Quellenverweis implementieren (UI-/
      Reports-Schicht, Milestone 6+) — Datengrundlage
      (`NewsCluster.items[*].url`) ist vorhanden.
- [ ] IR-RSS-Feed-URL-zu-Entity-Zuordnung lösen (aktuell nicht
      automatisiert, Connector erwartet die Feed-URL explizit).
- [ ] Quellqualitäts-Heuristik für „Kommentar" (kleine Domain-Liste in
      `news/classification.py`) bei Bedarf erweitern.

## Milestone 6 — Portfolio und Exporte (Implementierung abgeschlossen)

- [x] `portfolio/`-Modul: `WatchlistEntry`/`PortfolioPosition`-Modelle +
      Migration
- [x] CSV-Import (Watchlist + Portfolio), zeilengenaue Fehlersammlung,
      idempotent
- [x] Konzentrationsanalyse (Branche/Land/Währung), Positionsgrößen-
      Bandbreite, konfigurierbare `PortfolioAssumptions`
- [x] Historischer Max-Drawdown + Korrelation (reine Funktionen) +
      `PortfolioReport`-Orchestrierung
- [x] `reports/`-Modul: `ReportBundle` als einzige Quelle der Wahrheit +
      JSON-Export
- [x] Excel-Export (7 Tabellenblätter gemäß Auftrag §10) + PDF-Export
- [x] Tests: 60 neue (insgesamt 372 grün), `ruff`/`mypy` fehlerfrei
- [ ] **Offen:** UI-vs.-Export-Abgleich (Auftrag-Abnahmekriterium) live
      nachprüfen, sobald eine Streamlit-Detailseite existiert
      (voraussichtlich Milestone 8) — strukturell durch ADR-21
      (`ReportBundle`) bereits abgesichert.
- [ ] FX-Umrechnungsmodell für Portfolio-Konzentration bei gemischten
      Bestandswährungen (aktuell `computable=False`).
- [ ] Faktor-Konzentration (Value/Growth/Quality) — kein Faktormodell
      vorhanden.
- [ ] PDF-Export um Nachrichtentitel/-URLs als reine Tabellen-Zellen
      erweitern (aktuell bewusst nur aggregierte Zahlen, siehe ADR-21).
- [ ] IR-RSS-Feed-URL-zu-Entity-Zuordnung lösen (aus Milestone 5
      weiterhin offen).

## Milestone 7 — Backtesting (Implementierung abgeschlossen)

- [x] Point-in-time-Universum (`backtesting/universe.py`, ADR-22)
- [x] Perioden-Rendite inkl. geschätzter Dividende + Transaktionskosten
      (`backtesting/period_return.py`)
- [x] Train-/Validierungs-/Out-of-Sample-Split (`backtesting/splits.py`)
- [x] Kennzahlen: CAGR, Volatilität, Sharpe/Sortino, Turnover
      (`backtesting/metrics.py`); Max-Drawdown aus Milestone 6
      wiederverwendet
- [x] Deterministische Top-N-Score-Strategie (`backtesting/strategy.py`)
- [x] Rebalancing-Engine (`backtesting/engine.py`) + BacktestReport-
      Orchestrierung (`backtesting/report.py`)
- [x] Abnahmekriterium „kein Look-ahead" zweistufig nachgewiesen
      (Universum + vollständiger Backtest-Lauf)
- [x] Tests: 61 neue (insgesamt 425 grün), `ruff`/`mypy` fehlerfrei
- [ ] **Offen:** Verifikation mit echten Marktdaten (Auftrag-
      Abnahmekriterium) — in dieser Sandbox mangels Internetzugang
      nicht möglich (siehe `PROGRESS.md`).
- [ ] Benchmark-/Index-Kursquelle anbinden, damit „Ergebnisse gegen
      einfache Indizes vergleichen" mit echten Daten statt nur
      strukturell (Parameter-Schnittstelle) erfüllt ist.
- [ ] Survivorship-Bias vollständig schließen — dafür wäre eine
      Delisting-Historie-Quelle nötig, die im Kostenlos-Paket nicht
      existiert.
- [ ] Dividendenrendite periodengenauer schätzen statt grober
      Jahres-Näherung.
- [ ] Risikofreien Zins für Sharpe/Sortino aus einer echten Zinsreihe
      (z. B. EZB/FRED) beziehen statt Default 0.

## Milestone 8 — Sicherheit und Abnahme (abgeschlossen 2026-09-08, mit offenen Punkten, siehe ABNAHME.md)

- [x] Security-Review: jede `SECURITY.md`-Behauptung gegen den Code
      geprüft (siehe ADR-23). Drei echte Lücken gefunden und behoben:
      Downloadgrößen-Begrenzung (`ConnectorConfig.max_response_bytes`),
      unvollständige Log-Redaction (`record.args`), fehlender
      Pflichthinweis in Berichtsexporten (`reports/bundle.py::
      MANDATORY_DISCLAIMER`). Ein Dokumentationsfehler korrigiert
      (Redirect-Verhalten). `pip-audit`: keine bekannten Schwachstellen
      (Stand 2026-09-08).
- [x] Prompt-Injection-Schutz verifiziert: kein LLM-Aufruf existiert
      aktuell im Code; `news/sanitize.py` entfernt HTML/Skripte vor
      jeder Speicherung. Erneut zu prüfen, sobald die KI-Zusammenfassung
      (ADR-19) implementiert wird.
- [x] Ausfalltests (siehe ADR-24): XML-Entity-Expansion („Billion
      Laughs") im IR-RSS-Connector gefunden und behoben (Wechsel von
      `xml.etree.ElementTree` auf `defusedxml`, neue Abhängigkeit);
      Prompt-Injection-Versuch in News-Inhalten end-to-end als reine
      Nutzdaten bestätigt; widersprüchliche/extreme Testdaten (starke
      Verwässerung) end-to-end als sichtbare Score-Warnung bestätigt
      (kein stiller Fehlwert); Rate-Limit-Überschreitung je Connector
      durch bestehenden gemeinsamen Basis-Test abgedeckt; Restore-
      Prozess neu gebaut und end-to-end getestet
      (`db/backup.py::backup_database`/`restore_database` — Sicherung/
      Wiederherstellung der SQLite-Datenbankdatei, zusätzlich zum
      bereits bestehenden Alembic-Up-/Downgrade-Test). Eine echte
      Datenlücke dokumentiert statt verschwiegen: Auftrag-§3-„bei
      Widerspruch beide Werte zeigen" ist mit dem aktuellen
      Kostenlos-Quellen-Set strukturell nicht auftretbar (nur eine
      Fundamentaldatenquelle angebunden) und daher nicht implementiert.
- [x] Windows-Setup vervollständigt: `start.ps1` sichert die Datenbank
      jetzt automatisch vor jeder Migration (`-NoBackup` zum
      Überspringen, best-effort — Fehlschlag bricht den Start nicht
      ab); neue Skripte `scripts/backup-database.ps1`/
      `scripts/restore-database.ps1`; neues CLI-Werkzeug
      `db/backup_cli.py` (`sichern`/`wiederherstellen`/`auflisten`,
      5 neue Tests). Windows-Installer-Binärdatei (.exe/.msi) wird
      weiterhin NICHT gebaut — in dieser Linux-Sandbox keine Windows-
      Build-Tools verfügbar; als bewusste, dokumentierte Einschränkung
      in `README.md`/`BENUTZERHANDBUCH.md` festgehalten.
- [x] `BENUTZERHANDBUCH.md` geschrieben (Installation, Ersteinrichtung,
      Datenspeicherorte, Datenschutz/Sicherheit, Datensicherung,
      Fehlerbehebung, weiterführende Dokumente). Enthält einen
      ausdrücklich ehrlichen Abschnitt „Was die Oberfläche heute zeigt
      — und was noch nicht": nur die Start-/Datenstatus-Seite ist als
      Bildschirmseite gebaut, die übrigen neun Auftrag-§10-Seiten
      fehlen noch (Analysemotor selbst ist vollständig implementiert
      und getestet, nur noch nicht über die Oberfläche erreichbar).
- [x] Unabhängiger Security-/Plausibilitätscheck (Auftrag §15
      Kriterium 9): separater Agentendurchlauf ohne Kenntnis der
      Implementierungsentscheidungen, fand einen echten, blockierenden
      Look-ahead-Bias in `risk/warning_signals.py` (fehlendes `as_of`
      in allen Warnsignal-Checks — floss über `total_score` direkt in
      `backtesting/strategy.py::select_top_n` ein) sowie zwei weitere
      Härtungspunkte (Downloadgrößen-Prüfung jetzt gestreamt statt
      erst nach vollständiger Pufferung; HTML-Sanitizing-Fallback
      entfernt jetzt auch im Ausnahmefall Markup) und eine bewusst
      nicht behobene, ehrlich dokumentierte SSRF-Restlücke
      (Time-of-check-to-time-of-use). Alles in `DECISIONS.md` ADR-25
      dokumentiert, die ersten drei Funde behoben und mit neuen
      Regressionstests abgesichert (453 Tests, zuvor 450).
- [x] Abnahme-Checkliste gegen Auftrag §15 (neun Kriterien) ehrlich
      durchgegangen: `ABNAHME.md`. Sechs Kriterien vollständig erfüllt,
      eines teilweise (Handrechnung nur an synthetischen Daten), zwei
      strukturell fundiert aber empirisch nicht abschließend
      nachweisbar (kompletter Lauf mit echten Daten; Exporte = UI-Werte,
      da noch keine UI-Detailseite existiert) — ehrlich als offen
      geführt, nicht stillschweigend als erfüllt behandelt.
- [x] Finaler Doku-Abschluss (alle Pflichtdateien), `pytest`/`ruff`/
      `mypy` grün (453 Tests), Commit + Push.

## Nach Milestone 8 — Ausbau der Auftrag-§10-Oberflächenseiten (laufend)

Der ursprüngliche Auftragsplan (Milestone 0–8) ist abgeschlossen (siehe
oben). Auf Nutzerwunsch werden jetzt die restlichen Auftrag-§10-
Bildschirmseiten nachgezogen — der Analysemotor dahinter war bereits
seit Milestone 1–7 fertig, nur die Bedienoberfläche fehlte.

- [x] **Marktscreener** (Seite 2, siehe ADR-26): Unternehmen per
      CIK/Ticker hinzufügen, SEC-EDGAR-Fundamentaldaten und optional
      einen Alpha-Vantage-Kurs abrufen. Neues Modul `ingestion/
      pipeline.py` (Orchestrierung, per Dependency Injection ohne
      echten Netzwerkzugriff testbar), neues Profilfeld
      `sec_edgar_kontakt_email` (SEC-Pflichtangabe, bewusst nicht
      automatisch aus dem Nutzerkonto übernommen), `SecretStore` erstmals
      in `AppContext` verfügbar (nur OS-Keyring, kein Master-Passwort-
      Dialog — folgt mit der Einstellungen-Seite), einfache Liste
      bereits erfasster Unternehmen mit Namenssuche. Sidebar-Navigation
      (`st.sidebar.radio`) statt `st.navigation()` — bewusst einfach
      gehalten, solange nur zwei Seiten existieren. 20 neue Tests
      (insgesamt 471), `ruff`/`mypy` fehlerfrei. Mit echtem Playwright-
      Browser gegen einen laufenden Streamlit-Prozess verifiziert
      (Rendering, Navigation, Formularvalidierung) — ein echter SEC-
      EDGAR-Live-Abruf war mangels Internetzugang in dieser Sandbox
      nicht testbar (Nutzer muss das auf dem eigenen Rechner prüfen).
- [x] **Kandidaten-Rangliste** (Seite 3, siehe ADR-28): sortierbare
      Tabelle aller bereits erfassten Unternehmen nach Gesamtscore.
      Neues Modul `ui/ranking.py` — baut je Zeile den vollständigen
      `ReportBundle` (wie `ui/detail.py`), damit Score, Datenabdeckung
      und Klassifikation garantiert dieselben Werte zeigen wie die
      Detailseite und die Exporte. Rankt bewusst nur bereits erfasste
      Unternehmen (keine Breitensuche über ein größeres Universum —
      existiert in diesem Programm noch nicht). Warnung bei
      Unternehmen mit Klassifikation „Datenlage unzureichend". 4 neue
      Tests (insgesamt 482), `ruff`/`mypy` fehlerfrei. Mit echtem
      Playwright-Browser gegen eine synthetisch befüllte Testdatenbank
      mit drei Unternehmen verifiziert.
- [x] **Unternehmensdetail mit Quellenleiste** (Seite 4, siehe ADR-27):
      vollständiger `ReportBundle` (Kopfzeile mit Datenstand/Analysezeit/
      Marktdatenverzögerung/Datenabdeckung/Konfidenz, Kennzahlen,
      Bewertung inkl. DCF-Szenarien/Peer-Vergleich, Score inkl.
      Risikoabzügen/Gegenargumenten/Ungültigkeitsbedingungen, Nachrichten-
      Cluster, Quellenleiste mit Lizenzhinweis, Annahmen, JSON-/Excel-/
      PDF-Export) für ein ausgewähltes Unternehmen. Neues Modul
      `ui/detail.py` — rendert ausschließlich aus `report_bundle_to_dict()`,
      genau wie die Exportformate, wodurch Auftrag-§15-Kriterium 8
      („Exporte = Oberflächenwerte") jetzt strukturell erfüllt ist (siehe
      `ABNAHME.md`). 7 neue Tests (insgesamt 478), `ruff`/`mypy`
      fehlerfrei. Mit echtem Playwright-Browser gegen einen laufenden
      Streamlit-Prozess mit synthetisch befüllter Testdatenbank
      verifiziert — alle Abschnitte inkl. der drei Download-Buttons
      rendern korrekt.
- [ ] **Peer-Vergleich** (Seite 5): `fundamentals/peers.py::find_peers`
      bereits vorhanden, nur keine UI.
- [ ] **DCF- und Szenarioanalyse** (Seite 6): `valuation/dcf.py`
      inkl. Sensitivitätsmatrix bereits vorhanden, nur keine UI.
- [ ] **Nachrichten/Ereignisse** (Seite 7): `news/report.py::
      build_news_report` bereits vorhanden, nur keine UI. Benötigt
      zusätzlich einen GDELT-/IR-RSS-Abrufweg im Marktscreener oder
      einer eigenen Aktualisierungsfunktion.
- [ ] **Watchlist/Portfolio** (Seite 8): CSV-Import
      (`portfolio/csv_import.py`) und `PortfolioReport`-Orchestrierung
      bereits vorhanden, nur keine UI.
- [ ] **Backtest** (Seite 9): `backtesting/engine.py::run_backtest`
      bereits vorhanden, nur keine UI (Stichtags-/Top-N-Auswahl,
      Kennzahlen-Anzeige, Diagramm der NAV-Zeitreihe).
- [ ] **Einstellungen, Quellen und Prüfprotokoll** (Seite 10):
      Schlüsselverwaltung (`SecretStore.set_secret`/`delete_secret`,
      inkl. Master-Passwort-Dialog für den verschlüsselten Datei-
      Fallback, falls kein OS-Keyring verfügbar ist), Quellenübersicht
      (`Source`-Tabelle), Prüfprotokoll-Ansicht (`AuditLogEntry`-Tabelle).
      Wichtig für den Alpha-Vantage-Kursabruf im Marktscreener, der
      aktuell nur funktioniert, wenn der Schlüssel bereits anderweitig
      im OS-Keyring hinterlegt wurde.
- [ ] Sobald mehr als drei/vier Seiten existieren: Umstieg von
      `st.sidebar.radio` auf `st.navigation()`/`st.Page()` (siehe ADR-26).
