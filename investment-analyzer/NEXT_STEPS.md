# Nächste Schritte — Investment-Analysator

1. ~~Blocker: Nutzer beantwortet die vier blockierenden Fragen aus
   `MILESTONE_0.md`~~ — erledigt am 2026-09-07 (siehe `MILESTONE_0.md`,
   ADR-7–ADR-10 in `DECISIONS.md`).
2. ~~Freigabe zum Start von Milestone 1~~ — erteilt am 2026-09-07.
3. ~~Milestone 1 („Grundgerüst") umsetzen~~ — abgeschlossen am
   2026-09-07 (siehe `PROGRESS.md`; 50 Tests grün, ruff/mypy fehlerfrei).
4. ~~Milestone 2 („Datenbeschaffung") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (SEC-EDGAR- + Alpha-Vantage-Connector,
   Entity-Resolution, Ingestion; 116 Tests grün, ruff/mypy fehlerfrei).
5. ~~Milestone 3 („Fundamentalanalyse") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (Kennzahlen-Vokabular, Berechnungskern,
   Zeitreihen-Repository, SIC-Klassifikation/Peer-Gruppen, Warnsignale,
   FundamentalsReport; 182 Tests grün, ruff/mypy fehlerfrei).
6. ~~Milestone 4 („Bewertung und Score") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (Multiples, DCF mit drei Szenarien +
   Sensitivitätsmatrix, Valuation-Report, erklärbares Scoring mit
   Startgewichtung/Konfidenzlogik/Gegenargumenten; 241 Tests grün,
   ruff/mypy fehlerfrei).
7. ~~Milestone 5 („Nachrichtenanalyse") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (GDELT-/IR-RSS-Connectoren, `NewsItem`-
   Modell, HTML-Bereinigung, Klassifikation, Dedup-Ingestion,
   Ereignis-Clustering, `NewsReport`; 301 Tests grün, ruff/mypy
   fehlerfrei).
8. ~~Milestone 6 („Portfolio und Exporte") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (`portfolio/`-Modul: Watchlist/Portfolio-
   Import, Konzentration, Korrelation/Drawdown, Positionsgrößen-
   Bandbreite; `reports/`-Modul: `ReportBundle`, JSON-/Excel-/
   PDF-Export; 372 Tests grün, ruff/mypy fehlerfrei).
9. ~~Milestone 7 („Backtesting") umsetzen~~ — Implementierung
   abgeschlossen am 2026-09-07 (Point-in-time-Universum,
   Rebalancing-Engine, Top-N-Score-Strategie, CAGR/Vola/Sharpe/Sortino/
   Turnover/MaxDD, zweistufig nachgewiesener Look-ahead-Schutz;
   425 Tests grün, ruff/mypy fehlerfrei).
10. **Offen — vor produktivem Einsatz nachzuholen (Milestone 2–7, ein
    gemeinsamer Blocker):** Live-Verifikation der Connectoren gegen die
    echten APIs mit mindestens zehn realen Unternehmen, Handrechnungs-
    Abgleich der Fundamentalkennzahlen mit mindestens drei davon,
    Handrechnungs-Abgleich von DCF/Multiples/Score mit denselben oder
    weiteren realen Unternehmen, Verifikation der Duplikaterkennung an
    einem realen Nachrichten-Testset, Verifikation von Portfolio-
    Konzentration/Korrelation/Drawdown sowie der Export-Formate an einem
    realen Portfolio, UND ein realer Backtest-Lauf mit echten
    Kurshistorien über mehrere Rebalancing-Perioden (Auftrag-
    Abnahmekriterien Milestone 2–7). In dieser Sandbox-
    Entwicklungsumgebung ist ausgehender Netzwerkzugriff auf `sec.gov`,
    `alphavantage.co`, `api.gdeltproject.org` und beliebige IR-RSS-Hosts
    durch die Egress-Policy des Umgebungs-Proxys blockiert (verifiziert
    per `curl`, siehe `PROGRESS.md`). Sobald eine Umgebung mit echtem
    Internetzugang zur Verfügung steht (z. B. beim Nutzer über
    `start.ps1`):
    - SEC EDGAR: benötigt nur eine gültige Kontaktadresse für den
      User-Agent-Header, kein API-Schlüssel — sollte direkt funktionieren.
    - Alpha Vantage: benötigt einen echten API-Schlüssel vom Nutzer
      (kostenlos erhältlich unter alphavantage.co); der öffentliche
      „demo"-Schlüssel deckt nur das Testsymbol IBM ab, nicht zehn
      beliebige Unternehmen.
    - GDELT: benötigt keinen API-Schlüssel, sollte direkt funktionieren.
    - IR-RSS: benötigt reale Feed-URLs einiger Testunternehmen (manuell
      ermitteln, da die Feed-URL-zu-Entity-Zuordnung noch nicht
      automatisiert ist, siehe Punkt 12).
    - Für den Handrechnungs-Abgleich: drei reale Unternehmen mit
      öffentlich einsehbaren Geschäftsberichten auswählen, Kennzahlen von
      Hand aus dem 10-K nachrechnen und mit `build_fundamentals_report()`
      vergleichen; anschließend DCF/Multiples/Score derselben Unternehmen
      von Hand nachrechnen und mit `build_valuation_report()`/
      `score_entity()` vergleichen.
    - Für Portfolio/Exporte: ein reales Musterportfolio (3-5 reale
      Positionen mit echten Kursen über mehrere Tage) anlegen, Excel-/
      PDF-/JSON-Export erzeugen und mit einer künftigen UI-Detailseite
      abgleichen, sobald diese existiert (Milestone 8, siehe ADR-21).
    - Für Backtesting: über mehrere Wochen/Monate echte
      Alpha-Vantage-Kurs-Snapshots für 5-10 Unternehmen akkumulieren
      (täglicher Abruf), dann `run_backtest()`/`build_backtest_report()`
      über mehrere Rebalancing-Stichtage ausführen und die Kennzahlen
      stichprobenartig von Hand nachrechnen.
11. ~~Milestone 8 Security-Review durchführen~~ — abgeschlossen am
    2026-09-08 (siehe `PROGRESS.md`/ADR-23): drei echte Lücken
    behoben (Downloadgrößen-Begrenzung, unvollständige Log-Redaction,
    fehlender Pflichthinweis in Berichtsexporten), ein
    Dokumentationsfehler korrigiert (Redirect-Verhalten), `pip-audit`
    ohne Befund. 435 Tests grün, ruff/mypy fehlerfrei.
11a. ~~Milestone 8 Ausfalltests durchführen~~ — abgeschlossen am
    2026-09-08 (siehe `PROGRESS.md`/ADR-24): echte Sicherheitslücke
    gefunden und behoben (XML-Entity-Expansion im IR-RSS-Connector,
    Wechsel auf `defusedxml`), Prompt-Injection- und widersprüchliche-
    Daten-Ausfalltests bestätigen bestehende Mechanismen end-to-end,
    neuer Restore-Prozess-Baustein (`db/backup.py`) end-to-end
    getestet, Rate-Limit-Überschreitung je Connector bereits abgedeckt.
    445 Tests grün, ruff/mypy fehlerfrei.
11b. ~~Milestone 8 Windows-Setup vervollständigen + Benutzerhandbuch~~ —
    abgeschlossen am 2026-09-08 (siehe `PROGRESS.md`): `start.ps1`
    sichert die Datenbank jetzt automatisch vor jeder Migration, neue
    Endnutzer-Skripte `scripts/backup-database.ps1`/
    `scripts/restore-database.ps1`, neues `BENUTZERHANDBUCH.md` (inkl.
    ehrlicher Abschnitt zum aktuellen UI-Stand), `README.md`
    aktualisiert. 450 Tests grün, ruff/mypy fehlerfrei.
11c. ~~Milestone 8 abschließen: unabhängiger Review + Abnahme-
    Checkliste~~ — abgeschlossen am 2026-09-08 (siehe `PROGRESS.md`/
    ADR-25/`ABNAHME.md`). Separater, unabhängiger Agentenlauf fand
    einen echten, blockierenden Look-ahead-Bias in
    `risk/warning_signals.py` (fehlendes `as_of`, floss über
    `total_score` in die Backtest-Kandidatenauswahl ein) — noch in
    dieser Runde behoben und mit zwei Regressionstests abgesichert.
    Zwei weitere Härtungen behoben (Downloadgrößen-Prüfung per
    Streaming, HTML-Sanitizing-Fallback). Eine SSRF-Restlücke bewusst
    nicht behoben, ehrlich dokumentiert. Abnahme-Checkliste gegen alle
    neun Auftrag-§15-Kriterien in `ABNAHME.md`: 6/9 vollständig
    erfüllt, 1/9 teilweise, 2/9 strukturell fundiert aber noch nicht
    empirisch nachweisbar. 453 Tests grün, ruff/mypy fehlerfrei. **Damit
    ist der ursprüngliche Milestone-0–8-Plan aus `AUFTRAG.md`/`PLAN.md`
    vollständig durchlaufen.**
12. **Nächste Schritte — nicht mehr Teil des ursprünglichen
    Milestone-Plans, priorisiert nach Auftrag-Relevanz:**
    - **Vor jedem produktiven Einsatz zwingend nachzuholen** (siehe
      Punkt 10 oben): Live-Verifikation mit echten Datenquellen inkl.
      Hand-Verifikation an realen Unternehmenszahlen — die einzige
      verbleibende Lücke, die Auftrag-§15-Kriterien nicht als
      vollständig erfüllt gelten lässt (Kriterien 1, 6, 8 in
      `ABNAHME.md`). Sobald Internetzugang verfügbar ist: Reihenfolge
      und konkrete Schritte siehe Punkt 10.
    - ~~Ausbau der Auftrag-§10-UI-Seite „Marktscreener"~~ — umgesetzt
      am 2026-09-09 (siehe `PROGRESS.md`/ADR-26): neues `ingestion/`-
      Modul, Profilfeld `sec_edgar_kontakt_email`, `SecretStore` in
      der Oberfläche, Sidebar-Navigation. 471 Tests grün, ruff/mypy
      fehlerfrei, mit echtem Browser (Playwright) verifiziert.
    - ~~Ausbau der Auftrag-§10-UI-Seite „Unternehmensdetail mit
      Quellenleiste"~~ — umgesetzt am 2026-09-09 (siehe
      `PROGRESS.md`/ADR-27): neue `ui/detail.py`, rendert
      ausschließlich aus demselben `ReportBundle` wie die Exporte —
      schließt damit Auftrag-§15-Kriterium 8 („Exporte =
      Oberflächenwerte") strukturell UND durch eine echte UI-Seite
      (siehe aktualisierte Bewertung in `ABNAHME.md`). 478 Tests grün,
      ruff/mypy fehlerfrei, mit echtem Browser (Playwright) gegen eine
      synthetisch befüllte Testdatenbank verifiziert.
    - ~~Ausbau der Auftrag-§10-UI-Seite „Kandidaten-Rangliste"~~ —
      umgesetzt am 2026-09-09 (siehe `PROGRESS.md`/ADR-28): neue
      `ui/ranking.py`, baut je Zeile den vollständigen `ReportBundle`
      wie die Detailseite (garantiert konsistente Werte), rankt bewusst
      nur bereits erfasste Unternehmen (keine Breitensuche — noch nicht
      vorhanden, siehe unten). 482 Tests grün, ruff/mypy fehlerfrei, mit
      echtem Browser (Playwright) gegen drei synthetisch befüllte
      Unternehmen verifiziert.
    - **Ausbau der sechs weiteren Auftrag-§10-UI-Seiten** (Peer-
      Vergleich, DCF-/Szenarioanalyse, Nachrichten/Ereignisse,
      Watchlist/Portfolio, Backtest, Einstellungen/Quellen/
      Prüfprotokoll) — empfohlene Reihenfolge: Peer-Vergleich/DCF als
      Nächstes (nutzen dieselben Daten wie die Detailseite), zuletzt
      Watchlist/Portfolio, Backtest, Einstellungen (jeweils eigene
      Datenflüsse). Einstellungen-Seite ist zudem Voraussetzung dafür,
      dass der Alpha-Vantage-Kursabruf im Marktscreener ohne vorherige
      manuelle OS-Keyring-Einrichtung nutzbar wird.
    - Neu, nicht blockierend (aus dem Bau der Kandidaten-Rangliste,
      ADR-28): eine echte Breitensuche über ein größeres
      Aktienuniversum für den Marktscreener (z. B. SEC-EDGAR-
      Volltextsuche oder eine gepflegte Ticker-Liste) würde die
      Kandidaten-Rangliste erst zu einer echten Screening-Funktion
      machen — aktuell rankt sie nur bereits manuell hinzugefügte
      Unternehmen.
    - SSRF-IP-Pinning bis zur tatsächlichen HTTP-Verbindung (ADR-25
      Befund 4, `SECURITY.md`) — behebt die dokumentierte Time-of-
      check-to-time-of-use-Restlücke; erfordert einen eigenen
      `httpx`-Transport/Resolver, bewusst nicht kurzfristig umgesetzt.
    - Lockfile für Abhängigkeits-Pinning (`SECURITY.md`, aktuell nur
      `>=`-Untergrenzen in `pyproject.toml`).
    - Die beiden in Milestone 4 als nicht berechenbar dokumentierten
      Scoring-Komponenten „Wettbewerbsvorteil" und „Nachrichten und
      Katalysatoren" auf Basis des jetzt verfügbaren `news`-Moduls
      ergänzen (siehe ADR-17) sowie die KI-Zusammenfassung mit
      Quellenverweis für Nachrichten-Cluster implementieren (siehe
      ADR-19/`news/report.py`; danach ist der Prompt-Injection-Schutz
      aus ADR-23 Befund 5 erneut zu prüfen, da dann erstmals ein
      LLM-Aufruf existiert).
13. Bei Gelegenheit, weiterhin nicht blockierend:
    - Notierungswährung für Alpha-Vantage-Kurse auflösen (aus
      Milestone 2 offen, weiterhin nicht erledigt — jetzt zusätzlich
      relevant für die Portfolio-Konzentrationsanalyse, ADR-20, und die
      Backtest-Währungsumrechnung, ADR-22).
    - Peer-Gruppen-Zuordnung um einen Größenfilter (Marktkapitalisierung)
      ergänzen (jetzt mit `PRICE_CLOSE`/Marktkapitalisierung verfügbar).
    - WACC-Standardwert durch unternehmensspezifische CAPM-Herleitung
      (mit Beta) ersetzen.
    - Scoring-Komponente „Management/Kapitalallokation" um
      Insidertransaktionen/Vergütungsdaten erweitern, sobald eine
      strukturierte Quelle angebunden ist.
    - IR-RSS-Feed-URL-zu-Entity-Zuordnung lösen (z. B. als Feld am
      Nutzerprofil/Watchlist-Eintrag oder eigene Zuordnungstabelle).
    - Quellqualitäts-Heuristik für „Kommentar" (`news/classification.py`)
      bei Bedarf um weitere bekannte Domains erweitern.
    - PDF-Export um Nachrichtentitel/-URLs als reine Tabellen-Zellen
      erweitern (aktuell bewusst nur aggregierte Zahlen, siehe ADR-21).
    - FX-Umrechnungsmodell für Portfolio-Konzentration und Backtest-
      Renditen bei gemischten Bestandswährungen.
    - Benchmark-/Index-Kursquelle für den Backtest-Vergleich anbinden.
    - Risikofreien Zins für Sharpe/Sortino aus einer echten Zinsreihe
      (z. B. EZB/FRED) beziehen statt Default 0.
    - PostgreSQL-Migrationstest gegen eine echte Instanz (weiterhin offen).
    - ~~Test der Streamlit-Oberfläche in einem echten Browser~~ —
      inzwischen mehrfach mit echtem, headless laufendem Chromium
      (Playwright) gegen einen echten `streamlit run`-Prozess verifiziert
      (Ersteinrichtung, Datenstatus, Marktscreener inkl. Formular-
      validierung, Unternehmensdetail und Kandidaten-Rangliste mit
      synthetisch befüllter Testdatenbank) — kein reiner
      `AppTest`-Trockentest mehr, siehe `PROGRESS.md`.
