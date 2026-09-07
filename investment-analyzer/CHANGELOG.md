# Changelog — Investment-Analysator

## Unreleased

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
