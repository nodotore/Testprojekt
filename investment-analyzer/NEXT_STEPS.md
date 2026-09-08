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
11a. **Aktuell nächster inhaltlicher Schritt:** Milestone 8 fortsetzen —
    Ausfalltests (manipulierte/böswillige Webinhalte, absichtlich
    falsche/widersprüchliche Testdaten, Rate-Limit-Überschreitung je
    Connector, Restore-Prozess/Alembic-Up-Down-Zyklus end-to-end),
    danach Windows-Setup härten + `BENUTZERHANDBUCH.md` schreiben,
    danach die finale Abnahme-Checkliste gegen Auftrag §15 (neun
    Kriterien, ehrlich als erfüllt/teilweise/nicht erfüllt bewerten)
    und den Projekt-Doku-Abschluss. Danach — falls vom Nutzer
    priorisiert und nicht Teil der Milestone-8-Abnahme — die beiden in
    Milestone 4 als nicht berechenbar dokumentierten Scoring-
    Komponenten „Wettbewerbsvorteil" und „Nachrichten und Katalysatoren"
    auf Basis des jetzt verfügbaren `news`-Moduls ergänzen (siehe
    ADR-17) sowie die KI-Zusammenfassung mit Quellenverweis für
    Nachrichten-Cluster implementieren (siehe ADR-19/`news/report.py`;
    danach ist der Prompt-Injection-Schutz aus ADR-23 Befund 5 erneut
    zu prüfen, da dann erstmals ein LLM-Aufruf existiert).
12. Bei Gelegenheit, nicht blockierend für Milestone 8:
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
    - PostgreSQL-Migrationstest gegen eine echte Instanz, Test der
      Streamlit-Oberfläche in einem echten Browser (Sandbox hatte nur
      Headless-/HTTP-Verifikation zur Verfügung).
