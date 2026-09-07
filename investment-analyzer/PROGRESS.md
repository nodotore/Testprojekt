# Fortschritt — Investment-Analysator

## Milestone 0 — Klärung und Datenlizenzen

**Status: Fragen beantwortet, wartet auf ausdrückliche Freigabe für Milestone 1.**

Nutzerantworten (2026-09-07): Projektstruktur = Unterverzeichnis in
diesem Repo (bestätigt); Kostenvariante = Kostenlos; Prioritätsmärkte =
breit (USA, Deutschland, übriges Europa, weitere global offen);
Deployment = lokal Windows + SQLite. Festgehalten als ADR-7–ADR-10 in
`DECISIONS.md`, Details in `MILESTONE_0.md`.

Umgesetzt (dieser Agentenlauf, Hauptagent/project-orchestrator, keine
Parallelisierung nötig für reine Dokumentation):

- `AUFTRAG.md`: unveränderte Referenzkopie des Originalauftrags
- `CLAUDE.md`: Leitplanken, Modulgrenzen, Agentenregeln für künftige
  Sessions
- `MILESTONE_0.md`: Fragenliste (blockierend + ergänzend mit
  Standardwertvorschlag)
- `DATA_SOURCES.md`: Quellen-/Lizenzmatrix nach Auftrag-Hierarchie
  (Stufe 1–7) mit drei Kostenvarianten (kostenlos/günstig/professionell)
- `DECISIONS.md`: ADR-1 (Unterverzeichnis statt Repo-Root), ADR-2
  (Tech-Stack), ADR-3 (Modulgrenzen), ADR-4 (Agentenkoordination),
  ADR-5 (Secret-Management), ADR-6 (Provenienz-first-Datenmodell)
- `PLAN.md`: verbindlicher Implementierungsplan Milestone 0–8
- `METHODOLOGY.md`: Planungsstand Kennzahlen/Bewertung/Scoring/
  Zukunftsanalyse/Backtesting-Prinzipien
- `SECURITY.md`: Planungsstand Sicherheitsrichtlinie

**Geänderte Dateien:** ausschließlich neue Dateien unter
`investment-analyzer/` (keine bestehenden Repo-Dateien verändert).

**Tests:** keine (reine Dokumentation, kein Code in Milestone 0).

**Offene Risiken:**
- EU/DE-Meldungsabdeckung strukturell schwächer als USA in der
  Kostenlos-Variante (bekannte, dokumentierte Lücke, siehe ADR-9).
- Konkrete Schwellenwerte (Mindestmarktkapitalisierung, Mindestliquidität,
  Mindestkonfidenz für Top-10) sind als Platzhalter benannt, aber noch
  nicht zahlenmäßig festgelegt — folgt in Milestone 1/4.

**Nächster Schritt:** siehe `NEXT_STEPS.md`.
