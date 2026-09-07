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

## Milestone 6 — Portfolio und Exporte (nächster Schritt)

Siehe `PLAN.md` für Details; wird hier aufgeschlüsselt, sobald die
Milestone beginnt.

## Spätere Milestones

Siehe `PLAN.md` für Milestone 7–8; werden hier erst als Einzelaufgaben
aufgeschlüsselt, wenn die jeweilige Milestone beginnt.
