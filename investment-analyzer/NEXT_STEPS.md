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
   **Ein Punkt bleibt formal offen, siehe 5.**
5. **Offen — vor produktivem Einsatz nachzuholen:** Live-Verifikation
   der beiden Connectoren gegen die echten APIs mit mindestens zehn
   realen Unternehmen (Auftrag-Abnahmekriterium Milestone 2). In dieser
   Sandbox-Entwicklungsumgebung ist ausgehender Netzwerkzugriff auf
   `sec.gov` und `alphavantage.co` durch die Egress-Policy des
   Umgebungs-Proxys blockiert (verifiziert per `curl`, siehe
   `PROGRESS.md`). Sobald eine Umgebung mit echtem Internetzugang zur
   Verfügung steht (z. B. beim Nutzer über `start.ps1`):
   - SEC EDGAR: benötigt nur eine gültige Kontaktadresse für den
     User-Agent-Header, kein API-Schlüssel — sollte direkt funktionieren.
   - Alpha Vantage: benötigt einen echten API-Schlüssel vom Nutzer
     (kostenlos erhältlich unter alphavantage.co); der öffentliche
     „demo"-Schlüssel deckt nur das Testsymbol IBM ab, nicht zehn
     beliebige Unternehmen.
6. **Aktuell nächster inhaltlicher Schritt:** Milestone 3
   (Fundamentalanalyse) gemäß `PLAN.md` beginnen — Kennzahlenberechnung,
   Zeitreihen (1/3/5/10 Jahre), Peer-Gruppen, Warnsignale. Dabei auch
   die in Milestone 2 offen gelassene Notierungswährung für
   Alpha-Vantage-Kurse auflösen (siehe `TODO.md`).
7. Weiterhin offen, bei Gelegenheit nachzuholen (nicht blockierend):
   PostgreSQL-Migrationstest gegen eine echte Instanz, Test der
   Streamlit-Oberfläche in einem echten Browser (Sandbox hatte nur
   Headless-/HTTP-Verifikation zur Verfügung).
