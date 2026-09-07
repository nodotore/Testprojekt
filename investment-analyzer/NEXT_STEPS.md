# Nächste Schritte — Investment-Analysator

1. ~~Blocker: Nutzer beantwortet die vier blockierenden Fragen aus
   `MILESTONE_0.md`~~ — erledigt am 2026-09-07 (siehe `MILESTONE_0.md`,
   ADR-7–ADR-10 in `DECISIONS.md`).
2. ~~Freigabe zum Start von Milestone 1~~ — erteilt am 2026-09-07.
3. ~~Milestone 1 („Grundgerüst") umsetzen~~ — abgeschlossen am
   2026-09-07 (siehe `PROGRESS.md`; 50 Tests grün, ruff/mypy fehlerfrei).
4. **Aktuell:** Milestone 2 (Datenbeschaffung) gemäß `PLAN.md` beginnen:
   Connector-Basisklasse, SEC EDGAR (Meldungen), Alpha Vantage Free
   (Marktdaten), SSRF-Schutz/URL-Allowlist, Normalisierung,
   Entity-Resolution-Befüllung, Cache-/Rate-Limit-/Ausfalltests. Die
   bekannte EU/DE-Datenlücke (ADR-9) im späteren UI-Datenstatus sichtbar
   machen, nicht verschweigen.
5. Vor Abschluss von Milestone 1 als vollständig erledigt zu betrachten:
   zwei offene Punkte aus `PROGRESS.md`/`TODO.md` bei Gelegenheit
   nachholen — PostgreSQL-Migrationstest gegen eine echte Instanz und
   ein Test der Streamlit-Oberfläche in einem echten Browser (Sandbox
   hatte nur Headless-/HTTP-Verifikation zur Verfügung).
