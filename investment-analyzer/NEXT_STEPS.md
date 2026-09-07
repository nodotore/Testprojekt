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
7. **Offen — vor produktivem Einsatz nachzuholen (Milestone 2–4, ein
   gemeinsamer Blocker):** Live-Verifikation der Connectoren gegen die
   echten APIs mit mindestens zehn realen Unternehmen, Handrechnungs-
   Abgleich der Fundamentalkennzahlen mit mindestens drei davon, UND
   Handrechnungs-Abgleich von DCF/Multiples/Score mit denselben oder
   weiteren realen Unternehmen (Auftrag-Abnahmekriterien Milestone 2–4).
   In dieser Sandbox-Entwicklungsumgebung ist ausgehender
   Netzwerkzugriff auf `sec.gov` und `alphavantage.co` durch die
   Egress-Policy des Umgebungs-Proxys blockiert (verifiziert per
   `curl`, siehe `PROGRESS.md`). Sobald eine Umgebung mit echtem
   Internetzugang zur Verfügung steht (z. B. beim Nutzer über
   `start.ps1`):
   - SEC EDGAR: benötigt nur eine gültige Kontaktadresse für den
     User-Agent-Header, kein API-Schlüssel — sollte direkt funktionieren.
   - Alpha Vantage: benötigt einen echten API-Schlüssel vom Nutzer
     (kostenlos erhältlich unter alphavantage.co); der öffentliche
     „demo"-Schlüssel deckt nur das Testsymbol IBM ab, nicht zehn
     beliebige Unternehmen.
   - Für den Handrechnungs-Abgleich: drei reale Unternehmen mit
     öffentlich einsehbaren Geschäftsberichten auswählen, Kennzahlen von
     Hand aus dem 10-K nachrechnen und mit `build_fundamentals_report()`
     vergleichen; anschließend DCF/Multiples/Score derselben Unternehmen
     von Hand nachrechnen und mit `build_valuation_report()`/
     `score_entity()` vergleichen.
8. **Aktuell nächster inhaltlicher Schritt:** Milestone 5
   (Nachrichtenanalyse) gemäß `PLAN.md` beginnen — Abruf, Deduplizierung,
   Clustering, Klassifikation von Nachrichten; anschließend die beiden
   in Milestone 4 als nicht berechenbar dokumentierten Scoring-
   Komponenten „Wettbewerbsvorteil" und „Nachrichten und Katalysatoren"
   ergänzen (siehe ADR-17).
9. Bei Gelegenheit, nicht blockierend für Milestone 5:
   - Notierungswährung für Alpha-Vantage-Kurse auflösen (aus
     Milestone 2 offen, weiterhin nicht erledigt).
   - Peer-Gruppen-Zuordnung um einen Größenfilter (Marktkapitalisierung)
     ergänzen (jetzt mit `PRICE_CLOSE`/Marktkapitalisierung verfügbar).
   - WACC-Standardwert durch unternehmensspezifische CAPM-Herleitung
     (mit Beta) ersetzen.
   - Scoring-Komponente „Management/Kapitalallokation" um
     Insidertransaktionen/Vergütungsdaten erweitern, sobald eine
     strukturierte Quelle angebunden ist.
   - PostgreSQL-Migrationstest gegen eine echte Instanz, Test der
     Streamlit-Oberfläche in einem echten Browser (Sandbox hatte nur
     Headless-/HTTP-Verifikation zur Verfügung).
